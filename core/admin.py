from .models import (
    Department, Employee, Designation, Holiday, Leave, BudgetCategory, Budget, BudgetExpense, 
    BudgetRevenue, Asset, CompanySettings, LocalizationSettings, InvoiceSettings, SalarySettings, 
    ThemeSettings, Tax, Expense, Estimate, EstimateItem, Invoice, InvoiceItem, Attendance, 
    AttendanceLog, AttendanceMachine, Company, Feature, UserProfile, EmployeeScreenshot
)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Customize admin site
admin.site.site_header = "HRM System - Super Admin"
admin.site.site_title = "HRM Admin"
admin.site.index_title = "Multi-Tenant Company Management"

# Register your models here.

admin.site.register(Department)
admin.site.register(Employee)
# SalarySlip admin removed. PayrollItem and Payslip admin will be added.
admin.site.register(Designation)
admin.site.register(Holiday)
admin.site.register(Leave)
admin.site.register(BudgetCategory)
# No need to reference 'amount' or 'description' for Budget admin registration
admin.site.register(Budget)
admin.site.register(BudgetExpense)
admin.site.register(BudgetRevenue)
admin.site.register(Asset)
admin.site.register(CompanySettings)
admin.site.register(LocalizationSettings)
admin.site.register(InvoiceSettings)
admin.site.register(SalarySettings)
admin.site.register(ThemeSettings)
admin.site.register(Tax)
admin.site.register(Expense)
admin.site.register(Estimate)
admin.site.register(EstimateItem)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)

# Attendance models
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status', 'check_in', 'check_out', 'total_work_hours', 'is_late']
    list_filter = ['status', 'date', 'is_late', 'employee__department']
    search_fields = ['employee__user__username', 'employee__user__first_name', 'employee__user__last_name']
    date_hierarchy = 'date'

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'attendance_type', 'source', 'timestamp', 'machine_id']
    list_filter = ['attendance_type', 'source', 'timestamp', 'employee__department']
    search_fields = ['employee__user__username', 'machine_id', 'notes']
    date_hierarchy = 'timestamp'

@admin.register(AttendanceMachine)
class AttendanceMachineAdmin(admin.ModelAdmin):
    list_display = ['name', 'machine_type', 'protocol', 'get_connection_display', 'location', 'is_active', 'last_sync']
    list_filter = ['is_active', 'machine_type', 'protocol', 'location']
    search_fields = ['name', 'ip_address', 'location', 'description']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'machine_type', 'protocol', 'location', 'description', 'is_active')
        }),
        ('Network Configuration (TCP/IP, HTTP, HTTPS, WebSocket)', {
            'fields': ('ip_address', 'port', 'url'),
            'classes': ('collapse',)
        }),
        ('Serial/USB Configuration', {
            'fields': ('serial_port', 'baud_rate'),
            'classes': ('collapse',)
        }),
        ('Authentication', {
            'fields': ('username', 'password', 'api_key'),
            'classes': ('collapse',)
        }),
        ('Advanced Configuration', {
            'fields': ('configuration', 'sync_interval', 'last_sync', 'last_error'),
            'classes': ('collapse',)
        }),
    )
    
    def get_connection_display(self, obj):
        """Display connection string"""
        return obj.get_connection_string()
    get_connection_display.short_description = 'Connection'

@admin.register(EmployeeScreenshot)
class EmployeeScreenshotAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'captured_at', 'is_active']
    list_filter = ['date', 'captured_at', 'is_active', 'employee__department']
    search_fields = ['employee__user__username', 'employee__user__first_name', 'employee__user__last_name']
    date_hierarchy = 'captured_at'
    readonly_fields = ['captured_at']
    list_editable = ['is_active']


