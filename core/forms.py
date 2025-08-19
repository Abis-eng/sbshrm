from django import forms
from django.forms import ModelForm
from .models import *
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils import timezone

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'address', 'company', 'description']

class UserAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'is_active', 'is_staff', 'is_superuser']

class GroupedEmployeeChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.department.name}, {obj.designation.name})"

class GroupedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def optgroups(self, name, value, attrs=None):
        # Group employees by department
        employees = self.choices.queryset.select_related('department', 'designation')
        department_map = {}
        for emp in employees:
            dept = emp.department.name if emp.department else 'No Department'
            department_map.setdefault(dept, []).append(emp)
        groups = []
        for dept, emps in sorted(department_map.items()):
            group_choices = [(emp.pk, str(emp), emp.pk in value) for emp in emps]
            groups.append((dept, group_choices, 0))
        return groups

class ProjectForm(forms.ModelForm):
    manager = forms.ModelChoiceField(
        queryset=Employee.objects.none(),  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='Project Manager',
        to_field_name=None,
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only employees with designation 'Project Manager'
        self.fields['manager'].queryset = Employee.objects.select_related('department', 'designation').filter(designation__name='Project Manager')
        self.fields['manager'].label_from_instance = lambda obj: f"{obj.user.get_full_name() or obj.user.username} ({obj.department.name}, {obj.designation.name}) - Project Manager"

    class Meta:
        model = Project
        fields = ['name', 'client', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control', 'data-live-search': 'true'}),
        }

class TaskForm(forms.ModelForm):
    deadline = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    priority = forms.ChoiceField(choices=Task.PRIORITY_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    attachment = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), required=False)
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}), required=False)
    class Meta:
        model = Task
        fields = ['assigned_to', 'title', 'description', 'deadline', 'priority', 'attachment', 'comment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        manager = kwargs.pop('manager', None)
        super().__init__(*args, **kwargs)
        # Only show employees who are not the manager
        if manager:
            self.fields['assigned_to'].queryset = Employee.objects.exclude(id=manager.id)
        else:
            self.fields['assigned_to'].queryset = Employee.objects.all() 

class BudgetCategoryForm(forms.ModelForm):
    class Meta:
        model = BudgetCategory
        fields = ['name', 'description'] 

class BudgetForm(forms.ModelForm):
    period_start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    period_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    class Meta:
        model = Budget
        fields = ['type', 'name', 'category', 'project', 'tax', 'period_start', 'period_end', 'attachment', 'note'] 

class BudgetExpenseForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = BudgetExpense
        fields = ['title', 'budget', 'amount', 'description', 'start_date', 'end_date', 'attachment'] 

class BudgetRevenueForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = BudgetRevenue
        fields = ['title', 'budget', 'amount', 'description', 'start_date', 'end_date', 'attachment'] 

class AssetForm(forms.ModelForm):
    purchase_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    warranty_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = Asset
        fields = ['asset_name', 'asset_id', 'purchase_date', 'purchase_from', 'manufacturer', 'model', 'serial_number', 'brand', 'supplier', 'condition', 'warranty', 'warranty_end', 'cost', 'asset_user', 'status', 'description', 'files']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'asset_user': forms.Select(attrs={'class': 'form-control'}),
        } 

class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = ['company_name', 'contact_person', 'address', 'country', 'city', 'state_province', 'postal_code', 'email', 'phone_number', 'mobile_number', 'fax', 'website_url'] 

class LocalizationSettingsForm(forms.ModelForm):
    class Meta:
        model = LocalizationSettings
        fields = ['default_language', 'timezone', 'date_format', 'time_format', 'currency', 'currency_symbol', 'thousand_separator', 'decimal_separator'] 

class InvoiceSettingsForm(forms.ModelForm):
    class Meta:
        model = InvoiceSettings
        fields = ['prefix', 'logo']
        widgets = {
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        } 

