# Automatic Attendance Sync Setup Guide

This guide explains how to set up automatic attendance syncing so that attendance marked on biometric machines is automatically synced to the system without manual intervention.

## Overview

The system now supports automatic syncing of attendance data from biometric machines. You can set this up in two ways:

1. **Management Command** (Recommended for production)
2. **Scheduled Task/ Cron Job**

## Method 1: Management Command (Manual or Scheduled)

### Manual Execution

You can manually run the auto-sync command:

```bash
python manage.py auto_sync_attendance
```

### Options

- `--force`: Force sync all active machines regardless of sync interval
- `--machine-id <id>`: Sync only a specific machine by ID
- `--days <number>`: Number of days to sync (default: 1, meaning today only)

Examples:

```bash
# Sync all machines (respects sync intervals)
python manage.py auto_sync_attendance

# Force sync all machines (ignore sync intervals)
python manage.py auto_sync_attendance --force

# Sync only machine with ID 1
python manage.py auto_sync_attendance --machine-id 1

# Sync last 7 days
python manage.py auto_sync_attendance --days 7
```

## Method 2: Windows Task Scheduler

### Step 1: Create a Batch File

Create a file named `sync_attendance.bat` in your project root:

```batch
@echo off
cd /d C:\Users\SBS\Desktop\hrm\hrmsys4sbs
call venv312\Scripts\activate.bat
python manage.py auto_sync_attendance
deactivate
```

**Note:** Update the paths to match your project location.

### Step 2: Set Up Windows Task Scheduler

1. Open **Task Scheduler** (search for it in Windows Start menu)
2. Click **Create Basic Task** or **Create Task**
3. Name it: "HRM Auto Sync Attendance"
4. Set trigger: **Daily** or **Repeat task every** (e.g., every 15 minutes)
5. Action: **Start a program**
6. Program/script: Path to your `sync_attendance.bat` file
7. Start in: Your project directory (e.g., `C:\Users\SBS\Desktop\hrm\hrmsys4sbs`)
8. Click **Finish**

### Recommended Schedule

- **Every 15 minutes**: For real-time attendance updates
- **Every 30 minutes**: For less frequent updates
- **Every hour**: For basic syncing needs

The sync command respects each machine's `sync_interval` setting, so it won't sync machines that were recently synced.

## Method 3: Linux Cron Job

Add this to your crontab (run `crontab -e`):

```bash
# Sync attendance every 15 minutes
*/15 * * * * cd /path/to/hrmsys4sbs && /path/to/venv/bin/python manage.py auto_sync_attendance >> /var/log/attendance_sync.log 2>&1
```

Or for every 5 minutes:

```bash
*/5 * * * * cd /path/to/hrmsys4sbs && /path/to/venv/bin/python manage.py auto_sync_attendance >> /var/log/attendance_sync.log 2>&1
```

## Method 4: Using the Web Interface

You can also trigger auto-sync from the web interface by visiting:

```
http://your-domain/auto-sync-attendance/
```

This URL respects sync intervals and will only sync machines that are due for syncing.

## How It Works

1. **Sync Interval Check**: The system checks each machine's `last_sync` time and `sync_interval` setting
2. **Smart Syncing**: Only machines that are due for syncing (based on their interval) will be synced
3. **Automatic Processing**: After syncing, attendance logs are automatically processed into attendance records
4. **Error Handling**: Errors are logged but don't stop the sync process for other machines

## Machine Sync Interval Settings

Each machine has a `sync_interval` setting (in minutes) that determines how often it should be synced:

- **15 minutes**: Recommended for real-time updates
- **30 minutes**: Good balance
- **60 minutes**: For less frequent updates

You can set this in the machine configuration page.

## Troubleshooting

### Check if sync is running

Check the Django logs or the log file specified in your scheduled task.

### Manual sync test

Run the command manually to see if there are any errors:

```bash
python manage.py auto_sync_attendance --force
```

### Check machine status

Go to **Manage Attendance Machines** in the admin panel to see:
- Last sync time
- Last error (if any)
- Machine status (active/inactive)

## Notes

- The sync process is designed to be safe and won't duplicate records
- Only active machines are synced
- The system automatically processes attendance logs into attendance records after syncing
- Errors are logged but don't prevent other machines from syncing

