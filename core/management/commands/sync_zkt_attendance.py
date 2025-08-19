from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from core.zkt_service import zkt_service


class Command(BaseCommand):
    help = 'Sync attendance data from ZKT machine'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for sync (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for sync (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to sync (default: 7)',
        )

    def handle(self, *args, **options):
        start_date = None
        end_date = None

        if options['start_date']:
            start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
        if options['end_date']:
            end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()

        if not start_date and not end_date:
            # Default to last 7 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=options['days'])

        self.stdout.write(
            self.style.SUCCESS(f'Syncing attendance data from {start_date} to {end_date}')
        )

        try:
            # Sync attendance data
            synced_count = zkt_service.sync_attendance(start_date, end_date)
            
            # Process attendance logs
            processed_count = zkt_service.process_attendance_logs()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully synced {synced_count} attendance records and processed {processed_count} logs'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing attendance data: {str(e)}')
            )
