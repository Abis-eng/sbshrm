# DevOps Setup Guide for HRM Production Server

## 📋 What to Give Your DevOps Person

Give them this file: **`hrm/settings_production.py`**

This is the **corrected production settings file** that includes all the missing components.

## 🔧 Changes Made to Production Settings

### 1. ✅ Added Missing Context Processor
```python
'core.context_processors.company_context',  # Added to TEMPLATES context_processors
```

### 2. ✅ Added Missing Middleware
```python
'core.middleware.CompanyIsolationMiddleware',  # Added to MIDDLEWARE
```

### 3. ✅ Added ZKT SDK Path Configuration
```python
ZKT_SDK_PATH = os.environ.get('ZKT_SDK_PATH', '/opt/zkt_sdk')
```

### 4. ✅ Added LOGIN_REDIRECT_URL
```python
LOGIN_REDIRECT_URL = '/dashboard/'
```

## 🚀 Installation Steps for DevOps

### Step 1: Replace settings.py
```bash
# Backup current settings
cp hrm/settings.py hrm/settings.py.backup

# Use the corrected production settings
cp hrm/settings_production.py hrm/settings.py
```

### Step 2: Install ZKT SDK on Linux Server
```bash
# Option 1: Install SDK to /opt/zkt_sdk
sudo mkdir -p /opt/zkt_sdk
# Copy ZKT SDK files to this directory

# Option 2: Install SDK to /usr/local/zkt_sdk
sudo mkdir -p /usr/local/zkt_sdk
# Copy ZKT SDK files to this directory

# Option 3: Set environment variable
export ZKT_SDK_PATH=/path/to/zkt_sdk
# Add to /etc/environment or ~/.bashrc for permanent
```

### Step 3: Update ZKT_SDK_PATH in settings.py
Edit `hrm/settings.py` and set the correct path:
```python
ZKT_SDK_PATH = '/opt/zkt_sdk'  # or wherever SDK is installed
```

### Step 4: Verify Network Access
```bash
# Test connection to biometric machine
telnet 192.168.18.80 4370

# Or use netcat
nc -zv 192.168.18.80 4370

# If connection fails, check firewall rules
sudo ufw allow from 192.168.18.80 to any port 4370
```

### Step 5: Restart Django Application
```bash
# If using systemd
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Or if using supervisor
sudo supervisorctl restart hrm

# Or if using manual process
# Kill and restart your Django process
```

## ✅ Verification Checklist

After setup, verify:

1. ✅ Django application starts without errors
2. ✅ Can access admin panel
3. ✅ Can view attendance page
4. ✅ Can test machine connection (go to Manage Attendance Machines → Test Connection)
5. ✅ Can sync attendance from machine
6. ✅ Attendance logs show correct machine user IDs (not all "8")

## 🔍 Troubleshooting

### If attendance still doesn't work:

1. **Check Django logs:**
   ```bash
   tail -f /var/log/django/error.log
   # or wherever your logs are
   ```

2. **Check if SDK is found:**
   - Look for log message: "ZKT SDK path added: /path/to/sdk"
   - If you see "ZKT SDK path not found", SDK is not installed correctly

3. **Test SDK import:**
   ```bash
   python manage.py shell
   >>> from zk import ZK
   # Should not give ImportError
   ```

4. **Check network connectivity:**
   ```bash
   ping 192.168.18.80
   telnet 192.168.18.80 4370
   ```

5. **Check Django timezone:**
   ```bash
   python manage.py shell
   >>> from django.utils import timezone
   >>> timezone.now()
   # Should show Asia/Karachi time, not UTC
   ```

## 📝 Important Notes

1. **ZKT SDK Path:** This is the #1 issue. Make sure SDK is installed and path is correct.

2. **Network Access:** Production server must be able to reach `192.168.18.80:4370`

3. **Time Zone:** Already correct (`Asia/Karachi`) - don't change it!

4. **Database:** Credentials are already set correctly in the production settings.

## 🎯 Quick Fix Summary

**Give DevOps this file:** `hrm/settings_production.py`

**Tell them to:**
1. Replace `hrm/settings.py` with `settings_production.py`
2. Install ZKT SDK on Linux server
3. Set `ZKT_SDK_PATH` in settings.py to SDK location
4. Restart Django application
5. Test attendance sync

