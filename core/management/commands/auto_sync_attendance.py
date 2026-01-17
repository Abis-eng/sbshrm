from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from core.attendance_service import AttendanceService
from core.models import AttendanceMachine
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Automatically sync attendance data from all active machines based on their sync intervals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync all active machines regardless of sync interval',
        )
        parser.add_argument(
            '--machine-id',
            type=int,
            help='Sync only a specific machine by ID',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to sync (default: 1, meaning today only)',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        machine_id = options.get('machine_id', None)
        days = options.get('days', 1)
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)  # Include today
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting automatic attendance sync for date range: {start_date} to {end_date}'
            )
        )
        
        # Get machines to sync
        if machine_id:
            machines = AttendanceMachine.objects.filter(id=machine_id, is_active=True)
            if not machines.exists():
                self.stdout.write(
                    self.style.ERROR(f'Machine with ID {machine_id} not found or not active')
                )
                return
        else:
            machines = AttendanceMachine.objects.filter(is_active=True)
        
        if not machines.exists():
            self.stdout.write(
                self.style.WARNING('No active machines found to sync')
            )
            return
        
        total_synced = 0
        total_processed = 0
        success_count = 0
        skipped_count = 0
        error_count = 0
        
        for machine in machines:
            # Check if machine needs syncing based on sync_interval
            if not force:
                if machine.last_sync:
                    # Calculate next sync time
                    next_sync_time = machine.last_sync + timedelta(minutes=machine.sync_interval)
                    if timezone.now() < next_sync_time:
                        time_until_sync = next_sync_time - timezone.now()
                        minutes_until = int(time_until_sync.total_seconds() / 60)
                        self.stdout.write(
                            self.style.WARNING(
                                f'⏭ Skipping {machine.name}: Next sync in {minutes_until} minutes '
                                f'(last sync: {machine.last_sync.strftime("%Y-%m-%d %H:%M:%S")})'
                            )
                        )
                        skipped_count += 1
                        continue
            
            self.stdout.write(
                self.style.SUCCESS(f'🔄 Syncing {machine.name} ({machine.ip_address or "N/A"})...')
            )
            
            try:
                # Sync the machine
                result = AttendanceService.sync_machine_attendance(machine, start_date, end_date)
                
                if result['success']:
                    synced_count = result.get('synced_count', 0)
                    total_synced += synced_count
                    success_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Successfully synced {synced_count} records from {machine.name}'
                        )
                    )
                    
                    # Log any errors from the sync
                    if result.get('errors'):
                        for error in result['errors']:
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠ Warning: {error}')
                            )
                else:
                    error_count += 1
                    error_msg = result.get('message', 'Unknown error')
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to sync {machine.name}: {error_msg}'
                        )
                    )
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error syncing machine {machine.name}: {str(e)}", exc_info=True)
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error syncing {machine.name}: {str(e)}'
                    )
                )
        
        # Process attendance logs after all syncing is done
        self.stdout.write(
            self.style.SUCCESS('📊 Processing attendance logs into attendance records...')
        )
        
        try:
            processed_count = AttendanceService.process_attendance_logs()
            total_processed = processed_count
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Processed {processed_count} attendance logs into attendance records'
                )
            )
        except Exception as e:
            logger.error(f"Error processing attendance logs: {str(e)}", exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'✗ Error processing attendance logs: {str(e)}')
            )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('SYNC SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Machines synced successfully: {success_count}')
        self.stdout.write(f'  Machines skipped (not due): {skipped_count}')
        self.stdout.write(f'  Machines with errors: {error_count}')
        self.stdout.write(f'  Total records synced: {total_synced}')
        self.stdout.write(f'  Total logs processed: {total_processed}')
        self.stdout.write(self.style.SUCCESS('=' * 60))

