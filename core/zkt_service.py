import os
import sys
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import logging

# Add ZKT SDK path to system path
sdk_path = r"C:\Users\SBS\Desktop\sdk"
if os.path.exists(sdk_path):
    sys.path.append(sdk_path)

try:
    from zk import ZK
except ImportError:
    # Fallback to pyzk if SDK not available
    try:
        from pyzk import ZK
    except ImportError:
        ZK = None

logger = logging.getLogger(__name__)

class ZKTService:
    def __init__(self, ip_address="192.168.18.1", port=4370, timeout=5):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.zk = None
        self.connected = False
        
    def connect(self):
        """Connect to ZKT machine"""
        if not ZK:
            logger.error("ZKT SDK not available")
            return False
            
        try:
            self.zk = ZK(self.ip_address, port=self.port, timeout=self.timeout)
            self.zk.connect()
            self.connected = True
            logger.info(f"Connected to ZKT machine at {self.ip_address}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ZKT machine: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from ZKT machine"""
        if self.zk and self.connected:
            try:
                self.zk.disconnect()
                self.connected = False
                logger.info("Disconnected from ZKT machine")
            except Exception as e:
                logger.error(f"Error disconnecting from ZKT machine: {str(e)}")
    
    def get_attendance_data(self, start_date=None, end_date=None):
        """Get attendance data from ZKT machine"""
        if not self.connected:
            if not self.connect():
                return []
        
        try:
            # Get attendance records from machine
            attendance_data = self.zk.get_attendance()
            
            # Filter by date range if provided
            if start_date and end_date:
                filtered_data = []
                for record in attendance_data:
                    record_date = record.timestamp.date()
                    if start_date <= record_date <= end_date:
                        filtered_data.append(record)
                return filtered_data
            
            return attendance_data
        except Exception as e:
            logger.error(f"Error getting attendance data: {str(e)}")
            return []
    
    def get_users(self):
        """Get users registered in ZKT machine"""
        if not self.connected:
            if not self.connect():
                return []
        
        try:
            users = self.zk.get_users()
            return users
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return []
    
    def sync_attendance(self, start_date=None, end_date=None):
        """Sync attendance data from ZKT machine to database"""
        from .models import AttendanceLog, Employee, AttendanceMachine
        
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=7)
        if not end_date:
            end_date = timezone.now().date()
        
        # Get or create attendance machine record
        machine, created = AttendanceMachine.objects.get_or_create(
            ip_address=self.ip_address,
            defaults={
                'name': 'ZKT K70',
                'port': self.port,
                'location': 'Main Office'
            }
        )
        
        # Get attendance data from machine
        attendance_data = self.get_attendance_data(start_date, end_date)
        
        synced_count = 0
        for record in attendance_data:
            try:
                # Find employee by machine ID
                employee = Employee.objects.filter(machine_id=str(record.user_id)).first()
                
                if not employee:
                    logger.warning(f"Employee not found for machine ID: {record.user_id}")
                    continue
                
                # Check if attendance log already exists
                existing_log = AttendanceLog.objects.filter(
                    employee=employee,
                    machine_timestamp=record.timestamp,
                    source='machine'
                ).first()
                
                if existing_log:
                    continue
                
                # Determine attendance type based on time patterns
                attendance_type = self._determine_attendance_type(employee, record.timestamp)
                
                # Create attendance log
                AttendanceLog.objects.create(
                    employee=employee,
                    attendance_type=attendance_type,
                    source='machine',
                    timestamp=record.timestamp,
                    machine_timestamp=record.timestamp,
                    machine_id=str(record.user_id),
                    location=machine.location
                )
                
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error processing attendance record: {str(e)}")
                continue
        
        # Update machine last sync time
        machine.last_sync = timezone.now()
        machine.save()
        
        logger.info(f"Synced {synced_count} attendance records from ZKT machine")
        return synced_count
    
    def _determine_attendance_type(self, employee, timestamp):
        """Determine attendance type based on time patterns"""
        from .models import AttendanceLog
        
        # Get today's attendance logs for this employee
        today_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        today_logs = AttendanceLog.objects.filter(
            employee=employee,
            timestamp__gte=today_start,
            timestamp__lt=today_end
        ).order_by('timestamp')
        
        # If no logs today, this is likely a check-in
        if not today_logs.exists():
            return 'check_in'
        
        # Get the last log
        last_log = today_logs.last()
        
        # Simple logic: alternate between check-in and check-out
        if last_log.attendance_type == 'check_in':
            return 'check_out'
        elif last_log.attendance_type == 'check_out':
            return 'check_in'
        else:
            return 'check_in'
    
    def process_attendance_logs(self):
        """Process attendance logs and create/update attendance records"""
        from .models import AttendanceLog, Attendance
        
        # Get unprocessed logs
        logs = AttendanceLog.objects.filter(
            timestamp__date__gte=timezone.now().date() - timedelta(days=30)
        ).order_by('employee', 'timestamp')
        
        processed_count = 0
        
        for log in logs:
            try:
                # Get or create attendance record for the date
                attendance_date = log.timestamp.date()
                attendance, created = Attendance.objects.get_or_create(
                    employee=log.employee,
                    date=attendance_date,
                    defaults={'status': 'present'}
                )
                
                # Update attendance record based on log type
                if log.attendance_type == 'check_in' and not attendance.check_in:
                    attendance.check_in = log.timestamp
                elif log.attendance_type == 'check_out' and not attendance.check_out:
                    attendance.check_out = log.timestamp
                elif log.attendance_type == 'break_start' and not attendance.break_start:
                    attendance.break_start = log.timestamp
                elif log.attendance_type == 'break_end' and not attendance.break_end:
                    attendance.break_end = log.timestamp
                
                # Calculate hours
                attendance.calculate_hours()
                
                # Check for late arrival
                if attendance.check_in:
                    work_start_time = attendance.check_in.replace(
                        hour=9, minute=0, second=0, microsecond=0
                    )  # Assuming 9 AM start time
                    if attendance.check_in > work_start_time:
                        attendance.is_late = True
                        late_duration = attendance.check_in - work_start_time
                        attendance.late_minutes = int(late_duration.total_seconds() / 60)
                
                attendance.save()
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing attendance log {log.id}: {str(e)}")
                continue
        
        logger.info(f"Processed {processed_count} attendance logs")
        return processed_count

# Global ZKT service instance
zkt_service = ZKTService()
