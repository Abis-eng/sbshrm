$ErrorActionPreference = "Stop"

# Config: read from environment with defaults matching hrm/settings.py and docker-compose.yml
$dbName = $env:DB_NAME; if (-not $dbName -or $dbName.Trim() -eq "") { $dbName = "hrm" }
$dbUser = $env:DB_USER; if (-not $dbUser -or $dbUser.Trim() -eq "") { $dbUser = "hrm" }
$dbPass = $env:DB_PASSWORD; if (-not $dbPass) { $dbPass = $null } # may be empty
# If no password provided, try known defaults from project bootstrap
if ($dbPass -eq $null -or $dbPass -eq "") { $dbPass = "hrm12345" }
$dbHost = $env:DB_HOST; if (-not $dbHost -or $dbHost.Trim() -eq "") { $dbHost = "127.0.0.1" }
$dbPort = $env:DB_PORT; if (-not $dbPort -or $dbPort.Trim() -eq "") { $dbPort = "3306" }

# Output directory
$backupDir = Join-Path -Path $PSScriptRoot -ChildPath "backups"
if (-not (Test-Path -LiteralPath $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }

# Filename
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$fileName = "${dbName}_backup_${timestamp}.sql"
$outPath = Join-Path -Path $backupDir -ChildPath $fileName

# Verify mysqldump available
$mysqldump = Get-Command mysqldump -ErrorAction SilentlyContinue
if (-not $mysqldump) {
    $commonInstallPaths = @(
        "C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysqldump.exe",
        "C:\\Program Files\\MySQL\\MySQL Server 5.7\\bin\\mysqldump.exe",
        "C:\\Program Files\\MySQL\\MySQL Shell 8.0\\bin\\mysqldump.exe",
        "C:\\Program Files (x86)\\MySQL\\MySQL Server 8.0\\bin\\mysqldump.exe"
    )
    $found = $commonInstallPaths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($found) {
        $mysqldump = @{ Source = $found }
    }
}

# Build args
$commonArgs = @("-h", $dbHost, "-P", $dbPort, "-u", $dbUser, "--routines", "--triggers", "--single-transaction", "--quick", $dbName)

# Prefer env var for password using --password=... to avoid prompt
if ($dbPass -ne $null) {
    $commonArgs = @("--password=$dbPass") + $commonArgs
}

Write-Host "Exporting database '$dbName' from $($dbHost):$($dbPort) as user '$dbUser' ..."

if ($mysqldump) {
    # Local mysqldump path; use call operator for compatibility
    $stdErrTemp = New-TemporaryFile
    try {
        $output = & $($mysqldump.Source) @commonArgs 2> $stdErrTemp.FullName
        $stdErr = Get-Content -Raw -LiteralPath $stdErrTemp.FullName
        if ($LASTEXITCODE -ne 0 -or ($stdErr -and $stdErr.Trim().Length -gt 0)) {
            if ($stdErr -match "Access denied" -or $stdErr -match "using password: YES") {
                Write-Error "Access denied. Check DB_USER/DB_PASSWORD."
            }
            if ($stdErr -and $stdErr.Trim().Length -gt 0) { Write-Error $stdErr }
            if ($LASTEXITCODE -ne 0) { throw "mysqldump failed with exit code $LASTEXITCODE" }
        }
        Set-Content -LiteralPath $outPath -Value $output -Encoding UTF8
        Write-Host "Backup created: $outPath"
    }
    finally {
        if (Test-Path -LiteralPath $stdErrTemp.FullName) { Remove-Item -LiteralPath $stdErrTemp.FullName -Force -ErrorAction SilentlyContinue }
    }
}
else {
    # Try Docker fallback
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) { throw "mysqldump not found and Docker is not installed. Install MySQL client or Docker." }

    # Find a mysql container likely named '*_db_*' or with image mysql
    $containers = & docker ps --format "{{.ID}} {{.Image}} {{.Names}}"
    if (-not $containers) { throw "No running containers found. Start your database container (docker compose up -d)." }

    $candidate = $containers | Where-Object { ($_ -match "mysql") -or ($_ -match "\bdb\b") } | Select-Object -First 1
    if (-not $candidate) { throw "Could not find a running MySQL container. Ensure the db service is up." }
    $containerId = $candidate.Split()[0]

    $dockerArgs = @("exec", "-i", $containerId, "mysqldump", "-u", $dbUser)
    # Default compose password fallback when not provided
    $effectivePass = if ($dbPass -ne $null) { $dbPass } else { "password" }
    $dockerArgs += "--password=$effectivePass"
    $dockerArgs += @($dbName)

    Write-Host "Using Docker container $containerId to export database '$dbName' ..."
    $dump = & docker @dockerArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker mysqldump failed: $dump"
    }
    Set-Content -LiteralPath $outPath -Value $dump -Encoding UTF8
    Write-Host "Backup created: $outPath"
}


