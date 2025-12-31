"""
Management command to debug attendance matching issues
"""
from django.core.management.base import BaseCommand
from core.models import Employee, AttendanceMachine, AttendanceLog
from core.attendance_service import AttendanceService
from core.machine_drivers import get_machine_driver
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug attendance matching between machine and employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--machine-id',
            type=int,
            help='Machine ID to test',
        )

    def handle(self, *args, **options):
        machine_id = options.get('machine_id')
        
        if machine_id:
            machines = AttendanceMachine.objects.filter(id=machine_id)
        else:
            machines = AttendanceMachine.objects.filter(is_active=True)
        
        if not machines.exists():
            self.stdout.write(self.style.ERROR('No machines found'))
            return
        
        for machine in machines:
            self.stdout.write(self.style.SUCCESS(f'\n=== Testing Machine: {machine.name} ==='))
            self.stdout.write(f'Type: {machine.get_machine_type_display()}')
            self.stdout.write(f'Connection: {machine.get_connection_string()}')
            
            # Get driver
            try:
                driver = get_machine_driver(machine)
                if not driver.connect():
                    self.stdout.write(self.style.ERROR(f'Failed to connect to machine'))
                    continue
                
                # Get sample attendance data
                self.stdout.write('\nFetching attendance data...')
                attendance_data = driver.get_attendance_data()
                
                if not attendance_data:
                    self.stdout.write(self.style.WARNING('No attendance data found'))
                    driver.disconnect()
                    continue
                
                self.stdout.write(f'Found {len(attendance_data)} attendance records')
                
                # Show first few records
                self.stdout.write('\n--- Sample Records ---')
                for i, record in enumerate(attendance_data[:5]):
                    user_id = str(record['user_id']).strip()
                    self.stdout.write(f"Record {i+1}: user_id='{user_id}' (type: {type(record['user_id'])}) at {record['timestamp']}")
                
                # Check employee matching
                self.stdout.write('\n--- Employee Matching Test ---')
                unique_user_ids = set(str(r['user_id']).strip() for r in attendance_data)
                
                for user_id in list(unique_user_ids)[:10]:  # Test first 10 unique IDs
                    self.stdout.write(f"\nTesting user_id: '{user_id}'")
                    
                    # Try all matching methods
                    employee = Employee.objects.filter(machine_id=user_id).first()
                    if employee:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Matched via machine_id: {employee.user.username}"))
                        continue
                    
                    # Try with stripped
                    all_employees = Employee.objects.exclude(machine_id__isnull=True).exclude(machine_id='')
                    for emp in all_employees:
                        if emp.machine_id and str(emp.machine_id).strip() == user_id:
                            self.stdout.write(self.style.SUCCESS(f"  ✓ Matched via machine_id (stripped): {emp.user.username}"))
                            employee = emp
                            break
                    
                    if employee:
                        continue
                    
                    # Try other fields
                    employee = Employee.objects.filter(fingerprint_id=user_id).first()
                    if employee:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Matched via fingerprint_id: {employee.user.username}"))
                        continue
                    
                    # Try employee ID
                    try:
                        emp_id = int(user_id)
                        employee = Employee.objects.filter(id=emp_id).first()
                        if employee:
                            self.stdout.write(self.style.SUCCESS(f"  ✓ Matched via employee.id: {employee.user.username}"))
                            continue
                    except:
                        pass
                    
                    # Try user ID
                    try:
                        user_db_id = int(user_id)
                        employee = Employee.objects.filter(user_id=user_db_id).first()
                        if employee:
                            self.stdout.write(self.style.SUCCESS(f"  ✓ Matched via user.id: {employee.user.username}"))
                            continue
                    except:
                        pass
                    
                    self.stdout.write(self.style.ERROR(f"  ✗ No match found for user_id: '{user_id}'"))
                
                # Show all employees with machine_ids
                self.stdout.write('\n--- Employees with Machine IDs ---')
                employees_with_ids = Employee.objects.exclude(machine_id__isnull=True).exclude(machine_id='')
                for emp in employees_with_ids[:10]:
                    self.stdout.write(f"  {emp.user.username}: machine_id='{emp.machine_id}' (Employee ID: {emp.id}, User ID: {emp.user.id})")
                
                driver.disconnect()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
                import traceback
                self.stdout.write(traceback.format_exc())

