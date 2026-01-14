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
            
            # Process attendance logs to create/update attendance records
            try:
                processed_count = AttendanceService.process_attendance_logs()
                logger.info(f"Processed {processed_count} attendance logs into attendance records after sync")
            except Exception as e:
                logger.error(f"Error processing attendance logs after sync: {str(e)}")
                # Don't fail the sync if processing fails, just log it
            
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
        # Get logs from last 30 days, ordered by employee and timestamp
        logs = AttendanceLog.objects.filter(
            timestamp__date__gte=timezone.now().date() - timedelta(days=30)
        ).order_by('employee', 'timestamp')
        
        processed_count = 0
        updated_count = 0
        
        # Group logs by employee and date for efficient processing
        from collections import defaultdict
        logs_by_employee_date = defaultdict(list)
        
        for log in logs:
            attendance_date = log.timestamp.date()
            key = (log.employee.id, attendance_date)
            logs_by_employee_date[key].append(log)
        
        # Process each employee-date combination
        for (employee_id, attendance_date), day_logs in logs_by_employee_date.items():
            try:
                employee = Employee.objects.get(id=employee_id)
                
                # Get or create attendance record for the date
                attendance, created = Attendance.objects.get_or_create(
                    employee=employee,
                    date=attendance_date,
                    defaults={'status': 'present'}
                )
                
                # Process logs in chronological order
                # For check_in: use the earliest timestamp
                # For check_out: use the latest timestamp
                # For breaks: use the first start and last end
                check_ins = [log for log in day_logs if log.attendance_type == 'check_in']
                check_outs = [log for log in day_logs if log.attendance_type == 'check_out']
                break_starts = [log for log in day_logs if log.attendance_type == 'break_start']
                break_ends = [log for log in day_logs if log.attendance_type == 'break_end']
                
                updated = False
                
                # Update check_in: use earliest check-in (machine logs take precedence if they exist)
                if check_ins:
                    machine_check_ins = [log for log in check_ins if log.source == 'machine']
                    if machine_check_ins:
                        # Prefer machine check-ins
                        earliest_check_in = min(machine_check_ins, key=lambda x: x.timestamp)
                    else:
                        # Use manual check-ins if no machine logs
                        earliest_check_in = min(check_ins, key=lambda x: x.timestamp)
                    
                    if not attendance.check_in or attendance.check_in != earliest_check_in.timestamp:
                        attendance.check_in = earliest_check_in.timestamp
                        updated = True
                
                # Update check_out: use latest check-out (machine logs take precedence if they exist)
                if check_outs:
                    machine_check_outs = [log for log in check_outs if log.source == 'machine']
                    if machine_check_outs:
                        # Prefer machine check-outs
                        latest_check_out = max(machine_check_outs, key=lambda x: x.timestamp)
                    else:
                        # Use manual check-outs if no machine logs
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
                
                # Check for late arrival (only if check_in exists)
                if attendance.check_in:
                    work_start_time = attendance.check_in.replace(
                        hour=9, minute=0, second=0, microsecond=0
                    )  # Assuming 9 AM start time
                    if attendance.check_in > work_start_time:
                        attendance.is_late = True
                        late_duration = attendance.check_in - work_start_time
                        attendance.late_minutes = int(late_duration.total_seconds() / 60)
                    else:
                        attendance.is_late = False
                        attendance.late_minutes = 0
                
                # Update status based on check_in/check_out
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
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        logger.info(f"Processed {processed_count} attendance logs, updated {updated_count} attendance records")
        return processed_count
    
    @staticmethod
    def test_machine_connection(machine):
        """
        Test connection to a machine with detailed verification
        
        Args:
            machine: AttendanceMachine instance
        
        Returns:
            Dict with 'success' (bool), 'message' (str), 'details' (dict), and other info
        """
        try:
            driver = get_machine_driver(machine)
            result = driver.test_connection()
            
            # Ensure details dict exists
            if 'details' not in result:
                result['details'] = {}
            
            return result
        except Exception as e:
            import traceback
            logger.error(f"Error testing connection: {str(e)}\n{traceback.format_exc()}")
            return {
                'success': False,
                'message': f'Error testing connection: {str(e)}',
                'details': {
                    'error': str(e)
                }
            }

