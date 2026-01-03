from django import forms
from django.forms import ModelForm
from .models import *
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils import timezone

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'address', 'company', 'description', 'profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

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
    priority = forms.ChoiceField(choices=Task.PRIORITY_CHOICES, widget=forms.Select(attrs={'class': 'form-control form-select'}), required=False)
    attachment = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'style': 'display: none;'}), required=False)
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Add any additional notes or instructions...'}), required=False)
    class Meta:
        model = Task
        fields = ['assigned_to', 'title', 'description', 'deadline', 'priority', 'attachment', 'comment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task title...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Provide detailed description of the task...'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control form-select'}),
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
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter category description...'}),
        } 

class BudgetForm(forms.ModelForm):
    period_start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    period_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    class Meta:
        model = Budget
        fields = ['type', 'name', 'category', 'project', 'tax', 'period_start', 'period_end', 'attachment', 'note']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter budget name...'}),
            'category': forms.Select(attrs={'class': 'form-control form-select'}),
            'project': forms.Select(attrs={'class': 'form-control form-select'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter notes...'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        } 

class BudgetExpenseForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = BudgetExpense
        fields = ['title', 'budget', 'amount', 'description', 'start_date', 'end_date', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter expense title...'}),
            'budget': forms.Select(attrs={'class': 'form-control form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter description...'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control', 'style': 'display: none;'}),
        } 

class BudgetRevenueForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = BudgetRevenue
        fields = ['title', 'budget', 'amount', 'description', 'start_date', 'end_date', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter revenue title...'}),
            'budget': forms.Select(attrs={'class': 'form-control form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter description...'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control', 'style': 'display: none;'}),
        } 

class AssetForm(forms.ModelForm):
    purchase_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    warranty_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = Asset
        fields = ['asset_name', 'asset_id', 'purchase_date', 'purchase_from', 'manufacturer', 'model', 'serial_number', 'brand', 'supplier', 'condition', 'warranty', 'warranty_end', 'cost', 'asset_user', 'status', 'description', 'files']
        widgets = {
            'asset_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter asset name...'}),
            'asset_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter unique asset ID...'}),
            'purchase_from': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter purchase source...'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter manufacturer...'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter model...'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter serial number...'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter brand...'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter supplier...'}),
            'condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter condition...'}),
            'warranty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter warranty details...'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'status': forms.Select(attrs={'class': 'form-control form-select'}),
            'asset_user': forms.Select(attrs={'class': 'form-control form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter description...'}),
            'files': forms.ClearableFileInput(attrs={'class': 'form-control', 'style': 'display: none;'}),
        } 

class CompanySettingsForm(forms.ModelForm):
    email_host_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Leave blank to keep current password'
        }),
        help_text="Leave blank to keep current password"
    )
    
    class Meta:
        model = CompanySettings
        fields = ['company_name', 'contact_person', 'address', 'country', 'city', 'state_province', 'postal_code', 'email', 'phone_number', 'mobile_number', 'fax', 'website_url', 'logo',
                  'email_host', 'email_port', 'email_use_tls', 'email_use_ssl', 'email_host_user', 'email_host_password', 'email_from_name', 'email_enabled']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state_province': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'website_url': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'email_host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'smtp.gmail.com'}),
            'email_port': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 65535}),
            'email_use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_use_ssl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_host_user': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your-email@gmail.com'}),
            'email_from_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'HRM System'}),
            'email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Only update password if a new one was provided
        password = self.cleaned_data.get('email_host_password')
        if password:
            instance.email_host_password = password
        elif not instance.pk:
            # If creating new and no password provided, set empty
            instance.email_host_password = ''
        
        if commit:
            instance.save()
        return instance 

class LocalizationSettingsForm(forms.ModelForm):
    class Meta:
        model = LocalizationSettings
        fields = ['default_language', 'timezone', 'date_format', 'time_format', 'currency', 'currency_symbol', 'thousand_separator', 'decimal_separator']
        widgets = {
            'default_language': forms.Select(attrs={'class': 'form-control form-select'}),
            'timezone': forms.Select(attrs={'class': 'form-control form-select'}),
            'date_format': forms.TextInput(attrs={'class': 'form-control'}),
            'time_format': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control form-select', 'id': 'id_currency'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control', 'readonly': True, 'id': 'id_currency_symbol'}),
            'thousand_separator': forms.TextInput(attrs={'class': 'form-control'}),
            'decimal_separator': forms.TextInput(attrs={'class': 'form-control'}),
        } 

