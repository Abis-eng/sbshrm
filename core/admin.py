from .models import Department, Employee, Designation, Holiday, Leave, BudgetCategory, Budget, BudgetExpense, BudgetRevenue, Asset, CompanySettings, LocalizationSettings, InvoiceSettings, SalarySettings, ThemeSettings, Tax, Expense, Estimate, EstimateItem, Invoice, InvoiceItem, Attendance, AttendanceLog, AttendanceMachine
from django.contrib import admin

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