class SalarySettingsForm(forms.ModelForm):
    class Meta:
        model = SalarySettings
        fields = [
            'da_enabled', 'da_percent', 'hra_enabled', 'hra_percent',
            'pf_enabled', 'pf_employee_share', 'pf_org_share',
            'esi_enabled', 'esi_employee_share', 'esi_org_share',
            'gratuity_enabled', 'gratuity_employee_share', 'gratuity_org_share',
        ]
        widgets = {
            'da_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'hra_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'pf_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'esi_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'gratuity_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'da_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hra_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pf_employee_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pf_org_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esi_employee_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esi_org_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gratuity_employee_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gratuity_org_share': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        } 

class ThemeSettingsForm(forms.ModelForm):
    class Meta:
        model = ThemeSettings
        fields = [
            'app_name', 'logo_light', 'logo_dark', 'favicon',
            'layout', 'layout_width', 'color_scheme', 'layout_position',
            'topbar_color', 'sidebar_size', 'sidebar_view', 'sidebar_color',
        ]
        widgets = {
            'logo_light': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'logo_dark': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'layout': forms.Select(attrs={'class': 'form-select'}),
            'layout_width': forms.Select(attrs={'class': 'form-select'}),
            'color_scheme': forms.Select(attrs={'class': 'form-select'}),
            'layout_position': forms.Select(attrs={'class': 'form-select'}),
            'topbar_color': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_size': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_view': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_color': forms.Select(attrs={'class': 'form-select'}),
        } 

class TaxForm(forms.ModelForm):
    class Meta:
        model = Tax
        fields = ['name', 'percentage', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax name'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter percentage: 10', 'step': '0.01'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['item_name', 'purchased_from', 'purchased_date', 'amount', 'paid_by', 'status']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item Name'}),
            'purchased_from': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Purchased From'}),
            'purchased_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount', 'step': '0.01'}),
            'paid_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Paid By'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        } 

class EstimateForm(forms.ModelForm):
    class Meta:
        model = Estimate
        fields = ['client', 'project', 'tax', 'client_address', 'billing_address', 'estimate_date', 'expiry_date', 'discount', 'other_info']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'tax': forms.Select(attrs={'class': 'form-select'}),
            'client_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estimate_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class EstimateItemForm(forms.ModelForm):
    class Meta:
        model = EstimateItem
        fields = ['item', 'description', 'unit_cost', 'quantity', 'amount']
        widgets = {
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '1'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        } 

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'project', 'tax', 'client_address', 'billing_address', 'invoice_date', 'due_date', 'discount', 'other_info', 'status']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item', 'description', 'unit_cost', 'quantity', 'amount'] 

class EmployeeMachineForm(ModelForm):
    """Form for managing employee machine IDs"""
    class Meta:
        model = Employee
        fields = ['machine_id', 'fingerprint_id', 'face_id', 'card_id']
        widgets = {
            'machine_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Machine ID'}),
            'fingerprint_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Fingerprint ID'}),
            'face_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Face ID'}),
            'card_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Card ID'}),
        }

class ManualAttendanceForm(forms.Form):
    """Form for manual attendance entry"""
    ATTENDANCE_TYPE_CHOICES = [
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
        ('break_start', 'Break Start'),
        ('break_end', 'Break End'),
    ]
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Employee"
    )
    attendance_type = forms.ChoiceField(
        choices=ATTENDANCE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Attendance Type"
    )
    timestamp = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        label="Timestamp",
        initial=timezone.now
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="Notes"
    )

class AttendanceMachineForm(ModelForm):
    """Form for managing attendance machines"""
    class Meta:
        model = AttendanceMachine
        fields = ['name', 'ip_address', 'port', 'location', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'port': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Employee"
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Start Date"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="End Date"
    )
    status = forms.ChoiceField(
        choices=[('', 'All')] + Attendance.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Status"
    )
    source = forms.ChoiceField(
        choices=[('', 'All')] + AttendanceLog.SOURCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Source"
    ) 

class PayrollItemForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    class Meta:
        model = PayrollItem
        fields = ['employee', 'date', 'name', 'item_type', 'category', 'amount', 'description', 'is_recurring', 'start_date', 'end_date']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class PayslipCreateForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.select_related('user').all(), widget=forms.Select(attrs={'class': 'form-control'}))
    period_start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    period_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    base_salary = forms.DecimalField(required=False, min_value=0, decimal_places=2, max_digits=10, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}), help_text='Leave blank to use employee profile salary')
    send_email = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), label='Email payslip to employee')

class PayslipEditForm(forms.ModelForm):
    period_start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    period_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = Payslip
        fields = ['date', 'period_start', 'period_end', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class TaxSlabForm(forms.ModelForm):
    class Meta:
        model = TaxSlab
        fields = ['name', 'min_income', 'max_income', 'rate_percent', 'fixed_deduction']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'min_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rate_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fixed_deduction': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['employee', 'principal_amount', 'monthly_installment', 'balance', 'start_date', 'end_date', 'is_active']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'principal_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'monthly_installment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class AdvanceRequestForm(forms.ModelForm):
    class Meta:
        model = AdvanceRequest
        fields = ['amount', 'reason', 'desired_installments']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'desired_installments': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '1'}),
        }

class AdvanceReviewForm(forms.ModelForm):
    action = forms.ChoiceField(choices=[('approve', 'Approve'), ('reject', 'Reject')], widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = AdvanceRequest
        fields = ['admin_comment']
        widgets = {
            'admin_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }