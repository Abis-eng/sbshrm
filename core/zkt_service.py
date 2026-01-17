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
    def __init__(self, ip_address="192.168.18.80", port=4370, timeout=5):
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
                # IMPORTANT: ONLY match by machine_id field - no other matching strategies
                # ZKT machines: use 'uid' as the actual machine user ID, not 'user_id'
                user_id_raw = None
                if hasattr(record, 'uid') and record.uid:
                    user_id_raw = record.uid  # Use uid (actual machine user ID)
                elif hasattr(record, 'user_id') and record.user_id:
                    user_id_raw = record.user_id
                else:
                    logger.warning(f"Attendance record has no uid or user_id: {record}")
                    continue
                
                user_id = str(user_id_raw).strip()  # Convert to string and strip whitespace
                
                # Log detailed information for debugging
                logger.info(f"Processing attendance record - Machine user ID: '{user_id}' (uid: {getattr(record, 'uid', 'N/A')}, user_id: {getattr(record, 'user_id', 'N/A')}, type: {type(user_id_raw)}, raw: {repr(user_id_raw)})")
                
                if not user_id:
                    logger.warning(f"Skipping attendance record with empty user_id")
                    continue
                
                employee = None
                
                # ONLY match by machine_id field - exact match first
                employee = Employee.objects.filter(machine_id=user_id).first()
                if employee:
                    logger.info(f"✓ Matched via machine_id (exact): '{user_id}' -> {employee.user.username} (Employee ID: {employee.id}, Machine ID in DB: '{employee.machine_id}')")
                
                # Try with stripped machine_id from database (handles whitespace issues)
                if not employee:
                    all_employees = Employee.objects.exclude(machine_id__isnull=True).exclude(machine_id='')
                    for emp in all_employees:
                        if emp.machine_id and str(emp.machine_id).strip() == user_id:
                            employee = emp
                            logger.info(f"✓ Matched via machine_id (stripped): '{user_id}' -> {employee.user.username} (Employee ID: {employee.id}, Machine ID in DB: '{employee.machine_id}')")
                            break
                
                # NO OTHER MATCHING - Only machine_id is used
                
                if not employee:
                    # Log all available machine_ids for debugging
                    available_ids = list(Employee.objects.exclude(machine_id__isnull=True).exclude(machine_id='').values_list('machine_id', flat=True))
                    logger.warning(
                        f"❌ Employee NOT FOUND for machine user ID: '{user_id}' (raw: {repr(user_id_raw)}). "
                        f"Available machine_ids in database: {available_ids}. "
                        f"Please ensure the employee's Machine ID field is set to '{user_id}'."
                    )
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
                    machine=machine,
                    timestamp=record.timestamp,
                    machine_timestamp=record.timestamp,
                    machine_user_id=str(user_id),  # Store the actual user_id from the machine
                    location=machine.location
                )
                
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error processing attendance record: {str(e)}")
                continue
        
        # Update machine last sync time
        machine.last_sync = timezone.now()
        machine.save()
        
        # Process attendance logs to create/update attendance records
        try:
            processed_count = self.process_attendance_logs()
            logger.info(f"Processed {processed_count} attendance logs into attendance records after sync")
        except Exception as e:
            logger.error(f"Error processing attendance logs after sync: {str(e)}")
            # Don't fail the sync if processing fails, just log it
        
        logger.info(f"Synced {synced_count} attendance records from ZKT machine")
        return synced_count
    
    def _determine_attendance_type(self, employee, timestamp):
        """
        Determine attendance type based on sequential marking:
        1st mark = check_in
        2nd mark = break_start
        3rd mark = break_end
        4th mark = check_out
        """
        from .models import AttendanceLog
        
        # Get today's attendance logs for this employee
        today_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        today_logs = AttendanceLog.objects.filter(
            employee=employee,
            timestamp__gte=today_start,
            timestamp__lt=today_end
        ).order_by('timestamp')
        
        # Count how many logs exist today
        log_count = today_logs.count()
        
        # Sequential logic:
        # 1st mark = check_in
        # 2nd mark = break_start
        # 3rd mark = break_end
        # 4th mark = check_out
        if log_count == 0:
            return 'check_in'
        elif log_count == 1:
            return 'break_start'
        elif log_count == 2:
            return 'break_end'
        else:
            return 'check_out'
    
    def process_attendance_logs(self):
        """Process attendance logs and create/update attendance records"""
        # Use the improved AttendanceService method if available, otherwise use local implementation
        try:
            from .attendance_service import AttendanceService
            return AttendanceService.process_attendance_logs()
        except ImportError:
            # Fallback to local implementation
            from .models import AttendanceLog, Attendance
            from collections import defaultdict
            
            # Get logs from last 30 days, ordered by employee and timestamp
            logs = AttendanceLog.objects.filter(
                timestamp__date__gte=timezone.now().date() - timedelta(days=30)
            ).order_by('employee', 'timestamp')
            
            processed_count = 0
            updated_count = 0
            
            # Group logs by employee and date for efficient processing
            logs_by_employee_date = defaultdict(list)
            
            for log in logs:
                attendance_date = log.timestamp.date()
                key = (log.employee.id, attendance_date)
                logs_by_employee_date[key].append(log)
            
            # Process each employee-date combination
            for (employee_id, attendance_date), day_logs in logs_by_employee_date.items():
                try:
                    from .models import Employee
                    employee = Employee.objects.get(id=employee_id)
                    
                    # Get or create attendance record for the date
                    attendance, created = Attendance.objects.get_or_create(
                        employee=employee,
                        date=attendance_date,
                        defaults={'status': 'present'}
                    )
                    
                    # Process logs in chronological order
                    check_ins = [log for log in day_logs if log.attendance_type == 'check_in']
                    check_outs = [log for log in day_logs if log.attendance_type == 'check_out']
                    break_starts = [log for log in day_logs if log.attendance_type == 'break_start']
                    break_ends = [log for log in day_logs if log.attendance_type == 'break_end']
                    
                    updated = False
                    
                    # Update check_in: use earliest check-in (machine logs take precedence if they exist)
                    if check_ins:
                        machine_check_ins = [log for log in check_ins if log.source == 'machine']
                        if machine_check_ins:
                            earliest_check_in = min(machine_check_ins, key=lambda x: x.timestamp)
                        else:
                            earliest_check_in = min(check_ins, key=lambda x: x.timestamp)
                        
                        if not attendance.check_in or attendance.check_in != earliest_check_in.timestamp:
                            attendance.check_in = earliest_check_in.timestamp
                            updated = True
                    
                    # Update check_out: use latest check-out (machine logs take precedence if they exist)
                    if check_outs:
                        machine_check_outs = [log for log in check_outs if log.source == 'machine']
                        if machine_check_outs:
                            latest_check_out = max(machine_check_outs, key=lambda x: x.timestamp)
                        else:
                            latest_check_out = max(check_outs, key=lambda x: x.timestamp)
                        
                        if not attendance.check_out or attendance.check_out != latest_check_out.timestamp:
                            attendance.check_out = latest_check_out.timestamp
                            updated = True
                    
                    # Update break_start: use earliest break start
                    if break_starts:
                        earliest_break_start = min(break_starts, key=lambda x: x.timestamp)
                        if not attendance.break_start or attendance.break_start != earliest_break_start.timestamp:
                            attendance.break_start = earliest_break_start.timestamp
                            updated = True
                    
                    # Update break_end: use latest break end
                    if break_ends:
                        latest_break_end = max(break_ends, key=lambda x: x.timestamp)
                        if not attendance.break_end or attendance.break_end != latest_break_end.timestamp:
                            attendance.break_end = latest_break_end.timestamp
                            updated = True
                    
                    # Calculate hours
                    attendance.calculate_hours()
                    
                    # Check for late arrival (work hours: 10 AM to 6 PM)
                    if attendance.check_in:
                        work_start_time = attendance.check_in.replace(
                            hour=10, minute=0, second=0, microsecond=0
                        )
                        if attendance.check_in > work_start_time:
                            attendance.is_late = True
                            late_duration = attendance.check_in - work_start_time
                            attendance.late_minutes = int(late_duration.total_seconds() / 60)
                        else:
                            attendance.is_late = False
                            attendance.late_minutes = 0
                    
                    # Update status
                    if attendance.check_in:
                        attendance.status = 'present'
                    else:
                        attendance.status = 'absent'
                    
                    attendance.save()
                    processed_count += len(day_logs)
                    if updated or created:
                        updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing attendance logs for employee {employee_id} on {attendance_date}: {str(e)}")
                    continue
            
            logger.info(f"Processed {processed_count} attendance logs, updated {updated_count} attendance records")
            return processed_count

# Global ZKT service instance
zkt_service = ZKTService()
