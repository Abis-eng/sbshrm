"""
Management command to initialize companies and features
Run this after migrations to set up the multi-tenant system
"""
from django.core.management.base import BaseCommand
from core.models import Company, Feature, UserProfile, Employee, Department, Designation, Project, Client, Holiday, AttendanceMachine, BudgetCategory, Asset
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Initialize companies and features for multi-tenant system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing Companies and Features...'))
        
        # Create all features
        features_data = [
            ('employees', 'Employees Management', 'Manage employees, departments, and designations'),
            ('attendance', 'Attendance Management', 'Track employee attendance and manage attendance machines'),
            ('leaves', 'Leave Management', 'Manage employee leave requests and approvals'),
            ('holidays', 'Holiday Management', 'Manage company holidays'),
            ('payroll', 'Payroll Management', 'Manage payroll, payslips, and salary calculations'),
            ('loans', 'Loan Management', 'Manage employee loans'),
            ('advances', 'Advance Requests', 'Manage advance requests'),
            ('projects', 'Project Management', 'Manage projects and project details'),
            ('tasks', 'Task Management', 'Manage tasks and assignments'),
            ('tickets', 'Ticket Management', 'Manage support tickets'),
            ('clients', 'Client Management', 'Manage clients'),
            ('budgets', 'Budget Management', 'Manage budgets and budget categories'),
            ('expenses', 'Expense Management', 'Manage budget expenses'),
            ('revenues', 'Revenue Management', 'Manage budget revenues'),
            ('assets', 'Asset Management', 'Manage company assets'),
            ('invoices', 'Invoice Management', 'Manage invoices'),
            ('estimates', 'Estimate Management', 'Manage estimates'),
            ('reports', 'Reports & Analytics', 'View reports and analytics'),
            ('chat', 'Chat & Messaging', 'Internal chat and messaging'),
            ('notifications', 'Notifications', 'System notifications'),
            ('settings', 'Settings', 'System settings'),
            ('marzi', 'Marzi Features', 'Custom Marzi-specific features'),
        ]
        
        features = {}
        for code, name, description in features_data:
            feature, created = Feature.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': description, 'is_active': True}
            )
            features[code] = feature
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created feature: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Feature already exists: {name}'))
        
        # Create default company for existing data
        default_company, created = Company.objects.get_or_create(
            slug='default-company',
            defaults={
                'name': 'Default Company',
                'description': 'Default company for existing data',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created default company: {default_company.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'  Default company already exists: {default_company.name}'))
        
        # Assign all features to default company
        default_company.features.set(Feature.objects.filter(is_active=True))
        self.stdout.write(self.style.SUCCESS(f'  Assigned all features to default company'))
        
        # Assign existing data to default company
        updated_count = 0
        
        # Update employees
        employees_updated = Employee.objects.filter(company__isnull=True).update(company=default_company)
        if employees_updated:
            updated_count += employees_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {employees_updated} employees'))
        
        # Update departments
        departments_updated = Department.objects.filter(company__isnull=True).update(company=default_company)
        if departments_updated:
            updated_count += departments_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {departments_updated} departments'))
        
        # Update designations
        designations_updated = Designation.objects.filter(company__isnull=True).update(company=default_company)
        if designations_updated:
            updated_count += designations_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {designations_updated} designations'))
        
        # Update projects
        projects_updated = Project.objects.filter(company__isnull=True).update(company=default_company)
        if projects_updated:
            updated_count += projects_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {projects_updated} projects'))
        
        # Update clients
        clients_updated = Client.objects.filter(company__isnull=True).update(company=default_company)
        if clients_updated:
            updated_count += clients_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {clients_updated} clients'))
        
        # Update holidays
        holidays_updated = Holiday.objects.filter(company__isnull=True).update(company=default_company)
        if holidays_updated:
            updated_count += holidays_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {holidays_updated} holidays'))
        
        # Update attendance machines
        machines_updated = AttendanceMachine.objects.filter(company__isnull=True).update(company=default_company)
        if machines_updated:
            updated_count += machines_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {machines_updated} attendance machines'))
        
        # Update budget categories
        budget_cats_updated = BudgetCategory.objects.filter(company__isnull=True).update(company=default_company)
        if budget_cats_updated:
            updated_count += budget_cats_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {budget_cats_updated} budget categories'))
        
        # Update assets
        assets_updated = Asset.objects.filter(company__isnull=True).update(company=default_company)
        if assets_updated:
            updated_count += assets_updated
            self.stdout.write(self.style.SUCCESS(f'  Updated {assets_updated} assets'))
        
        # Create UserProfile for existing users without profile
        users_without_profile = User.objects.filter(profile__isnull=True)
        profiles_created = 0
        for user in users_without_profile:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'company': default_company}
            )
            if created:
                profiles_created += 1
        
        if profiles_created:
            self.stdout.write(self.style.SUCCESS(f'  Created {profiles_created} user profiles'))
        
        self.stdout.write(self.style.SUCCESS(f'\nInitialization complete!'))
        self.stdout.write(self.style.SUCCESS(f'   - Created/verified {len(features)} features'))
        self.stdout.write(self.style.SUCCESS(f'   - Created/verified default company'))
        self.stdout.write(self.style.SUCCESS(f'   - Updated {updated_count} existing records'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {profiles_created} user profiles'))
        self.stdout.write(self.style.WARNING(f'\n⚠️  Next steps:'))
        self.stdout.write(self.style.WARNING(f'   1. Create additional companies in Django Admin'))
        self.stdout.write(self.style.WARNING(f'   2. Assign features to each company'))
        self.stdout.write(self.style.WARNING(f'   3. Assign Company Admins to each company'))
        self.stdout.write(self.style.WARNING(f'   4. Assign users to their respective companies'))

