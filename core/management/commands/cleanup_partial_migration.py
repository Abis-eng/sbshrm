"""
Management command to clean up partial migration 0040
Drops Company table and related fields if they exist
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Clean up partial migration 0040 by dropping Company table and related fields'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write('Cleaning up partial migration...')
            
            # Drop foreign key constraints first
            try:
                cursor.execute("""
                    SELECT CONSTRAINT_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME LIKE 'core_%' 
                    AND REFERENCED_TABLE_NAME = 'core_company'
                """)
                constraints = cursor.fetchall()
                for constraint in constraints:
                    table_name = constraint[0].split('_')[0] + '_' + constraint[0].split('_')[1]
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} DROP FOREIGN KEY {constraint[0]}")
                        self.stdout.write(self.style.SUCCESS(f'  Dropped constraint {constraint[0]}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  Could not drop constraint {constraint[0]}: {e}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Could not find constraints: {e}'))
            
            # Drop company fields from various tables
            tables_to_clean = [
                'core_client',
                'core_asset',
                'core_attendancemachine',
                'core_budget',
                'core_budgetcategory',
                'core_department',
                'core_designation',
                'core_employee',
                'core_holiday',
                'core_project',
            ]
            
            for table in tables_to_clean:
                try:
                    cursor.execute(f"ALTER TABLE {table} DROP COLUMN company_id")
                    self.stdout.write(self.style.SUCCESS(f'  Dropped company_id from {table}'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Could not drop company_id from {table}: {e}'))
            
            # Drop many-to-many table
            try:
                cursor.execute("DROP TABLE IF EXISTS core_feature_companies")
                self.stdout.write(self.style.SUCCESS('  Dropped core_feature_companies table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Could not drop core_feature_companies: {e}'))
            
            # Drop Feature and UserProfile tables
            try:
                cursor.execute("DROP TABLE IF EXISTS core_userprofile")
                self.stdout.write(self.style.SUCCESS('  Dropped core_userprofile table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Could not drop core_userprofile: {e}'))
            
            try:
                cursor.execute("DROP TABLE IF EXISTS core_feature")
                self.stdout.write(self.style.SUCCESS('  Dropped core_feature table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Could not drop core_feature: {e}'))
            
            # Drop Company table last
            try:
                cursor.execute("DROP TABLE IF EXISTS core_company")
                self.stdout.write(self.style.SUCCESS('  Dropped core_company table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Could not drop core_company: {e}'))
            
            self.stdout.write(self.style.SUCCESS('\nCleanup complete! You can now run migrations again.'))

