# Production Settings Issues & Fixes

## 🔴 CRITICAL ISSUES FOUND

### 1. **ZKT SDK Path - BLOCKING ATTENDANCE**
**Location:** `core/zkt_service.py` line 9

**Problem:**
```python
sdk_path = r"C:\Users\SBS\Desktop\sdk"  # Windows path - won't work on Linux server!
```

**Impact:** This is likely why attendance is NOT working in production! The SDK can't be imported on a Linux server with this Windows path.

**Fix:** Make the SDK path configurable via environment variable or settings.

### 2. **Missing Context Processor**
**Production is missing:** `'core.context_processors.company_context'`

**Impact:** Currency and company context might not work correctly in templates.

### 3. **Missing Middleware**
**Production is missing:** `'core.middleware.CompanyIsolationMiddleware'`

**Impact:** Company data isolation might not work correctly.

### 4. **STATIC_URL Path**
**Production:** `STATIC_URL = '/static/'` ✅ (Correct)
**Local:** `STATIC_URL = 'static/'` ❌ (Missing leading slash)

## ✅ GOOD THINGS IN PRODUCTION

1. **TIME_ZONE = 'Asia/Karachi'** ✅ (Correct for Pakistan)
2. **DEBUG = False** ✅ (Correct for production)
3. **ALLOWED_HOSTS** ✅ (Properly configured)

## 🔧 REQUIRED FIXES FOR PRODUCTION

### Fix 1: Make ZKT SDK Path Configurable

Update `core/zkt_service.py`:

```python
# Add ZKT SDK path to system path
import os
import sys
from django.conf import settings

# Get SDK path from settings or environment variable
sdk_path = getattr(settings, 'ZKT_SDK_PATH', os.environ.get('ZKT_SDK_PATH', None))
if not sdk_path:
    # Try common Linux paths
    possible_paths = [
        '/opt/zkt_sdk',
        '/usr/local/zkt_sdk',
        '/var/www/zkt_sdk',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'zkt_sdk'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            sdk_path = path
            break

if sdk_path and os.path.exists(sdk_path):
    sys.path.append(sdk_path)
```

### Fix 2: Add Missing Context Processor to Production

Add to `TEMPLATES[0]['OPTIONS']['context_processors']`:
```python
'core.context_processors.company_context',
```

### Fix 3: Add Missing Middleware (if needed)

Add to `MIDDLEWARE`:
```python
'core.middleware.CompanyIsolationMiddleware',
```

### Fix 4: Add ZKT_SDK_PATH to Settings

Add to production `settings.py`:
```python
# ZKT SDK Path (adjust based on where SDK is installed on server)
ZKT_SDK_PATH = '/opt/zkt_sdk'  # or wherever the SDK is on your Linux server
```

## 🚨 MOST LIKELY CAUSE OF ATTENDANCE NOT WORKING

The **ZKT SDK path** is the #1 issue. The hardcoded Windows path `C:\Users\SBS\Desktop\sdk` won't exist on a Linux production server, so:
- The SDK can't be imported
- ZKT connection fails
- Attendance syncing fails silently

## 📋 CHECKLIST FOR DEVOPS

1. ✅ Install ZKT SDK on production server (Linux path)
2. ✅ Set `ZKT_SDK_PATH` in settings.py or environment variable
3. ✅ Add missing context processor
4. ✅ Add missing middleware (if using company isolation)
5. ✅ Verify network access to biometric machine (192.168.18.80:4370)
6. ✅ Check firewall rules allow connection to machine
7. ✅ Test connection from production server: `telnet 192.168.18.80 4370`

