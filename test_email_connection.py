"""
Quick test script to verify email configuration
Run this from Django shell: python manage.py shell < test_email_connection.py
Or run: python manage.py shell, then paste this code
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrm.settings')
django.setup()

from core.models import CompanySettings
from core.email_utils import send_test_email

# Get settings
settings = CompanySettings.objects.first()
if not settings:
    print("❌ Company settings not found!")
    exit()

print("=" * 50)
print("Email Configuration Check")
print("=" * 50)
print(f"Email Enabled: {settings.email_enabled}")
print(f"SMTP Host: {settings.email_host}")
print(f"SMTP Port: {settings.email_port}")
print(f"Use TLS: {settings.email_use_tls}")
print(f"Use SSL: {settings.email_use_ssl}")
print(f"Email User: {settings.email_host_user}")
print(f"Email Password: {'*' * len(settings.email_host_password) if settings.email_host_password else 'NOT SET'}")
print("=" * 50)

if not settings.email_enabled:
    print("❌ Email is not enabled!")
    exit()

if not settings.email_host_user or not settings.email_host_password:
    print("❌ Email username or password not configured!")
    exit()

# Test sending email
test_email = "murtaza7n@gmail.com"
print(f"\nSending test email to {test_email}...")
success, message = send_test_email(test_email)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")

