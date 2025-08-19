from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

# Create your models here.

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Designation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey('Designation', on_delete=models.SET_NULL, null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    PAY_FREQUENCY_MONTHLY = 'monthly'
    PAY_FREQUENCY_BIWEEKLY = 'biweekly'
    PAY_FREQUENCY_WEEKLY = 'weekly'
    PAY_FREQUENCY_CHOICES = [
        (PAY_FREQUENCY_MONTHLY, 'Monthly'),
        (PAY_FREQUENCY_BIWEEKLY, 'Bi-weekly'),
        (PAY_FREQUENCY_WEEKLY, 'Weekly'),
    ]
    pay_frequency = models.CharField(max_length=10, choices=PAY_FREQUENCY_CHOICES, default=PAY_FREQUENCY_MONTHLY)
    last_pay_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    is_restricted = models.BooleanField(default=False)
    can_view_attendance = models.BooleanField(default=True)
    can_view_tasks = models.BooleanField(default=True)
    can_view_department = models.BooleanField(default=True)
    can_view_designation = models.BooleanField(default=True)
    can_view_holidays = models.BooleanField(default=True)
    can_view_leaves = models.BooleanField(default=True)
    # New fields for ZKT machine integration
    machine_id = models.CharField(max_length=50, blank=True, null=True, help_text="Employee ID registered in the ZKT machine")
    fingerprint_id = models.CharField(max_length=50, blank=True, null=True, help_text="Fingerprint ID in the ZKT machine")
    face_id = models.CharField(max_length=50, blank=True, null=True, help_text="Face ID in the ZKT machine")
    card_id = models.CharField(max_length=50, blank=True, null=True, help_text="Card ID in the ZKT machine")

    def __str__(self):
        return str(self.user)

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender} to {self.recipient}: {self.content[:20]}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets_created')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_assigned')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"

class OnlineUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} (online)"

class AttendanceMachine(models.Model):
    name = models.CharField(max_length=100, default="ZKT K70")
    ip_address = models.GenericIPAddressField(default="192.168.18.1")
    port = models.IntegerField(default=4370)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port})"

class AttendanceLog(models.Model):
    ATTENDANCE_TYPE_CHOICES = [
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
        ('break_start', 'Break Start'),
        ('break_end', 'Break End'),
    ]
    
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('machine', 'ZKT Machine'),
        ('api', 'API'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_logs')
    attendance_type = models.CharField(max_length=20, choices=ATTENDANCE_TYPE_CHOICES)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
    timestamp = models.DateTimeField()
    machine_timestamp = models.DateTimeField(null=True, blank=True, help_text="Original timestamp from the machine")
    machine_id = models.CharField(max_length=50, blank=True, null=True, help_text="Machine ID if from ZKT device")
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['employee', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.employee} - {self.get_attendance_type_display()} at {self.timestamp}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('holiday', 'Holiday'),
        ('leave', 'Leave'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)
    total_work_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_break_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    is_late = models.BooleanField(default=False)
    late_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.status})"
    
    def calculate_hours(self):
        """Calculate total work hours and break hours"""
        if self.check_in and self.check_out:
            work_duration = self.check_out - self.check_in
            self.total_work_hours = round(work_duration.total_seconds() / 3600, 2)
        
        if self.break_start and self.break_end:
            break_duration = self.break_end - self.break_start
            self.total_break_hours = round(break_duration.total_seconds() / 3600, 2)
        
        self.save()

# SalarySlip model removed. PayrollItem and Payslip models will be added.

class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"

class Leave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.employee} {self.leave_type} {self.start_date} - {self.end_date}"

class PayrollItem(models.Model):
    EARNING = 'earning'
    DEDUCTION = 'deduction'
    ITEM_TYPE_CHOICES = [
        (EARNING, 'Earning'),
        (DEDUCTION, 'Deduction'),
    ]
    CATEGORY_BASE = 'base'
    CATEGORY_ALLOWANCE = 'allowance'
    CATEGORY_BONUS = 'bonus'
    CATEGORY_OVERTIME = 'overtime'
    CATEGORY_COMMISSION = 'commission'
    CATEGORY_TAX = 'tax'
    CATEGORY_PF = 'pf'
    CATEGORY_LOAN = 'loan'
    CATEGORY_CUSTOM = 'custom'
    CATEGORY_CHOICES = [
        (CATEGORY_BASE, 'Base Salary'),
        (CATEGORY_ALLOWANCE, 'Allowance'),
        (CATEGORY_BONUS, 'Bonus'),
        (CATEGORY_OVERTIME, 'Overtime'),
        (CATEGORY_COMMISSION, 'Commission'),
        (CATEGORY_TAX, 'Income Tax'),
        (CATEGORY_PF, 'Provident/Social Security'),
        (CATEGORY_LOAN, 'Loan/Advance'),
        (CATEGORY_CUSTOM, 'Custom'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_items')
    date = models.DateField(default=timezone.now)
    name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_CUSTOM)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.item_type})"

