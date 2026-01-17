# Settings Comparison: Local vs Production

## Critical Differences That Could Affect Attendance

### 1. ⚠️ **TIME_ZONE - CRITICAL FOR ATTENDANCE**
- **Local:** `TIME_ZONE = 'UTC'`
- **Production:** `TIME_ZONE = 'Asia/Karachi'`

**Impact:** This is VERY IMPORTANT for attendance! If your production server is using UTC but your local is using Asia/Karachi, attendance timestamps will be off by 5 hours. This could cause:
- Attendance records showing wrong times
- Late arrival calculations being incorrect
- Attendance logs not matching the correct dates

**Recommendation:** Production should use `TIME_ZONE = 'Asia/Karachi'` (which it does - GOOD!)

### 2. ⚠️ **Missing Context Processor - Could Affect Currency Display**
- **Local:** Has `'core.context_processors.company_context'` 
- **Production:** Missing this context processor

**Impact:** This won't directly affect attendance functionality, but could affect currency display in templates.

### 3. ⚠️ **Missing Middleware**
- **Local:** Has `'core.middleware.CompanyIsolationMiddleware'`
- **Production:** Missing this middleware

**Impact:** This could affect data filtering by company, but shouldn't directly affect attendance matching.

### 4. **STATIC_URL Path**
- **Local:** `STATIC_URL = 'static/'` (no leading slash)
- **Production:** `STATIC_URL = '/static/'` (with leading slash)

**Impact:** Static files might not load correctly, but won't affect attendance.

### 5. **Database User**
- **Local:** `'USER': 'hrm'`
- **Production:** `'USER': 'hrm_user'`

**Impact:** Different database users - this is fine, just different credentials.

## Recommendations for Production Settings

Add these to your production settings.py:

```python
# Add missing context processor
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.views.theme_settings_context',
                'core.context_processors.company_context',  # ADD THIS
            ],
        },
    },
]

# Add missing middleware (if using company isolation)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.CompanyIsolationMiddleware',  # ADD THIS if needed
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Fix STATIC_URL
STATIC_URL = '/static/'  # Add leading slash

# Ensure TIME_ZONE is correct (already correct in production)
TIME_ZONE = 'Asia/Karachi'
USE_TZ = True
```

## Most Likely Cause of Attendance Issues

The **TIME_ZONE** difference is the most likely culprit if attendance is working locally but not in production. However, since production already has `TIME_ZONE = 'Asia/Karachi'` (which is correct), the issue might be:

1. **Missing context processor** - Could cause template rendering issues
2. **Missing middleware** - Could cause data filtering issues
3. **Network/firewall issues** - The biometric machine at IP 192.168.18.80 might not be accessible from the production server
4. **SDK path issues** - The ZKT SDK path might be different on production server