class InvoiceSettingsForm(forms.ModelForm):
    class Meta:
        model = InvoiceSettings
        fields = ['prefix', 'logo']
        widgets = {
            'prefix': forms.TextInput(attrs={'class': 'form-control'}),
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
            'app_name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo_light': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'logo_dark': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'layout': forms.Select(attrs={'class': 'form-control form-select'}),
            'layout_width': forms.Select(attrs={'class': 'form-control form-select'}),
            'color_scheme': forms.Select(attrs={'class': 'form-control form-select'}),
            'layout_position': forms.Select(attrs={'class': 'form-control form-select'}),
            'topbar_color': forms.Select(attrs={'class': 'form-control form-select'}),
            'sidebar_size': forms.Select(attrs={'class': 'form-control form-select'}),
            'sidebar_view': forms.Select(attrs={'class': 'form-control form-select'}),
            'sidebar_color': forms.Select(attrs={'class': 'form-control form-select'}),
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
    """Form for manual attendance entry - Direct attendance record creation"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('leave', 'Leave'),
        ('holiday', 'Holiday'),
    ]
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.select_related('user').all().order_by('user__first_name', 'user__last_name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Employee",
        required=True
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date",
        initial=timezone.now().date(),
        required=True
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Status",
        required=True,
        initial='present'
    )
    check_in = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'id': 'id_check_in'}, format='%Y-%m-%dT%H:%M'),
        label="Check In",
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    check_out = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'id': 'id_check_out'}, format='%Y-%m-%dT%H:%M'),
        label="Check Out",
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    break_start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'id': 'id_break_start'}, format='%Y-%m-%dT%H:%M'),
        label="Break Start",
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    break_end = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'id': 'id_break_end'}, format='%Y-%m-%dT%H:%M'),
        label="Break End",
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    is_late = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Is Late",
        required=False
    )
    late_minutes = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        label="Late Minutes",
        required=False,
        initial=0
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="Notes"
    )

class AttendanceMachineForm(ModelForm):
    """Form for managing attendance machines with support for multiple machine types"""
    
    class Meta:
        model = AttendanceMachine
        fields = [
            'name', 'machine_type', 'protocol', 'ip_address', 'port', 'url',
            'serial_port', 'baud_rate', 'username', 'password', 'api_key',
            'location', 'is_active', 'sync_interval', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'machine_type': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'protocol': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'port': forms.NumberInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://api.example.com'}),
            'serial_port': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'COM1 or /dev/ttyUSB0'}),
            'baud_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'render_value': True}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 1440, 'value': 15}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        help_texts = {
            'machine_type': 'Select the brand/type of your biometric machine',
            'protocol': 'Select the connection protocol used by the machine',
            'url': 'Full URL for HTTP/HTTPS/API connections (e.g., https://api.example.com)',
            'serial_port': 'COM port for serial connection (Windows: COM1, Linux: /dev/ttyUSB0)',
            'api_key': 'API key for API-based machines',
            'sync_interval': 'How often to sync data in minutes (1-1440)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields conditionally required based on protocol
        protocol = None
        
        if self.instance and self.instance.pk:
            # Editing existing machine
            protocol = self.instance.protocol
        elif args and len(args) > 0:
            # Form submitted via POST - check POST data
            data = args[0]
            protocol = data.get('protocol', None)
        else:
            # New form - check initial data
            protocol = self.initial.get('protocol', AttendanceMachine.PROTOCOL_TCP_IP)
        
        # Default to TCP/IP if protocol not set
        if not protocol:
            protocol = AttendanceMachine.PROTOCOL_TCP_IP
        
        # Set default value for sync_interval if not provided
        if not self.instance.pk and 'sync_interval' not in self.initial:
            self.fields['sync_interval'].initial = 15
        
        # Show/hide fields based on protocol
        if protocol == AttendanceMachine.PROTOCOL_TCP_IP:
            self.fields['ip_address'].required = True
            self.fields['port'].required = True
            self.fields['url'].required = False
            self.fields['serial_port'].required = False
        elif protocol in [AttendanceMachine.PROTOCOL_HTTP, AttendanceMachine.PROTOCOL_HTTPS]:
            self.fields['url'].required = True
            self.fields['ip_address'].required = False
            self.fields['port'].required = False
            self.fields['serial_port'].required = False
        elif protocol == AttendanceMachine.PROTOCOL_SERIAL:
            self.fields['serial_port'].required = True
            self.fields['ip_address'].required = False
            self.fields['port'].required = False
            self.fields['url'].required = False
        else:
            self.fields['url'].required = True
            self.fields['ip_address'].required = False
            self.fields['port'].required = False
            self.fields['serial_port'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        protocol = cleaned_data.get('protocol')
        
        # Additional validation based on protocol
        if protocol == AttendanceMachine.PROTOCOL_TCP_IP:
            if not cleaned_data.get('ip_address'):
                self.add_error('ip_address', 'IP address is required for TCP/IP protocol.')
            if not cleaned_data.get('port'):
                self.add_error('port', 'Port is required for TCP/IP protocol.')
        elif protocol in [AttendanceMachine.PROTOCOL_HTTP, AttendanceMachine.PROTOCOL_HTTPS]:
            if not cleaned_data.get('url'):
                self.add_error('url', 'URL is required for HTTP/HTTPS protocol.')
        elif protocol == AttendanceMachine.PROTOCOL_SERIAL:
            if not cleaned_data.get('serial_port'):
                self.add_error('serial_port', 'Serial port is required for Serial protocol.')
        
        return cleaned_data

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
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.select_related('user').all(), 
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select Employee'
        }),
        empty_label='-- Select Employee --'
    )
    period_start = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control',
            'placeholder': 'mm/dd/yyyy'
        })
    )
    period_end = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control',
            'placeholder': 'mm/dd/yyyy'
        })
    )
    base_salary = forms.DecimalField(
        required=False, 
        min_value=0, 
        decimal_places=2, 
        max_digits=10, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'step': '0.01',
            'placeholder': '0.00'
        }), 
        help_text='Leave blank to use employee profile salary'
    )
    send_email = forms.BooleanField(
        required=False, 
        initial=False, 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), 
        label='Email payslip to employee'
    )

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

class PayslipRegisterEditForm(forms.Form):
    """Comprehensive form for editing all payslip amounts shown in register"""
    # Basic fields
    base_pay = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Basic Pay'
    )
    work_days = forms.IntegerField(
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number'
        }),
        label='Work Days'
    )
    absences = forms.IntegerField(
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number'
        }),
        label='Absences'
    )
    leaves = forms.IntegerField(
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number'
        }),
        label='Leaves'
    )
    basic_salary = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Basic Salary'
    )
    
    # Allowances
    allowance_fuel = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Allowance - Fuel'
    )
    allowance_mobile = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Allowance - Mobile'
    )
    allowance_other = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Allowance - Other'
    )
    
    # Gross and Net
    gross_pay = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Gross Salary'
    )
    
    # Opening/Closing Balance
    opening_balance = forms.DecimalField(
        required=True,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Opening Balance'
    )
    
    # Deductions
    deduction_add = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Deduction - Add'
    )
    deduction_ded = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Deduction - Ded.'
    )
    deduction_other = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Deduction - Other'
    )
    
    closing_balance = forms.DecimalField(
        required=True,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Closing Balance'
    )
    
    # Net Pay
    net_pay = forms.DecimalField(
        required=True,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Net Pay'
    )
    
    # Payslip fields
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=True
    )
    period_start = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False
    )
    period_end = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False
    )
    status = forms.ChoiceField(
        choices=[('pending', 'Pending'), ('processed', 'Processed'), ('paid', 'Paid')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True
    )

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

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'attachment', 'image_display_mode', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter notice title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter notice content (optional if file is attached)'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.webp'}),
            'image_display_mode': forms.Select(attrs={'class': 'form-control form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MonthlyPayrollForm(forms.Form):
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    city = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'id': 'id_city'
        })
    )
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All Departments',
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'id': 'id_department'
        })
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        })
    )
    year = forms.IntegerField(
        required=True,
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Year (e.g., 2025)'
        })
    )
    days_of_month = forms.IntegerField(
        required=True,
        min_value=28,
        max_value=31,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Days in month'
        })
    )
    
    def __init__(self, *args, **kwargs):
        city_filter = kwargs.pop('city_filter', None)
        super().__init__(*args, **kwargs)
        from .models import Department, Employee
        
        # Get all unique cities from employees
        cities = Employee.objects.exclude(city__isnull=True).exclude(city='').values_list('city', flat=True).distinct().order_by('city')
        city_choices = [('', 'All Cities')] + [(city, city) for city in cities]
        self.fields['city'].choices = city_choices
        
        # Filter departments by city if city is provided
        if city_filter:
            self.fields['department'].queryset = Department.objects.filter(
                employees__city=city_filter
            ).distinct().order_by('name')
        else:
            self.fields['department'].queryset = Department.objects.all().order_by('name')