class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    STATUS_PENDING = 'pending'
    STATUS_PROCESSED = 'processed'
    STATUS_PAID = 'paid'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSED, 'Processed'),
        (STATUS_PAID, 'Paid'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PROCESSED)
    pdf = models.FileField(upload_to='payslips/', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payslip: {str(self.employee)} - {self.date}"

    def get_payroll_items(self):
        from .models import PayrollItem
        return PayrollItem.objects.filter(employee=self.employee)

class TaxSlab(models.Model):
    name = models.CharField(max_length=100, default='Default')
    min_income = models.DecimalField(max_digits=12, decimal_places=2)
    max_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rate_percent = models.DecimalField(max_digits=5, decimal_places=2)
    fixed_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        top = '∞' if self.max_income is None else self.max_income
        return f"{self.name}: {self.min_income} - {top} @ {self.rate_percent}%"

class Loan(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Loan for {self.employee} (balance {self.balance})"

class MonthlyPayrollRun(models.Model):
    period_start = models.DateField(unique=True)
    period_end = models.DateField(unique=True)
    run_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payroll Run {self.period_start} - {self.period_end} at {self.run_at}"

class AdvanceRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='advance_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    desired_installments = models.PositiveIntegerField(null=True, blank=True, help_text="Optional number of monthly installments")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='advance_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True)

    def __str__(self):
        return f"Advance {self.employee} {self.amount} ({self.status})"

class Client(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=200)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')
    # team = models.ManyToManyField(Employee, related_name='projects')  # Remove or comment out

    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks_assigned')
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks_received')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    deadline = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status}) for {self.assigned_to}"

class BudgetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Budget(models.Model):
    TYPE_CHOICES = [
        ('project', 'Project'),
        ('category', 'Category'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='project')
    name = models.CharField(max_length=100)
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, related_name='budgets', null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets')
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    period_start = models.DateField()
    period_end = models.DateField()
    attachment = models.FileField(upload_to='budget_attachments/', null=True, blank=True)
    note = models.TextField(blank=True)
    # amount is now calculated, not user input

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class BudgetExpense(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    attachment = models.FileField(upload_to='budget_expense_attachments/', null=True, blank=True)

    def __str__(self):
        return f"Expense: {self.title} ({self.amount}) for {self.budget.name}"

class BudgetRevenue(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='revenues')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    attachment = models.FileField(upload_to='budget_revenue_attachments/', null=True, blank=True)

    def __str__(self):
        return f"Revenue: {self.title} ({self.amount}) for {self.budget.name}"

class Asset(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('pending', 'Pending'),
        ('returned', 'Returned'),
    ]
    asset_name = models.CharField(max_length=255)
    asset_id = models.CharField(max_length=100, unique=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_from = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=255, blank=True)
    brand = models.CharField(max_length=255, blank=True)
    supplier = models.CharField(max_length=255, blank=True)
    condition = models.CharField(max_length=255, blank=True)
    warranty = models.CharField(max_length=100, blank=True)
    warranty_end = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    asset_user = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    description = models.TextField(blank=True)
    files = models.FileField(upload_to='asset_files/', null=True, blank=True)

    def __str__(self):
        return f"{self.asset_name} ({self.asset_id})"

class CompanySettings(models.Model):
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    mobile_number = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    website_url = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.company_name or 'Company Settings'

class LocalizationSettings(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ur', 'Urdu'),
        ('ar', 'Arabic'),
        # Add more as needed
    ]
    TIMEZONE_CHOICES = [
        ('Asia/Karachi', 'Asia/Karachi'),
        ('Asia/Dubai', 'Asia/Dubai'),
        ('UTC', 'UTC'),
        # Add more as needed
    ]
    default_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='Asia/Karachi')
    date_format = models.CharField(max_length=20, default='%Y-%m-%d')
    time_format = models.CharField(max_length=20, default='%H:%M')
    currency = models.CharField(max_length=10, default='PKR')
    currency_symbol = models.CharField(max_length=5, default='₨')
    thousand_separator = models.CharField(max_length=2, default=',')
    decimal_separator = models.CharField(max_length=2, default='.')

    def __str__(self):
        return f"Localization ({self.default_language}, {self.timezone})"

class InvoiceSettings(models.Model):
    prefix = models.CharField(max_length=20, default='INV-')
    logo = models.ImageField(upload_to='invoice_logos/', blank=True, null=True)

    def __str__(self):
        return f"Invoice Settings ({self.prefix})"

class SalarySettings(models.Model):
    # DA and HRA
    da_enabled = models.BooleanField(default=False)
    da_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    hra_enabled = models.BooleanField(default=False)
    hra_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Provident Fund
    pf_enabled = models.BooleanField(default=False)
    pf_employee_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pf_org_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # ESI
    esi_enabled = models.BooleanField(default=False)
    esi_employee_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    esi_org_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Gratuity
    gratuity_enabled = models.BooleanField(default=False)
    gratuity_employee_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gratuity_org_share = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return "Salary Settings"

class ThemeSettings(models.Model):
    LAYOUT_CHOICES = [
        ('vertical', 'Vertical'),
        ('horizontal', 'Horizontal'),
    ]
    LAYOUT_WIDTH_CHOICES = [
        ('fluid', 'Fluid'),
        ('boxed', 'Boxed'),
    ]
    COLOR_SCHEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('orange', 'Orange'),
        ('blue', 'Blue'),
        ('maroon', 'Maroon'),
        ('purple', 'Purple'),
    ]
    LAYOUT_POSITION_CHOICES = [
        ('scrollable', 'Scrollable'),
        ('fixed', 'Fixed'),
    ]
    TOPBAR_COLOR_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]
    SIDEBAR_SIZE_CHOICES = [
        ('default', 'Default'),
        ('small', 'Small'),
        ('large', 'Large'),
    ]
    SIDEBAR_VIEW_CHOICES = [
        ('default', 'Default'),
        ('compact', 'Compact'),
    ]
    SIDEBAR_COLOR_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]
    app_name = models.CharField(max_length=100, default='SBS HRM')
    logo_light = models.ImageField(upload_to='theme_logos/', blank=True, null=True)
    logo_dark = models.ImageField(upload_to='theme_logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='theme_favicons/', blank=True, null=True)
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='vertical')
    layout_width = models.CharField(max_length=20, choices=LAYOUT_WIDTH_CHOICES, default='fluid')
    color_scheme = models.CharField(max_length=20, choices=COLOR_SCHEME_CHOICES, default='light')
    layout_position = models.CharField(max_length=20, choices=LAYOUT_POSITION_CHOICES, default='scrollable')
    topbar_color = models.CharField(max_length=20, choices=TOPBAR_COLOR_CHOICES, default='light')
    sidebar_size = models.CharField(max_length=20, choices=SIDEBAR_SIZE_CHOICES, default='default')
    sidebar_view = models.CharField(max_length=20, choices=SIDEBAR_VIEW_CHOICES, default='default')
    sidebar_color = models.CharField(max_length=20, choices=SIDEBAR_COLOR_CHOICES, default='dark')

    def __str__(self):
        return f"Theme Settings ({self.app_name})"

class Tax(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

class Expense(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    item_name = models.CharField(max_length=200)
    purchased_from = models.CharField(max_length=200)
    purchased_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.item_name} - {self.amount}";

class Estimate(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)
    tax = models.ForeignKey('Tax', on_delete=models.SET_NULL, null=True, blank=True)
    client_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    estimate_date = models.DateField()
    expiry_date = models.DateField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    other_info = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Estimate #{self.id} - {self.client.name}"

class EstimateItem(models.Model):
    estimate = models.ForeignKey(Estimate, on_delete=models.CASCADE, related_name='items')
    item = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.item} ({self.estimate})"

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)
    tax = models.ForeignKey('Tax', on_delete=models.SET_NULL, null=True, blank=True)
    client_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    other_info = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.client.name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.item} ({self.invoice})"
