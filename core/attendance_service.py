"""
Generic attendance service that works with any biometric machine using the driver system.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from .models import AttendanceLog, Employee, AttendanceMachine, Attendance
from .machine_drivers import get_machine_driver

logger = logging.getLogger(__name__)


class AttendanceService:
    """Generic attendance service for syncing with any biometric machine"""
    
    @staticmethod
    def sync_machine_attendance(machine, start_date=None, end_date=None):
        """
        Sync attendance data from a specific machine to database
        
        Args:
            machine: AttendanceMachine instance
            start_date: Start date for sync (optional)
            end_date: End date for sync (optional)
        
        Returns:
            Dict with 'success' (bool), 'synced_count' (int), and 'message' (str)
        """
        if not machine.is_active:
            return {
                'success': False,
                'synced_count': 0,
                'message': f'Machine {machine.name} is not active'
            }
        
        try:
            # Get appropriate driver for the machine
            driver = get_machine_driver(machine)
            
            # Connect to machine
            if not driver.connect():
                error_msg = f'Failed to connect to {machine.name}'
                machine.last_error = error_msg
                machine.save()
                return {
                    'success': False,
                    'synced_count': 0,
                    'message': error_msg
                }
            
            # Get attendance data
            if not start_date:
                start_date = timezone.now().date() - timedelta(days=7)
            if not end_date:
                end_date = timezone.now().date()
            
            attendance_data = driver.get_attendance_data(start_date, end_date)
            
            synced_count = 0
            errors = []
            
            for record in attendance_data:
                try:
                    # Find employee by machine user ID
                    # Try multiple matching strategies:
                    # 1. machine_id, fingerprint_id, face_id, card_id fields
                    # 2. Employee database ID
                    # 3. User ID
                    employee = None
                    user_id_raw = record['user_id']
                    user_id = str(user_id_raw).strip()  # Convert to string and strip whitespace
                    
                    logger.debug(f"Processing attendance record - Machine user ID: '{user_id}' (type: {type(user_id_raw)}, raw: {repr(user_id_raw)})")
                    
                    # First, try the dedicated machine ID fields (exact match, case-sensitive)
                    employee = Employee.objects.filter(machine_id=user_id).first()
                    if employee:
                        logger.info(f"Matched via machine_id field: '{user_id}' -> {employee.user.username}")
                    
                    # Try with stripped machine_id from database
                    if not employee:
                        # Get all employees and check manually (handles whitespace issues)
                        all_employees = Employee.objects.exclude(machine_id__isnull=True).exclude(machine_id='')
                        for emp in all_employees:
                            if emp.machine_id and str(emp.machine_id).strip() == user_id:
                                employee = emp
                                logger.info(f"Matched via machine_id (stripped): '{user_id}' -> {employee.user.username}")
                                break
                    
                    if not employee:
                        employee = Employee.objects.filter(fingerprint_id=user_id).first()
                        if employee:
                            logger.info(f"Matched via fingerprint_id: '{user_id}' -> {employee.user.username}")
                    
                    if not employee:
                        employee = Employee.objects.filter(face_id=user_id).first()
                        if employee:
                            logger.info(f"Matched via face_id: '{user_id}' -> {employee.user.username}")
                    
                    if not employee:
                        employee = Employee.objects.filter(card_id=user_id).first()
                        if employee:
                            logger.info(f"Matched via card_id: '{user_id}' -> {employee.user.username}")
                    
                    # If not found, try matching by employee database ID
                    if not employee:
                        try:
                            employee_db_id = int(user_id)
                            employee = Employee.objects.filter(id=employee_db_id).first()
                            if employee:
                                logger.info(f"Matched via employee.id: '{user_id}' -> {employee.user.username}")
                        except (ValueError, TypeError):
                            pass
                    
                    # If still not found, try matching by user ID
                    if not employee:
                        try:
                            user_db_id = int(user_id)
                            employee = Employee.objects.filter(user_id=user_db_id).first()
                            if employee:
                                logger.info(f"Matched via user.id: '{user_id}' -> {employee.user.username}")
                        except (ValueError, TypeError):
                            pass
                    
                    if not employee:
                        # Log all available machine_ids for debugging
                        available_ids = list(Employee.objects.exclude(machine_id__isnull=True).exclude(machine_id='').values_list('machine_id', flat=True))
                        logger.warning(f"Employee not found for machine user ID: '{user_id}' in {machine.name}. Available machine_ids: {available_ids}")
                        errors.append(f"Employee not found for user ID: '{user_id}'")
                        continue
                    
                    logger.info(f"✓ Matched machine user ID '{user_id}' to employee: {employee.user.username} (Employee ID: {employee.id}, User ID: {employee.user.id}, Machine ID in DB: '{employee.machine_id}')")
                    
                    # Check if attendance log already exists
                    timestamp = record['timestamp']
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    
                    existing_log = AttendanceLog.objects.filter(
                        employee=employee,
                        machine=machine,
                        machine_timestamp=timestamp,
                        source='machine'
                    ).first()
                    
                    if existing_log:
                        continue
                    
                    # Determine attendance type
                    attendance_type = AttendanceService._determine_attendance_type(
                        employee, timestamp
                    )
                    
                    # Create attendance log
                    log = AttendanceLog.objects.create(
                        employee=employee,
                        attendance_type=attendance_type,
                        source='machine',
                        machine=machine,
                        timestamp=timestamp,
                        machine_timestamp=timestamp,
                        machine_user_id=user_id,
                        location=machine.location,
                        raw_data=record.get('raw_data', {})
                    )
                    
                    logger.info(f"Created attendance log: {log.id} for {employee.user.username} - {attendance_type} at {timestamp}")
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing attendance record: {str(e)}")
                    errors.append(str(e))
                    continue
            
            # Disconnect from machine
            driver.disconnect()
            
            # Update machine sync status
            machine.last_sync = timezone.now()
            machine.last_error = '; '.join(errors) if errors else ''
            machine.save()
            
            message = f'Synced {synced_count} attendance records from {machine.name}'
            if errors:
                message += f'. {len(errors)} errors occurred.'
                # Log first few errors for debugging
                for error in errors[:5]:
                    logger.warning(f"Sync error: {error}")
            
            logger.info(f"Sync completed: {message}. Total records fetched: {len(attendance_data)}")
            
            return {
                'success': True,
                'synced_count': synced_count,
                'message': message,
                'errors': errors
            }
            
        except Exception as e:
            error_msg = f'Error syncing {machine.name}: {str(e)}'
            logger.error(error_msg)
            machine.last_error = error_msg
            machine.save()
            return {
                'success': False,
                'synced_count': 0,
                'message': error_msg
            }
    
    @staticmethod
    def sync_all_machines(start_date=None, end_date=None):
        """
        Sync attendance from all active machines
        
        Args:
            start_date: Start date for sync (optional)
            end_date: End date for sync (optional)
        
        Returns:
            Dict with results for each machine
        """
        machines = AttendanceMachine.objects.filter(is_active=True)
        results = {}
        
        for machine in machines:
            result = AttendanceService.sync_machine_attendance(machine, start_date, end_date)
            results[machine.id] = {
                'machine_name': machine.name,
                **result
            }
        
        return results
    
    @staticmethod
    def _determine_attendance_type(employee, timestamp):
        """Determine attendance type based on time patterns"""
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
    
    @staticmethod
    def process_attendance_logs():
        """Process attendance logs and create/update attendance records"""
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
    
    @staticmethod
    def test_machine_connection(machine):
        """
        Test connection to a machine
        
        Args:
            machine: AttendanceMachine instance
        
        Returns:
            Dict with 'success' (bool) and 'message' (str)
        """
        try:
            driver = get_machine_driver(machine)
            result = driver.test_connection()
            return result
        except Exception as e:
            return {
                'success': False,
                'message': f'Error testing connection: {str(e)}'
            }

