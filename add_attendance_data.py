#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrm.settings')
django.setup()

from core.models import Employee, Attendance
from django.utils import timezone
from datetime import date, timedelta
import random

def add_sample_attendance():
    print("Adding sample attendance data...")
    
    employees = Employee.objects.all()
    if not employees.exists():
        print("No employees found. Please create employees first.")
        return
    
    # Add attendance records for the last 7 days
    for employee in employees:
        for i in range(7):
            attendance_date = date.today() - timedelta(days=i)
            
            # Skip if attendance record already exists
            if Attendance.objects.filter(employee=employee, date=attendance_date).exists():
                continue
            
            status = random.choice(['present', 'absent', 'late', 'half_day'])
            
            # Create attendance record
            attendance = Attendance.objects.create(
                employee=employee,
                date=attendance_date,
                status=status,
                check_in=timezone.now().replace(hour=9, minute=random.randint(0, 30)) if status in ['present', 'late'] else None,
                check_out=timezone.now().replace(hour=17, minute=random.randint(0, 59)) if status in ['present', 'late'] else None,
                is_late=status == 'late',
                late_minutes=random.randint(5, 30) if status == 'late' else 0
            )
            
            # Calculate hours if check-in and check-out exist
            if attendance.check_in and attendance.check_out:
                attendance.calculate_hours()
            
            print(f"Created attendance for {employee.user.username} on {attendance_date} - {status}")
    
    print("Sample attendance data creation completed!")

if __name__ == '__main__':
    add_sample_attendance()