# Multi-Tenant Company and Feature Management
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Super Admin interface for managing companies"""
    list_display = ['name', 'slug', 'admin', 'is_active', 'created_at', 'feature_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['feature_list']
    list_editable = ['is_active']  # Allow quick activation/deactivation
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        ('Company Admin', {
            'fields': ('admin',),
            'description': 'Select a user to be the Company Admin for this company. This user will be able to manage employees and access features assigned to this company.'
        }),
        ('Features', {
            'fields': ('feature_list',),
            'description': 'To assign features to this company, go to the Feature admin page and edit each feature to add this company. Or use the Feature admin page to manage company-feature relationships.'
        }),
    )
    
    def feature_count(self, obj):
        """Display number of features assigned"""
        return obj.features.count()
    feature_count.short_description = 'Features'
    
    def feature_list(self, obj):
        """Display list of features assigned to this company"""
        from django.utils.html import format_html
        if obj.pk:
            features = obj.features.all()
            if features:
                feature_links = []
                for f in features:
                    feature_links.append(f'<a href="/admin/core/feature/{f.id}/change/">{f.name}</a>')
                return format_html(', '.join(feature_links))
            return format_html('No features assigned. <a href="/admin/core/feature/">Go to Features</a> to assign features to this company.')
        return 'Save the company first, then assign features from the Feature admin page.'
    feature_list.short_description = 'Assigned Features'
    
    def get_queryset(self, request):
        """Super Admin sees all companies"""
        return super().get_queryset(request).prefetch_related('features')
    
    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    """Super Admin interface for managing features"""
    list_display = ['name', 'code', 'is_active', 'company_count', 'company_list']
    list_filter = ['is_active', 'code']
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ['companies']  # For many-to-many companies
    list_editable = ['is_active']  # Allow quick activation/deactivation
    fieldsets = (
        ('Feature Information', {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Companies', {
            'fields': ('companies',),
            'description': 'Select which companies have access to this feature. Use Ctrl/Cmd to select multiple companies.'
        }),
    )
    
    def company_count(self, obj):
        """Display number of companies with access"""
        return obj.companies.count()
    company_count.short_description = 'Companies'
    
    def company_list(self, obj):
        """Display list of companies with access"""
        from django.utils.html import format_html
        if obj.pk:
            companies = obj.companies.all()
            if companies:
                company_links = []
                for c in companies:
                    company_links.append(f'<a href="/admin/core/company/{c.id}/change/">{c.name}</a>')
                return format_html(', '.join(company_links))
            return 'No companies assigned'
        return '-'
    company_list.short_description = 'Companies with Access'
    
    def get_queryset(self, request):
        """Super Admin sees all features"""
        return super().get_queryset(request).prefetch_related('companies')
    
    class Meta:
        verbose_name = 'Feature'
        verbose_name_plural = 'Features'


# Extend User Admin to show company profile
class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Company Profile'
    fields = ('company', 'is_company_admin')
    fk_name = 'user'
    extra = 0
    max_num = 1


class UserAdmin(BaseUserAdmin):
    """Extended User Admin with company profile"""
    inlines = (UserProfileInline,)
    
    def save_formset(self, request, form, formset, change):
        """Handle UserProfile inline saving to avoid duplicates"""
        if formset.model == UserProfile:
            # Check if UserProfile already exists (created by signal)
            existing_profile = None
            try:
                existing_profile = UserProfile.objects.get(user=form.instance)
            except UserProfile.DoesNotExist:
                pass
            
            instances = formset.save(commit=False)
            for instance in instances:
                # Ensure UserProfile is linked to the user
                if not instance.user_id:
                    instance.user = form.instance
                
                if existing_profile:
                    # Update existing profile instead of creating new one
                    existing_profile.company = instance.company
                    existing_profile.is_company_admin = instance.is_company_admin
                    existing_profile.save()
                else:
                    # Use get_or_create to avoid IntegrityError (race condition protection)
                    profile, created = UserProfile.objects.get_or_create(
                        user=form.instance,
                        defaults={
                            'company': instance.company,
                            'is_company_admin': instance.is_company_admin
                        }
                    )
                    if not created:
                        # Update existing profile (in case it was created between check and create)
                        profile.company = instance.company
                        profile.is_company_admin = instance.is_company_admin
                        profile.save()
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)


# Unregister default User admin and register extended version
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
