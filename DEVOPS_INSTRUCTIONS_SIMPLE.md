# Simple Instructions for DevOps

## File to Use
**Give DevOps:** `hrm/settings_production.py`

This file matches exactly what they provided, with only ONE addition for attendance to work.

## What DevOps Needs to Do

### 1. Replace settings.py
```bash
# Backup current
cp hrm/settings.py hrm/settings.py.backup

# Use the production settings
cp hrm/settings_production.py hrm/settings.py
```

### 2. Add ZKT SDK Path (REQUIRED for attendance)
Add this ONE line at the end of `hrm/settings.py`:

```python
# ZKT SDK Path - REQUIRED for attendance to work
# Set this to where ZKT SDK is installed on Linux server
ZKT_SDK_PATH = '/opt/zkt_sdk'  # or wherever SDK is installed
```

### 3. Install ZKT SDK
```bash
# Copy ZKT SDK files to Linux server
# Common location: /opt/zkt_sdk
sudo mkdir -p /opt/zkt_sdk
# Copy SDK files here
```

### 4. Restart Application
```bash
# Restart your Django application
sudo systemctl restart gunicorn  # or however you run Django
```

## That's It!

The settings file is now exactly as they provided, with just the ZKT SDK path added for attendance functionality.

