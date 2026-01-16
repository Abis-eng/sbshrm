from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib import messages
from .company_utils import require_feature, require_company_admin, filter_by_company, get_user_company, is_super_admin, is_company_admin, has_feature_access, get_company_context
from .models import Employee, Department, Designation, Attendance, AttendanceLog, AttendanceMachine, Ticket, Client, Holiday, Leave, Notice, EmployeeScreenshot
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from core.models import ChatMessage, Notification
from django.db.models import Q, Max, Min
from .models import OnlineUser
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from django.db.models import Count
import json
from .models import PayrollItem, Payslip, Employee
from .models import TaxSlab, Loan
from .models import AdvanceRequest
from django import forms
from django.db.models import Sum
from .forms import ClientForm, UserAdminForm, ProjectForm, NoticeForm
from django.forms import ModelForm
from .models import Project, Department
from .forms import TaskForm
from .models import Task
from django.urls import reverse
from django.http import HttpResponseForbidden
from .models import BudgetCategory
from .forms import BudgetCategoryForm
from .forms import BudgetForm
from .models import Budget
from .forms import BudgetExpenseForm
from .models import BudgetExpense
from .forms import BudgetRevenueForm
from .models import BudgetRevenue
from .forms import AssetForm
from .models import Asset
from .forms import CompanySettingsForm
from .models import CompanySettings
from .forms import LocalizationSettingsForm
from .models import LocalizationSettings
from .forms import InvoiceSettingsForm
from .models import InvoiceSettings
from .forms import SalarySettingsForm
from .models import SalarySettings
from .forms import ThemeSettingsForm
from .models import ThemeSettings
from .forms import TaxForm
from .models import Tax
from .forms import ExpenseForm
from .models import Expense
from django.forms import inlineformset_factory
from .models import Estimate, EstimateItem
from .forms import EstimateForm, EstimateItemForm
from .forms import InvoiceForm, InvoiceItemForm, EmployeeMachineForm, ManualAttendanceForm, AttendanceMachineForm, AttendanceFilterForm
from .forms import PayrollItemForm, PayslipCreateForm, PayslipEditForm, TaxSlabForm, LoanForm, AdvanceRequestForm, AdvanceReviewForm, MonthlyPayrollForm, PayslipRegisterEditForm
from .models import Invoice, InvoiceItem, Notification
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .zkt_service import zkt_service
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate
from .models import CompanySettings
import logging

logger = logging.getLogger(__name__)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Explicitly check if user is active
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Please contact the administrator.')
                return render(request, 'core/login.html')
            login(request, user)
            # Redirect based on user type
            if user.is_superuser:
                return redirect('dashboard')  # Admin goes to admin dashboard
            else:
                return redirect('employee_dashboard')  # Employee goes to employee dashboard
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')

def is_admin(user):
    return user.is_superuser

def is_employee(user):
    return user.is_authenticated and not user.is_superuser

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    from django.db.models import Count, Sum, Q
    from django.db.models.functions import TruncMonth
    from django.utils import timezone
    from datetime import timedelta
    
    attendance_stats = Attendance.objects.values('status').annotate(count=Count('id'))
    dept_counts = Department.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    desig_counts = Designation.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    salary_stats = None
    try:
        salary_stats = Employee.objects.values('department__name').annotate(total_salary=Sum('salary'))
    except Exception:
        pass
    total_employees = Employee.objects.count()
    total_departments = Department.objects.count()
    total_projects = Project.objects.count()
    total_tickets = Ticket.objects.count()
    total_clients = Client.objects.count()
    
    # Additional stats
    open_tickets = Ticket.objects.filter(status__in=['open', 'new', 'in_progress']).count()
    pending_leaves = Leave.objects.filter(status='pending').count()
    pending_advances = AdvanceRequest.objects.filter(status='pending').count()
    try:
        active_projects = Project.objects.filter(status='active').count()
    except:
        active_projects = total_projects
    
    # Today's attendance
    today = timezone.now().date()
    today_present = Attendance.objects.filter(date=today, status='present').count()
    today_absent = Attendance.objects.filter(date=today, status='absent').count()
    today_late = Attendance.objects.filter(date=today, status='late').count()
    
    # Recent activities
    recent_tickets = Ticket.objects.order_by('-created_at')[:5]
    recent_leaves = Leave.objects.order_by('-applied_at')[:5]
    
    # Calculate trends (comparing with last month)
    last_month = timezone.now() - timedelta(days=30)
    employees_last_month = Employee.objects.filter(date_of_joining__lt=last_month).count()
    employees_trend = total_employees - employees_last_month if employees_last_month > 0 else 0
    
    # Active tasks
    active_tasks = Task.objects.filter(status__in=['pending', 'in_progress']).count()
    completed_tasks = Task.objects.filter(status='completed').count()
    
    # Total salary
    total_salary = Employee.objects.aggregate(total=Sum('salary'))['total'] or 0
    
    # Expenses by month
    expense_stats = (
        BudgetExpense.objects.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    # Revenues by month
    revenue_stats = (
        BudgetRevenue.objects.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    
    # Monthly totals
    current_month_expenses = BudgetExpense.objects.filter(
        date__year=timezone.now().year,
        date__month=timezone.now().month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    current_month_revenue = BudgetRevenue.objects.filter(
        date__year=timezone.now().year,
        date__month=timezone.now().month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'core/dashboard.html', {
        'attendance_stats': list(attendance_stats),
        'dept_counts': list(dept_counts),
        'desig_counts': list(desig_counts),
        'salary_stats': list(salary_stats) if salary_stats else None,
        'total_employees': total_employees,
        'total_departments': total_departments,
        'total_projects': total_projects,
        'total_tickets': total_tickets,
        'total_clients': total_clients,
        'open_tickets': open_tickets,
        'pending_leaves': pending_leaves,
        'pending_advances': pending_advances,
        'active_projects': active_projects,
        'today_present': today_present,
        'today_absent': today_absent,
        'today_late': today_late,
        'recent_tickets': recent_tickets,
        'recent_leaves': recent_leaves,
        'expense_stats': list(expense_stats),
        'revenue_stats': list(revenue_stats),
        'current_month_expenses': current_month_expenses,
        'current_month_revenue': current_month_revenue,
        'employees_trend': employees_trend,
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'total_salary': total_salary,
    })

@login_required
@require_feature('employees')
def employee_list(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    from django.db.models import Q
    from .company_utils import filter_by_company, is_super_admin, get_user_company
    
    # Check for export format
    export_format = request.GET.get('format', '')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    dept_filter = request.GET.get('department', '')
    desig_filter = request.GET.get('designation', '')
    
    # Get user's company
    user_company = get_user_company(request.user)
    
    if is_super_admin(request.user):
        # Super Admin sees all employees
        employees = Employee.objects.select_related('user', 'department', 'designation', 'company').all()
        departments = Department.objects.all()
        designations = Designation.objects.all()
    elif user_company:
        # Company Admin and Employees see only their company's data
        employees = Employee.objects.filter(company=user_company).select_related('user', 'department', 'designation', 'company')
        departments = Department.objects.filter(company=user_company)
        designations = Designation.objects.filter(company=user_company)
        
        # Regular employees can only see their own information
        if not (is_company_admin(request.user) or request.user.is_staff):
            try:
                employee = request.user.employee
                employees = employees.filter(id=employee.id)
            except Exception:
                employees = Employee.objects.none()
    else:
        # No company assigned - no data
        employees = Employee.objects.none()
        departments = Department.objects.none()
        designations = Designation.objects.none()
    
    # Apply filters (for both display and export)
    if search_query:
        employees = employees.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    if dept_filter:
        employees = employees.filter(department__name=dept_filter)
    if desig_filter:
        employees = employees.filter(designation__name=desig_filter)
    
    # Order employees
    employees = employees.order_by('user__first_name', 'user__last_name')
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Username', 'Full Name', 'Email', 'Phone', 'Department', 'Designation', 'Salary', 'Date of Joining', 'Status']
        data = []
        for emp in employees:
            data.append([
                str(emp.id),
                str(emp.user.username) if emp.user.username else 'N/A',
                str(emp.user.get_full_name()) if emp.user.get_full_name() else str(emp.user.username) if emp.user.username else 'N/A',
                str(emp.user.email) if emp.user.email else 'N/A',
                str(emp.phone) if emp.phone else 'N/A',
                str(emp.department.name) if emp.department and emp.department.name else 'N/A',
                str(emp.designation.name) if emp.designation and emp.designation.name else 'N/A',
                f"Rs{float(emp.salary):.2f}" if emp.salary else 'N/A',
                emp.date_of_joining.strftime('%Y-%m-%d') if emp.date_of_joining else 'N/A',
                'Active' if not emp.is_restricted else 'Restricted'
            ])
        
        filename = f"employees_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Employees Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Employees Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Employees Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Employees Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('employee_list')
    
    return render(request, 'core/employee_list.html', {
        'employees': employees, 
        'departments': departments, 
        'designations': designations,
        'search_query': search_query,
        'dept_filter': dept_filter,
        'desig_filter': desig_filter,
    })

@login_required
def view_employee_profile(request, employee_id):
    employee = get_object_or_404(Employee.objects.select_related('user', 'department', 'designation'), id=employee_id)
    # Get related data
    attendance_count = Attendance.objects.filter(employee=employee).count()
    leaves_count = Leave.objects.filter(employee=employee).count()
    advances_count = AdvanceRequest.objects.filter(employee=employee).count()
    # Check if Project and Task models have assigned_to field
    try:
        projects_count = Project.objects.filter(manager=employee).count()
    except:
        projects_count = 0
    try:
        tasks_count = Task.objects.filter(assigned_to=employee.user).count()
    except:
        tasks_count = 0
    
    # Check if current user can edit this profile (own profile or admin)
    can_edit = request.user.is_superuser or (hasattr(request.user, 'employee') and request.user.employee.id == employee.id)
    
    return render(request, 'core/view_employee_profile.html', {
        'employee': employee,
        'attendance_count': attendance_count,
        'leaves_count': leaves_count,
        'projects_count': projects_count,
        'tasks_count': tasks_count,
        'advances_count': advances_count,
        'can_edit': can_edit,
    })

@login_required
def update_my_profile_picture(request):
    """Allow employees to update their own profile picture"""
    try:
        employee = request.user.employee
    except:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_list')
    
    if request.method == 'POST':
        profile_picture = request.FILES.get('profile_picture')
        if profile_picture:
            employee.profile_picture = profile_picture
            employee.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('view_employee_profile', employee_id=employee.id)
        else:
            messages.error(request, 'Please select a picture to upload.')
    
    return render(request, 'core/update_profile_picture.html', {
        'employee': employee,
    })

@user_passes_test(is_admin)
def user_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'users': []})
    if request.user.is_superuser:
        users = User.objects.exclude(id=request.user.id)
    else:
        users = User.objects.filter(is_superuser=False).exclude(id=request.user.id)
    user_data = [
        {
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'initials': (u.first_name[:1] + u.last_name[:1]).upper() if u.first_name or u.last_name else u.username[:2].upper()
        }
        for u in users
    ]
    return JsonResponse({'users': user_data})

@user_passes_test(is_admin)
def add_employee(request):
    departments = Department.objects.all()
    designations = Designation.objects.all()
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        department_id = request.POST.get('department')
        designation_id = request.POST.get('designation')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        if not address:
            address = ''
        city = request.POST.get('city', '').strip()
        email = request.POST.get('email', '').strip()
        date_of_joining = request.POST.get('date_of_joining')
        if not date_of_joining:
            date_of_joining = None
        machine_id = request.POST.get('machine_id')
        fingerprint_id = request.POST.get('fingerprint_id')
        face_id = request.POST.get('face_id')
        card_id = request.POST.get('card_id')
        profile_picture = request.FILES.get('profile_picture')
        
        # Check if username exists and if it's associated with an active employee
        existing_user = User.objects.filter(username=username).first()
        if existing_user:
            # Check if user has an active employee record
            try:
                if hasattr(existing_user, 'employee') and existing_user.employee:
                    error = 'Username already exists and is associated with an active employee. Please choose another username.'
                    existing_cities = Employee.objects.exclude(city__isnull=True).exclude(city='').values_list('city', flat=True).distinct().order_by('city')
                    return render(request, 'core/add_employee.html', {
                        'departments': departments, 
                        'designations': designations, 
                        'error': error,
                        'existing_cities': existing_cities
                    })
            except Employee.DoesNotExist:
                pass  # No employee record, continue with cleanup
            
            # User exists but has no employee record - this is a leftover from deletion
            # Clean it up by deleting the user completely using raw SQL to force deletion
            try:
                from django.db import connection
                from django.db.utils import OperationalError, ProgrammingError
                user_id = existing_user.id
                
                # Use raw SQL to force delete all related records
                with connection.cursor() as cursor:
                    try:
                        cursor.execute("DELETE FROM core_chatmessage WHERE sender_id = %s OR recipient_id = %s", [user_id, user_id])
                    except (OperationalError, ProgrammingError):
                        pass
                    
                    try:
                        # Notification uses recipient_id and sender_id, not user_id
                        cursor.execute("DELETE FROM core_notification WHERE recipient_id = %s OR sender_id = %s", [user_id, user_id])
                    except (OperationalError, ProgrammingError):
                        pass
                    
                    try:
                        cursor.execute("DELETE FROM core_ticket WHERE created_by_id = %s", [user_id])
                    except (OperationalError, ProgrammingError):
                        pass
                    
                    try:
                        cursor.execute("DELETE FROM core_userfamilyinfo WHERE user_id = %s", [user_id])
                    except (OperationalError, ProgrammingError):
                        pass
                    
                    try:
                        cursor.execute("DELETE FROM core_onlineuser WHERE user_id = %s", [user_id])
                    except (OperationalError, ProgrammingError):
                        pass
                    
                    try:
                        cursor.execute("DELETE FROM core_userprofile WHERE user_id = %s", [user_id])
                    except (OperationalError, ProgrammingError):
                        pass
                    
                    # Finally delete the user
                    try:
                        cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])
                        logger.info(f"Cleaned up leftover user account: {username} (ID: {user_id})")
                    except (OperationalError, ProgrammingError) as e:
                        logger.error(f"Failed to delete user {username}: {e}")
                        # Try Django ORM as fallback
                        existing_user.delete()
                        logger.info(f"Cleaned up leftover user account using ORM: {username}")
                
            except Exception as e:
                logger.error(f"Error cleaning up leftover user {username}: {e}")
                # Last resort: try to delete using Django ORM
                try:
                    from .models import UserProfile, ChatMessage, Notification, Ticket, UserFamilyInfo, OnlineUser
                    ChatMessage.objects.filter(sender=existing_user).delete()
                    ChatMessage.objects.filter(recipient=existing_user).delete()
                    Notification.objects.filter(recipient=existing_user).delete()
                    Notification.objects.filter(sender=existing_user).delete()
                    Ticket.objects.filter(created_by=existing_user).delete()
                    UserFamilyInfo.objects.filter(user=existing_user).delete()
                    OnlineUser.objects.filter(user=existing_user).delete()
                    UserProfile.objects.filter(user=existing_user).delete()
                    existing_user.delete()
                    logger.info(f"Cleaned up leftover user account using ORM fallback: {username}")
                except Exception as e2:
                    logger.error(f"Complete cleanup failure for {username}: {e2}")
                    error = f'Username exists but cleanup failed. Error: {str(e2)}. Please try a different username or contact administrator.'
                    existing_cities = Employee.objects.exclude(city__isnull=True).exclude(city='').values_list('city', flat=True).distinct().order_by('city')
                    return render(request, 'core/add_employee.html', {
                        'departments': departments, 
                        'designations': designations, 
                        'error': error,
                        'existing_cities': existing_cities
                    })
        
        user = User.objects.create(
            username=username,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            email=email if email else '',
        )
        # Handle salary field - convert to Decimal if provided
        salary = None
        salary_str = request.POST.get('salary', '').strip()
        if salary_str:
            try:
                from decimal import Decimal
                salary = Decimal(salary_str)
            except (ValueError, TypeError):
                salary = None
        
        employee = Employee.objects.create(
            user=user,
            department_id=department_id,
            designation_id=designation_id,
            salary=salary,
            phone=phone,
            address=address,
            city=city,
            date_of_joining=date_of_joining,
            machine_id=machine_id.strip() if machine_id and machine_id.strip() else None,
            fingerprint_id=fingerprint_id.strip() if fingerprint_id and fingerprint_id.strip() else None,
            face_id=face_id.strip() if face_id and face_id.strip() else None,
            card_id=card_id.strip() if card_id and card_id.strip() else None,
            profile_picture=profile_picture,
        )
        
        # Send welcome email if email is configured
        from .email_utils import send_welcome_email
        email_sent = False
        email_error = None
        if employee.user.email:
            try:
                email_sent = send_welcome_email(employee, username, password)
                if not email_sent:
                    email_error = "Failed to send welcome email. Please check email settings."
            except Exception as e:
                email_error = f"Error sending email: {str(e)}"
        
        return render(request, 'core/employee_created.html', {
            'username': username, 
            'password': password,
            'email_sent': email_sent,
            'email_error': email_error,
            'employee_email': employee.user.email if employee.user.email else None
        })
    # Get all existing cities for autocomplete
    existing_cities = Employee.objects.exclude(city__isnull=True).exclude(city='').values_list('city', flat=True).distinct().order_by('city')
    return render(request, 'core/add_employee.html', {
        'departments': departments, 
        'designations': designations, 
        'error': error,
        'existing_cities': existing_cities
    })

class DepartmentForm(ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']

@user_passes_test(is_admin)
def manage_departments(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    from django.db.models import Count
    
    export_format = request.GET.get('format', '')
    departments = Department.objects.all().order_by('name')
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Name', 'Description', 'Total Employees']
        data = []
        for dept in departments:
            emp_count = Employee.objects.filter(department=dept).count()
            data.append([
                dept.id,
                dept.name,
                dept.description[:100] + '...' if dept.description and len(dept.description) > 100 else (dept.description or 'N/A'),
                emp_count
            ])
        filename = f"departments_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Departments Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Departments Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Departments Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Departments Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('manage_departments')
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_departments')
    else:
        form = DepartmentForm()
    # For graph: employee count per department
    dept_counts = Department.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    return render(request, 'core/manage_departments.html', {'departments': departments, 'form': form, 'dept_counts': list(dept_counts)})

@user_passes_test(is_admin)
def manage_designations(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    from django.db.models import Count
    
    export_format = request.GET.get('format', '')
    designations = Designation.objects.all().order_by('name')
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Name', 'Description', 'Total Employees']
        data = []
        for desg in designations:
            emp_count = Employee.objects.filter(designation=desg).count()
            data.append([
                desg.id,
                desg.name,
                desg.description[:100] + '...' if desg.description and len(desg.description) > 100 else (desg.description or 'N/A'),
                emp_count
            ])
        filename = f"designations_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Designations Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Designations Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Designations Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Designations Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('manage_designations')
    
    if request.method == 'POST':
        form = DesignationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_designations')
    else:
        form = DesignationForm()
    # For graph: employee count per designation
    desig_counts = Designation.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    return render(request, 'core/manage_designations.html', {'designations': designations, 'form': form, 'desig_counts': list(desig_counts)})

class DesignationForm(ModelForm):
    class Meta:
        model = Designation
        fields = ['name', 'description']

@user_passes_test(is_admin)
def delete_department(request, department_id):
    Department.objects.filter(id=department_id).delete()
    return redirect('manage_departments')

@user_passes_test(is_admin)
def delete_designation(request, designation_id):
    Designation.objects.filter(id=designation_id).delete()
    return redirect('manage_designations')

@user_passes_test(is_admin)
def edit_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f'Department "{department.name}" updated successfully!')
            return redirect('manage_departments')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'core/edit_department.html', {'form': form, 'department': department})

@user_passes_test(is_admin)
def edit_designation(request, designation_id):
    designation = get_object_or_404(Designation, id=designation_id)
    if request.method == 'POST':
        form = DesignationForm(request.POST, instance=designation)
        if form.is_valid():
            form.save()
            messages.success(request, f'Designation "{designation.name}" updated successfully!')
            return redirect('manage_designations')
    else:
        form = DesignationForm(instance=designation)
    return render(request, 'core/edit_designation.html', {'form': form, 'designation': designation})

@user_passes_test(is_admin)
def edit_holiday(request, holiday_id):
    holiday = get_object_or_404(Holiday, id=holiday_id)
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=holiday)
        if form.is_valid():
            form.save()
            messages.success(request, f'Holiday "{holiday.name}" updated successfully!')
            return redirect('manage_holidays')
    else:
        form = HolidayForm(instance=holiday)
    return render(request, 'core/edit_holiday.html', {'form': form, 'holiday': holiday})

@login_required
def department_employees(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    employees = Employee.objects.filter(department=department).select_related('user', 'designation')
    return render(request, 'core/department_employees.html', {
        'department': department,
        'employees': employees
    })

@login_required
def designation_employees(request, designation_id):
    designation = get_object_or_404(Designation, id=designation_id)
    employees = Employee.objects.filter(designation=designation).select_related('user', 'department')
    return render(request, 'core/designation_employees.html', {
        'designation': designation,
        'employees': employees
    })

@login_required
def my_department(request):
    try:
        employee = request.user.employee
        if not employee.can_view_department:
            return HttpResponse('You are restricted from accessing department.', status=403)
        department = employee.department
    except Exception:
        department = None
    # Get all departments with employee counts for graph
    from django.db.models import Count
    dept_counts = Department.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    total_employees = Employee.objects.count()
    return render(request, 'core/my_department.html', {
        'department': department,
        'dept_counts': list(dept_counts),
        'total_employees': total_employees
    })

@login_required
def my_designation(request):
    try:
        employee = request.user.employee
        if not employee.can_view_designation:
            return HttpResponse('You are restricted from accessing designation.', status=403)
        designation = employee.designation
    except Exception:
        designation = None
    # Get all designations with employee counts for graph
    from django.db.models import Count
    desig_counts = Designation.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    total_employees = Employee.objects.count()
    return render(request, 'core/my_designation.html', {
        'designation': designation,
        'desig_counts': list(desig_counts),
        'total_employees': total_employees
    })

@login_required
def employee_dashboard(request):
    from django.db.models import Count, Sum
    # Attendance stats for graph
    try:
        employee = request.user.employee
        attendance_stats = Attendance.objects.filter(employee=employee).values('status').annotate(count=Count('id'))
    except Exception:
        # If user doesn't have an employee record, return empty stats
        attendance_stats = []
    
    # Department bar chart: all departments and their employee counts
    dept_counts = Department.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    desig_counts = Designation.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    
    # Get active notices for notice board
    notices = Notice.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Salary graph: Payroll and Payslip stats will be added here
    return render(request, 'core/employee_dashboard.html', {
        'attendance_stats': list(attendance_stats),
        'dept_counts': list(dept_counts),
        'desig_counts': list(desig_counts),
        'notices': notices,
        # 'payroll_stats': ...
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def chat_user_list(request):
    """Get list of all users for chat (everyone can see everyone, including admin)"""
    user = request.user
    # Show all users except the current user (including admin)
    users = User.objects.exclude(id=user.id).order_by('username')
    online_ids = set(OnlineUser.objects.values_list('user_id', flat=True))
    user_data = []
    for u in users:
        # Get last message between current user and this user
        last_msg = ChatMessage.objects.filter(
            (Q(sender=user, recipient=u) | Q(sender=u, recipient=user))
        ).order_by('-timestamp').first()
        
        # Get employee profile picture if exists
        profile_picture_url = None
        try:
            employee = Employee.objects.get(user=u)
            if employee.profile_picture:
                profile_picture_url = employee.profile_picture.url
        except Employee.DoesNotExist:
            pass
        
        user_data.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'initials': (u.first_name[:1] + u.last_name[:1]).upper() if u.first_name or u.last_name else u.username[:2].upper(),
            'profile_picture_url': profile_picture_url,
            'last_message': last_msg.content if last_msg else '',
            'last_timestamp': last_msg.timestamp.strftime('%Y-%m-%d %H:%M') if last_msg else '',
            'online': u.id in online_ids,
        })
    return JsonResponse({'users': user_data})

@login_required
@require_POST
def send_chat_message(request):
    """API endpoint to send a chat message"""
    try:
        # Try to parse JSON body, fallback to POST data
        if request.content_type == 'application/json' and request.body:
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST
        recipient_username = data.get('recipient')
        message_content = data.get('message', '').strip()
        
        if not recipient_username:
            return JsonResponse({'error': 'Recipient is required'}, status=400)
        
        if not message_content:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        try:
            recipient = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Recipient not found'}, status=404)
        
        # Create message
        message = ChatMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            content=message_content,
            timestamp=timezone.now()
        )
        
        # Verify message was created
        if not message.id:
            return JsonResponse({'error': 'Failed to save message'}, status=500)
        
        # Create notification
        sender_name = request.user.get_full_name() or request.user.username
        Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            notification_type='message',
            title=f'New message from {sender_name}',
            message=message_content[:100] + ('...' if len(message_content) > 100 else ''),
            link=f'?chat_user={request.user.username}',
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'user': message.sender.username,
                'message': message.content,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_chat_messages(request, recipient_username):
    """API endpoint to get chat messages with a specific user"""
    try:
        # Get recipient user (case-insensitive lookup)
        try:
            recipient = User.objects.get(username__iexact=recipient_username)
        except User.DoesNotExist:
            return JsonResponse({'error': f'Recipient "{recipient_username}" not found'}, status=404)
        except User.MultipleObjectsReturned:
            recipient = User.objects.filter(username__iexact=recipient_username).first()
        
        # Get all messages between current user and recipient (bidirectional)
        # This includes:
        # 1. Messages sent BY current user TO recipient
        # 2. Messages sent BY recipient TO current user
        messages = ChatMessage.objects.filter(
            Q(sender=request.user, recipient=recipient) | Q(sender=recipient, recipient=request.user)
        ).exclude(recipient__isnull=True).order_by('timestamp')
        
        # Debug info
        total_count = messages.count()
        
        messages_data = [
            {
                'id': msg.id,
                'user': msg.sender.username,
                'message': msg.content,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for msg in messages
        ]
        
        return JsonResponse({
            'messages': messages_data, 
            'count': len(messages_data),
            'success': True
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e), 
            'success': False
        }, status=500)

@login_required
def get_new_messages(request):
    """API endpoint to get new messages since a given timestamp"""
    try:
        last_timestamp = request.GET.get('last_timestamp')
        recipient_username = request.GET.get('recipient')
        
        if not recipient_username:
            return JsonResponse({'error': 'Recipient is required'}, status=400)
        
        recipient = User.objects.get(username=recipient_username)
        
        # Get messages sent TO current user FROM recipient (new messages)
        query = Q(sender=recipient, recipient=request.user)
        if last_timestamp:
            try:
                from datetime import datetime
                last_dt = datetime.strptime(last_timestamp, '%Y-%m-%d %H:%M:%S')
                query &= Q(timestamp__gt=last_dt)
            except:
                pass
        
        messages = ChatMessage.objects.filter(query).order_by('timestamp')
        
        messages_data = [
            {
                'id': msg.id,
                'user': msg.sender.username,
                'message': msg.content,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for msg in messages
        ]
        
        return JsonResponse({
            'messages': messages_data,
            'success': True
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'Recipient not found'}, status=404)
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

@login_required
def my_tickets(request):
    """View user's own tickets"""
    from django.db.models import Q, Count
    
    if request.user.is_superuser:
        tickets = Ticket.objects.all()
    else:
        tickets = Ticket.objects.filter(
            Q(created_by=request.user) | Q(assigned_to=request.user)
        )
    
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'sent':
        tickets = tickets.filter(created_by=request.user)
    elif filter_type == 'received':
        tickets = tickets.filter(assigned_to=request.user)
    
    tickets = tickets.select_related('created_by', 'assigned_to').annotate(
        reply_count=Count('replies')
    ).order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(tk_id__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if request.user.is_superuser:
        base_stats = Ticket.objects.all()
    else:
        base_stats = Ticket.objects.filter(Q(created_by=request.user) | Q(assigned_to=request.user))
    
    stats = {
        'total': base_stats.count(),
        'new': base_stats.filter(status='new').count(),
        'open': base_stats.filter(status='open').count(),
        'in_progress': base_stats.filter(status='in_progress').count(),
        'closed': base_stats.filter(status='closed').count(),
        'sent': Ticket.objects.filter(created_by=request.user).count(),
        'received': Ticket.objects.filter(assigned_to=request.user).count(),
    }
    
    return render(request, 'core/my_tickets.html', {
        'tickets': tickets,
        'stats': stats,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'filter_type': filter_type,
    })

@login_required
def my_advances(request):
    try:
        employee = request.user.employee
    except Exception:
        return HttpResponse('Not an employee', status=403)
    advances = AdvanceRequest.objects.filter(employee=employee).order_by('-requested_at')
    
    # Calculate statistics
    total_count = advances.count()
    approved_count = advances.filter(status='approved').count()
    pending_count = advances.filter(status='pending').count()
    
    # Calculate monthly payments for each advance
    advances_with_monthly = []
    for adv in advances:
        monthly_payment = None
        if adv.desired_installments and adv.desired_installments > 0:
            monthly_payment = float(adv.amount) / adv.desired_installments
        advances_with_monthly.append({
            'advance': adv,
            'monthly_payment': monthly_payment
        })
    
    if request.method == 'POST':
        form = AdvanceRequestForm(request.POST)
        if form.is_valid():
            advance = form.save(commit=False)
            advance.employee = employee
            advance.save()
            # Create notification for admin
            admin_users = User.objects.filter(is_superuser=True)
            for admin in admin_users:
                create_notification(
                    recipient=admin,
                    sender=request.user,
                    notification_type='system',
                    title=f'Advance request from {employee.user.get_full_name() or employee.user.username}',
                    message=f'Amount: {advance.amount}, Reason: {advance.reason[:100]}',
                    link=f'/manage-advances/'
                )
            messages.success(request, 'Advance request submitted successfully!')
            return redirect('my_advances')
    else:
        form = AdvanceRequestForm()
    return render(request, 'core/my_advances.html', {
        'advances': advances,
        'advances_with_monthly': advances_with_monthly,
        'form': form,
        'total_count': total_count,
        'approved_count': approved_count,
        'pending_count': pending_count,
    })

@user_passes_test(is_admin)
def manage_advances(request):
    advances = AdvanceRequest.objects.select_related('employee__user', 'employee__department', 'reviewed_by').order_by('-requested_at')
    # Filter by employee if provided
    employee_id = request.GET.get('employee')
    if employee_id:
        advances = advances.filter(employee_id=employee_id)
    
    # Calculate statistics
    total_count = advances.count()
    pending_count = advances.filter(status='pending').count()
    approved_count = advances.filter(status='approved').count()
    rejected_count = advances.filter(status='rejected').count()
    
    # Calculate monthly payments for each advance
    advances_with_monthly = []
    for adv in advances:
        monthly_payment = None
        if adv.desired_installments and adv.desired_installments > 0:
            monthly_payment = float(adv.amount) / adv.desired_installments
        advances_with_monthly.append({
            'advance': adv,
            'monthly_payment': monthly_payment
        })
    
    if request.method == 'POST':
        advance_id = request.POST.get('advance_id')
        action = request.POST.get('action')
        admin_comment = request.POST.get('admin_comment', '')
        adv = get_object_or_404(AdvanceRequest, id=advance_id)
        if action == 'approve':
            adv.status = AdvanceRequest.STATUS_APPROVED
            # Get approved amount from admin (default to requested amount if not provided)
            approved_amount_str = request.POST.get('approved_amount')
            if approved_amount_str:
                try:
                    approved_amount = float(approved_amount_str)
                except (ValueError, TypeError):
                    approved_amount = float(adv.amount)
            else:
                approved_amount = float(adv.amount)
            
            # Get and save installments
            installments_str = request.POST.get('desired_installments')
            if installments_str:
                try:
                    installments = int(installments_str)
                except (ValueError, TypeError):
                    installments = adv.desired_installments or 1
            else:
                installments = adv.desired_installments or 1
            
            adv.desired_installments = installments
            adv.save()
            
            # Create a Loan record with approved amount
            monthly_installment = approved_amount / max(1, installments)
            Loan.objects.create(
                employee=adv.employee,
                principal_amount=approved_amount,
                monthly_installment=monthly_installment,
                balance=approved_amount,
                start_date=timezone.now().date(),
                is_active=True,
            )
            # Create notification for employee
            if approved_amount != float(adv.amount):
                create_notification(
                    recipient=adv.employee.user,
                    sender=request.user,
                    notification_type='system',
                    title='Advance request approved',
                    message=f'Your advance request of Rs{adv.amount} has been approved for Rs{approved_amount:.2f}.',
                    link=f'/my-advances/'
                )
            else:
                create_notification(
                    recipient=adv.employee.user,
                    sender=request.user,
                    notification_type='system',
                    title='Advance request approved',
                    message=f'Your advance request of Rs{adv.amount} has been approved.',
                    link=f'/my-advances/'
                )
        elif action == 'reject':
            adv.status = AdvanceRequest.STATUS_REJECTED
            # Create notification for employee
            create_notification(
                recipient=adv.employee.user,
                sender=request.user,
                notification_type='system',
                title='Advance request rejected',
                message=f'Your advance request of {adv.amount} has been rejected. {admin_comment[:100]}',
                link=f'/my-advances/'
            )
        adv.reviewed_by = request.user
        adv.reviewed_at = timezone.now()
        adv.admin_comment = admin_comment
        adv.save()
        messages.success(request, f'Advance request {action}d successfully!')
        return redirect('manage_advances')
    return render(request, 'core/manage_advances.html', {
        'advances': advances,
        'advances_with_monthly': advances_with_monthly,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })

@login_required
def submit_ticket(request):
    """Submit a new ticket"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'medium')
        assigned_to_id = request.POST.get('assigned_to', '').strip()
        end_date_str = request.POST.get('end_date', '').strip()
        
        if not title or not description or not assigned_to_id:
            messages.error(request, 'Title, description, and recipient are required.')
            return redirect('submit_ticket')
        
        try:
            assigned_to = User.objects.get(id=assigned_to_id)
        except (User.DoesNotExist, ValueError):
            messages.error(request, 'Selected recipient not found.')
            return redirect('submit_ticket')
        
        end_date = None
        if end_date_str:
            try:
                from datetime import datetime
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date)
            except:
                pass
        
        related_task = None
        if request.user.is_superuser:
            related_task_id = request.POST.get('related_task', '').strip()
            if related_task_id:
                try:
                    from .models import Task
                    related_task = Task.objects.get(id=related_task_id)
                except:
                    pass
        
        ticket = Ticket.objects.create(
            title=title,
            subject=subject,
            description=description,
            priority=priority,
            created_by=request.user,
            assigned_to=assigned_to,
            related_task=related_task,
            end_date=end_date,
            status='new'
        )
        
        from .models import TicketFile
        if request.FILES.getlist('attachments'):
            for file in request.FILES.getlist('attachments'):
                try:
                    TicketFile.objects.create(
                        ticket=ticket,
                        file=file,
                        file_name=file.name,
                        file_size=file.size,
                        uploaded_by=request.user
                    )
                except:
                    pass
        
        try:
            create_notification(
                recipient=assigned_to,
                sender=request.user,
                notification_type='ticket',
                title=f'New ticket: {ticket.tk_id} - {title}',
                message=description[:200],
                link=f'/ticket/{ticket.id}/'
            )
        except:
            pass
        
        messages.success(request, f'Ticket {ticket.tk_id} created successfully!')
        # Redirect to all tickets if admin, otherwise my tickets
        if request.user.is_superuser:
            return redirect('all_tickets')
        else:
            return redirect('my_tickets')
    
    if request.user.is_superuser:
        employees = User.objects.filter(is_superuser=False, employee__isnull=False).select_related('employee')
        admins = []
        from .models import Task
        tasks = Task.objects.select_related('project', 'assigned_to').all().order_by('-created_at')[:100]
    else:
        employees = []
        admins = User.objects.filter(is_superuser=True)
        tasks = []
    
    return render(request, 'core/submit_ticket.html', {
        'employees': employees,
        'admins': admins,
        'tasks': tasks,
    })

@user_passes_test(is_admin)
def all_tickets(request):
    """View all tickets (admin only)"""
    from django.db.models import Q, Count
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    tickets = Ticket.objects.select_related('created_by', 'assigned_to').annotate(
        reply_count=Count('replies')
    ).order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(tk_id__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(created_by__username__icontains=search_query)
        )
    
    export_format = request.GET.get('format', '')
    if export_format:
        headers = ['Ticket ID', 'Title', 'Created By', 'Assigned To', 'Status', 'Priority', 'Created Date']
        data = []
        for ticket in tickets:
            data.append([
                ticket.tk_id,
                ticket.title,
                ticket.created_by.get_full_name() or ticket.created_by.username,
                ticket.assigned_to.get_full_name() if ticket.assigned_to else 'Unassigned',
                ticket.get_status_display(),
                ticket.get_priority_display(),
                ticket.created_at.strftime('%Y-%m-%d %H:%M'),
            ])
        filename = f"tickets_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Tickets Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Tickets Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Tickets Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Tickets Report', headers, filename)
        except:
            messages.error(request, 'Export error occurred.')
            return redirect('all_tickets')
    
    stats = {
        'total': Ticket.objects.count(),
        'new': Ticket.objects.filter(status='new').count(),
        'open': Ticket.objects.filter(status='open').count(),
        'in_progress': Ticket.objects.filter(status='in_progress').count(),
        'closed': Ticket.objects.filter(status='closed').count(),
        'high_priority': Ticket.objects.filter(priority='high', status__in=['new', 'open', 'in_progress']).count(),
    }
    
    return render(request, 'core/all_tickets.html', {
        'tickets': tickets,
        'stats': stats,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
    })

@login_required
def ticket_detail(request, ticket_id):
    """View ticket details with comprehensive error handling"""
    from django.http import HttpResponse
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        ticket = get_object_or_404(Ticket, id=ticket_id)
        
        if not request.user.is_superuser:
            if ticket.created_by != request.user and ticket.assigned_to != request.user:
                messages.error(request, 'You do not have permission to view this ticket.')
                return redirect('my_tickets')
        
        from .models import TicketReply, TicketFile
        replies = []
        files = []
        employees = []
        
        try:
            # Get all replies for this ticket - ensure they persist
            replies = list(TicketReply.objects.filter(ticket=ticket).select_related('created_by', 'ticket').order_by('created_at'))
        except Exception as e:
            logger.warning(f"Error loading replies: {str(e)}")
            replies = []
        
        try:
            files = list(TicketFile.objects.filter(ticket=ticket).select_related('uploaded_by'))
        except Exception as e:
            logger.warning(f"Error loading files: {str(e)}")
            files = []
        
        try:
            employees = list(User.objects.filter(is_superuser=False, employee__isnull=False).select_related('employee'))
        except Exception as e:
            logger.warning(f"Error loading employees: {str(e)}")
            employees = []
        
        if request.method == 'POST':
            try:
                action = request.POST.get('action')
                
                if action == 'reply':
                    message = request.POST.get('message', '').strip()
                    if message:
                        reply = TicketReply.objects.create(
                            ticket=ticket,
                            message=message,
                            created_by=request.user
                        )
                        from .models import TicketReplyFile
                        if request.FILES.getlist('attachments'):
                            for file in request.FILES.getlist('attachments'):
                                try:
                                    TicketReplyFile.objects.create(
                                        ticket_reply=reply,
                                        file=file,
                                        file_name=file.name,
                                        file_size=file.size,
                                        uploaded_by=request.user
                                    )
                                except Exception as e:
                                    logger.error(f"Error saving attachment {file.name}: {str(e)}")
                        messages.success(request, 'Reply added successfully!')
                    else:
                        messages.error(request, 'Message cannot be empty.')
                
                elif action == 'update_status' and request.user.is_superuser:
                    ticket.status = request.POST.get('status')
                    ticket.save()
                    messages.success(request, 'Ticket status updated!')
                
                elif action == 'assign' and request.user.is_superuser:
                    assigned_user_id = request.POST.get('assigned_to')
                    if assigned_user_id:
                        ticket.assigned_to_id = assigned_user_id
                        ticket.save()
                        messages.success(request, 'Ticket assigned successfully!')
                
                elif action == 'update_priority' and request.user.is_superuser:
                    ticket.priority = request.POST.get('priority')
                    ticket.save()
                    messages.success(request, 'Ticket priority updated!')
                
                elif action == 'update_progress':
                    progress = request.POST.get('progress_percentage')
                    if progress:
                        try:
                            ticket.progress_percentage = int(progress)
                            if ticket.progress_percentage == 100 and request.POST.get('lock_progress') == 'true':
                                ticket.progress_locked = True
                            ticket.save()
                            messages.success(request, 'Progress updated successfully!')
                        except (ValueError, TypeError):
                            messages.error(request, 'Invalid progress value.')
                
                elif action == 'unlock_progress' and request.user.is_superuser:
                    ticket.progress_locked = False
                    ticket.save()
                    messages.success(request, 'Progress unlocked!')
                
                return redirect('ticket_detail', ticket_id=ticket.id)
            except Exception as e:
                logger.error(f"Error processing POST request: {str(e)}\n{traceback.format_exc()}")
                messages.error(request, f'An error occurred: {str(e)}')
                return redirect('ticket_detail', ticket_id=ticket.id)
        
        try:
            ticket.replies.filter(is_read=False).exclude(created_by=request.user).update(is_read=True)
        except Exception as e:
            logger.warning(f"Error updating read status: {str(e)}")
        
        # Determine if user can update progress
        can_update_progress = False
        if ticket.related_task:
            if request.user.is_superuser:
                can_update_progress = True
            elif ticket.assigned_to == request.user and not ticket.progress_locked:
                can_update_progress = True
        
        return render(request, 'core/ticket_detail.html', {
            'ticket': ticket,
            'replies': replies,
            'files': files,
            'employees': employees,
            'can_update_progress': can_update_progress,
        })
    except Exception as e:
        logger.error(f"CRITICAL: Error in ticket_detail view: {str(e)}\n{traceback.format_exc()}")
        return HttpResponse(f"<html><body><h1>Error Loading Ticket</h1><p>An unexpected error occurred: {str(e)}</p><p><a href='/my-tickets/'>Go back to tickets</a></p></body></html>", status=500)

@user_passes_test(is_admin)
def edit_ticket(request, ticket_id):
    """Edit ticket (admin only)"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    employees = User.objects.filter(is_superuser=False, employee__isnull=False).select_related('employee')
    from .models import Task
    tasks = Task.objects.select_related('project', 'assigned_to').all().order_by('-created_at')[:100]
    
    if request.method == 'POST':
        ticket.title = request.POST.get('title', ticket.title)
        ticket.subject = request.POST.get('subject', ticket.subject)
        ticket.description = request.POST.get('description', ticket.description)
        ticket.status = request.POST.get('status', ticket.status)
        ticket.priority = request.POST.get('priority', ticket.priority)
        
        if request.POST.get('assigned_to'):
            ticket.assigned_to_id = request.POST.get('assigned_to')
        else:
            ticket.assigned_to = None
        
        related_task_id = request.POST.get('related_task', '')
        if related_task_id:
            try:
                ticket.related_task = Task.objects.get(id=related_task_id)
            except:
                ticket.related_task = None
        else:
            ticket.related_task = None
        
        end_date_str = request.POST.get('end_date', '')
        if end_date_str:
            try:
                from datetime import datetime
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                ticket.end_date = timezone.make_aware(end_date)
            except:
                pass
        else:
            ticket.end_date = None
        
        ticket.save()
        
        from .models import TicketFile
        if request.FILES.getlist('attachments'):
            for file in request.FILES.getlist('attachments'):
                try:
                    TicketFile.objects.create(
                        ticket=ticket,
                        file=file,
                        file_name=file.name,
                        file_size=file.size,
                        uploaded_by=request.user
                    )
                except:
                    pass
        
        messages.success(request, f'Ticket {ticket.tk_id} updated successfully!')
        return redirect('ticket_detail', ticket_id=ticket.id)
    
    return render(request, 'core/edit_ticket.html', {
        'ticket': ticket,
        'employees': employees,
        'tasks': tasks,
    })

@user_passes_test(is_admin)
def update_ticket_status(request, ticket_id):
    """Update ticket status (admin only)"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        ticket.status = request.POST.get('status')
        ticket.priority = request.POST.get('priority', ticket.priority)
        if request.POST.get('assigned_to'):
            ticket.assigned_to_id = request.POST.get('assigned_to')
        ticket.save()
        messages.success(request, 'Ticket updated successfully!')
        return redirect('ticket_detail', ticket_id=ticket.id)
    employees = User.objects.filter(is_superuser=False, employee__isnull=False).select_related('employee')
    return render(request, 'core/update_ticket.html', {'ticket': ticket, 'employees': employees})

@login_required
def delete_ticket(request, ticket_id):
    """Delete ticket"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.user.is_superuser or ticket.created_by == request.user:
        ticket_id_str = ticket.tk_id
        ticket.delete()
        messages.success(request, f'Ticket {ticket_id_str} deleted successfully!')
        if request.user.is_superuser:
            return redirect('all_tickets')
        else:
            return redirect('my_tickets')
    else:
        messages.error(request, 'You do not have permission to delete this ticket.')
        if request.user.is_superuser:
            return redirect('all_tickets')
        else:
            return redirect('my_tickets')

@login_required
def my_attendance(request):
    try:
        employee = request.user.employee
        if not employee.can_view_attendance:
            return HttpResponse('You are restricted from accessing attendance.', status=403)
    except Exception:
        return HttpResponse('You are restricted from accessing attendance.', status=403)
    
    today = timezone.now().date()
    records = Attendance.objects.filter(employee=employee).order_by('-date')
    today_record = Attendance.objects.filter(employee=employee, date=today).first()
    
    # Get today's attendance logs
    try:
        today_logs = AttendanceLog.objects.filter(
            employee=employee,
            timestamp__date=today
        ).order_by('timestamp')
    except Exception:
        today_logs = []
    
    if request.method == 'POST':
        attendance_type = request.POST.get('attendance_type')
        if attendance_type in ['check_in', 'check_out', 'break_start', 'break_end']:
            try:
                # Create manual attendance log
                AttendanceLog.objects.create(
                    employee=employee,
                    attendance_type=attendance_type,
                    source='manual',
                    timestamp=timezone.now()
                )
                
                # Process attendance logs to update attendance record
                try:
                    zkt_service.process_attendance_logs()
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Error processing attendance logs: {e}")
                
                messages.success(request, f'{attendance_type.replace("_", " ").title()} recorded successfully!')
            except Exception as e:
                messages.error(request, f'Error recording attendance: {str(e)}')
        return redirect('my_attendance')
    
    return render(request, 'core/my_attendance.html', {
        'records': records, 
        'today_record': today_record,
        'today_logs': today_logs
    })

@login_required
@require_POST
def check_clock_status(request):
    """API endpoint to check if employee is currently clocked in"""
    try:
        employee = request.user.employee
    except Exception:
        return JsonResponse({'error': 'Employee not found'}, status=403)
    
    today = timezone.now().date()
    today_record = Attendance.objects.filter(employee=employee, date=today).first()
    
    # Employee is clocked in if they have check_in but no check_out for today
    is_clocked_in = False
    if today_record and today_record.check_in and not today_record.check_out:
        is_clocked_in = True
    
    return JsonResponse({
        'is_clocked_in': is_clocked_in,
        'check_in': today_record.check_in.isoformat() if today_record and today_record.check_in else None,
        'check_out': today_record.check_out.isoformat() if today_record and today_record.check_out else None,
    })

@login_required
@require_POST
def upload_screenshot(request):
    """API endpoint to upload employee screenshot"""
    try:
        employee = request.user.employee
    except Exception:
        return JsonResponse({'error': 'Employee not found'}, status=403)
    
    # Check if employee is clocked in
    today = timezone.now().date()
    today_record = Attendance.objects.filter(employee=employee, date=today).first()
    
    if not today_record or not today_record.check_in or today_record.check_out:
        return JsonResponse({'error': 'You must be clocked in to capture screenshots'}, status=400)
    
    # Get screenshot from request
    if 'screenshot' not in request.FILES:
        return JsonResponse({'error': 'No screenshot file provided'}, status=400)
    
    screenshot_file = request.FILES['screenshot']
    
    # Validate file type
    if not screenshot_file.content_type.startswith('image/'):
        return JsonResponse({'error': 'Invalid file type. Only images are allowed'}, status=400)
    
    # Create screenshot record
    try:
        screenshot = EmployeeScreenshot.objects.create(
            employee=employee,
            screenshot=screenshot_file,
            date=today,
            captured_at=timezone.now()
        )
        return JsonResponse({
            'success': True,
            'message': 'Screenshot uploaded successfully',
            'screenshot_id': screenshot.id,
            'captured_at': screenshot.captured_at.isoformat()
        })
    except Exception as e:
        logger.error(f"Error uploading screenshot: {str(e)}")
        return JsonResponse({'error': f'Error uploading screenshot: {str(e)}'}, status=500)

@user_passes_test(is_admin)
def employee_screenshots(request, employee_id=None):
    """Admin view to see employee screenshots"""
    from django.db.models import Q
    from .company_utils import get_user_company, is_super_admin, is_company_admin
    
    # Get user's company
    user_company = get_user_company(request.user)
    
    # Get employees based on permissions
    if is_super_admin(request.user):
        employees = Employee.objects.select_related('user', 'department', 'company').all()
    elif user_company:
        employees = Employee.objects.filter(company=user_company).select_related('user', 'department', 'company')
    else:
        employees = Employee.objects.none()
    
    # Get selected employee from URL parameter or GET parameter
    selected_employee_id = employee_id or request.GET.get('employee_id')
    selected_employee = None
    screenshots = EmployeeScreenshot.objects.none()
    
    if selected_employee_id:
        try:
            selected_employee = get_object_or_404(Employee, id=selected_employee_id)
            # Verify access
            if not is_super_admin(request.user) and selected_employee.company != user_company:
                return HttpResponse('You do not have permission to view this employee\'s screenshots.', status=403)
            
            # Get date filter
            date_filter = request.GET.get('date', '')
            
            # Get screenshots for selected employee
            screenshots = EmployeeScreenshot.objects.filter(employee=selected_employee).order_by('-captured_at')
            
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    screenshots = screenshots.filter(date=filter_date)
                except ValueError:
                    pass
        except Exception as e:
            logger.error(f"Error loading employee screenshots: {str(e)}")
    
    # Get date range for filter
    if selected_employee:
        date_range = EmployeeScreenshot.objects.filter(employee=selected_employee).aggregate(
            min_date=Min('date'),
            max_date=Max('date')
        )
    else:
        date_range = {'min_date': None, 'max_date': None}
    
    return render(request, 'core/employee_screenshots.html', {
        'employees': employees,
        'selected_employee': selected_employee,
        'screenshots': screenshots,
        'date_range': date_range,
        'selected_date': request.GET.get('date', ''),
    })

@user_passes_test(is_admin)
def all_attendance(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    employees = Employee.objects.all()
    form = AttendanceFilterForm(request.GET)
    
    records = Attendance.objects.select_related('employee__user', 'employee__department').order_by('-date')
    
    # Filter by employee if provided via GET parameter (from employee profile)
    employee_id = request.GET.get('employee')
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
            records = records.filter(employee=employee)
            # Pre-fill form with employee
            form = AttendanceFilterForm(initial={'employee': employee})
        except Employee.DoesNotExist:
            pass
    
    if form.is_valid():
        if form.cleaned_data.get('employee'):
            records = records.filter(employee=form.cleaned_data['employee'])
        if form.cleaned_data.get('start_date'):
            records = records.filter(date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            records = records.filter(date__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('status'):
            records = records.filter(status=form.cleaned_data['status'])
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Employee', 'Department', 'Date', 'Check In', 'Check Out', 'Status', 'Work Hours', 'Late Minutes']
        data = []
        for att in records:
            data.append([
                att.id,
                att.employee.user.get_full_name() or att.employee.user.username,
                att.employee.department.name if att.employee.department else 'N/A',
                att.date.strftime('%Y-%m-%d'),
                att.check_in.strftime('%H:%M') if att.check_in else 'N/A',
                att.check_out.strftime('%H:%M') if att.check_out else 'N/A',
                att.get_status_display(),
                f"{att.total_work_hours:.2f}" if att.total_work_hours else 'N/A',
                att.late_minutes
            ])
        filename = f"attendance_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Attendance Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Attendance Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Attendance Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Attendance Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('all_attendance')
    
    # For graph: attendance count by status
    status_counts = Attendance.objects.values('status').annotate(count=Count('id'))
    
    # Get machines for sync modal
    machines = AttendanceMachine.objects.all().order_by('name', 'location')
    today = timezone.now().date()
    
    return render(request, 'core/all_attendance.html', {
        'records': records,
        'status_counts': list(status_counts),
        'employees': employees,
        'form': form,
        'machines': machines,
        'today': today,
    })

@user_passes_test(is_admin)
def reprocess_attendance_logs(request):
    """Manually reprocess attendance logs into attendance records"""
    from .attendance_service import AttendanceService
    from .models import AttendanceLog, Attendance
    from django.db.models import Count
    import traceback
    
    try:
        # Count logs before processing
        total_logs = AttendanceLog.objects.count()
        recent_logs = AttendanceLog.objects.filter(
            timestamp__date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        # Check log types for debugging
        log_types = AttendanceLog.objects.filter(
            timestamp__date__gte=timezone.now().date() - timedelta(days=30)
        ).values('attendance_type').annotate(count=Count('id'))
        log_types_info = ', '.join([f"{lt['attendance_type']}: {lt['count']}" for lt in log_types])
        
        # Count attendance records before processing
        attendance_before = Attendance.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        # Process logs
        processed_count = AttendanceService.process_attendance_logs()
        
        # Count attendance records after processing
        total_attendance = Attendance.objects.count()
        recent_attendance = Attendance.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        if processed_count > 0:
            messages.success(
                request, 
                f'Successfully processed {processed_count} attendance logs! '
                f'Log types found: {log_types_info}. '
                f'Attendance records: {attendance_before} → {recent_attendance} (last 30 days)'
            )
        else:
            messages.warning(
                request, 
                f'No attendance logs to process. Total logs: {total_logs} (last 30 days: {recent_logs}). '
                f'If logs exist, check their attendance_type values.'
            )
    except Exception as e:
        error_msg = f"Error processing attendance logs: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        messages.error(request, f'Error processing attendance logs: {str(e)}')
    
    return redirect('all_attendance')

@user_passes_test(is_admin)
def attendance_logs(request):
    """View attendance logs with filtering"""
    form = AttendanceFilterForm(request.GET)
    logs = AttendanceLog.objects.select_related('employee__user').order_by('-timestamp')
    
    if form.is_valid():
        if form.cleaned_data.get('employee'):
            logs = logs.filter(employee=form.cleaned_data['employee'])
        if form.cleaned_data.get('start_date'):
            logs = logs.filter(timestamp__date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            logs = logs.filter(timestamp__date__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('source'):
            logs = logs.filter(source=form.cleaned_data['source'])
    
    return render(request, 'core/attendance_logs.html', {
        'logs': logs,
        'form': form,
    })

@user_passes_test(is_admin)
def sync_zkt_machine(request):
    """Sync attendance data from ZKT machine (legacy - redirects to new sync)"""
    return redirect('sync_attendance_machine')

@user_passes_test(is_admin)
def sync_attendance_machine(request, machine_id=None):
    """Sync attendance data from a specific machine or all machines"""
    from .attendance_service import AttendanceService
    
    try:
        # Get parameters from POST or GET
        if request.method == 'POST':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            machine_id = request.POST.get('machine_id') or machine_id
        else:
            # Handle GET requests (from links)
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            machine_id = request.GET.get('machine_id') or machine_id
        
        # Parse dates if provided
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        
        if machine_id:
            # Sync specific machine
            try:
                machine_id = int(machine_id)
            except (ValueError, TypeError):
                messages.error(request, 'Invalid machine ID')
                return redirect('all_attendance')
            
            machine = get_object_or_404(AttendanceMachine, id=machine_id)
            result = AttendanceService.sync_machine_attendance(machine, start_date, end_date)
            
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, result['message'])
        else:
            # Sync all active machines
            results = AttendanceService.sync_all_machines(start_date, end_date)
            total_synced = sum(r['synced_count'] for r in results.values())
            success_count = sum(1 for r in results.values() if r['success'])
            total_machines = len(results)
            
            if total_machines == 0:
                messages.warning(request, 'No active machines found to sync.')
            elif success_count == 0:
                messages.error(request, f'Failed to sync from all {total_machines} machine(s). Check machine configurations.')
            else:
                messages.success(request, f'Synced {total_synced} records from {success_count} of {total_machines} machine(s)!')
        
        # Process attendance logs to create/update attendance records
        try:
            processed_count = AttendanceService.process_attendance_logs()
            if processed_count > 0:
                logger.info(f"Processed {processed_count} attendance logs into attendance records")
                messages.info(request, f'Processed {processed_count} attendance logs into attendance records.')
            else:
                messages.info(request, 'No attendance logs to process.')
        except Exception as e:
            import traceback
            error_msg = f"Error processing attendance logs: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            messages.error(request, f'Error processing attendance logs: {str(e)}')
            # Don't fail the sync if processing fails, just log it
        
    except Exception as e:
        import traceback
        logger.error(f"Error syncing attendance: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, f'Error syncing attendance: {str(e)}')
    
    return redirect('all_attendance')

@user_passes_test(is_admin)
def debug_attendance_matching(request, machine_id):
    """Debug view to test attendance matching"""
    from .attendance_service import AttendanceService
    from .machine_drivers import get_machine_driver
    
    machine = get_object_or_404(AttendanceMachine, id=machine_id)
    debug_info = {
        'machine': machine,
        'employees': [],
        'attendance_records': [],
        'matches': [],
        'errors': []
    }
    
    try:
        # Get driver and connect
        driver = get_machine_driver(machine)
        
        # Try to connect and capture detailed error
        connection_result = driver.connect()
        if not connection_result:
            # Connection failed, get detailed error message
            error_msg = getattr(driver, 'connection_error', 'Unknown connection error')
            debug_info['errors'].append(f"Connection Error: {error_msg}")
            debug_info['errors'].append("")
            debug_info['errors'].append("Troubleshooting steps:")
            debug_info['errors'].append(f"1. Verify machine is powered on and connected to network")
            debug_info['errors'].append(f"2. Check IP address: {machine.ip_address} (ping this IP from your computer)")
            debug_info['errors'].append(f"3. Check port: {machine.port or 4370} (ensure it's not blocked by firewall)")
            debug_info['errors'].append(f"4. Verify machine and computer are on the same network")
            debug_info['errors'].append(f"5. Check if ZKT SDK is installed (zk or pyzk package)")
            debug_info['errors'].append(f"6. Try increasing timeout in machine configuration")
            
            # Try test_connection for more details
            try:
                test_result = driver.test_connection()
                if not test_result.get('success'):
                    debug_info['errors'].append("")
                    debug_info['errors'].append(f"Connection test result: {test_result.get('message', 'Unknown error')}")
            except Exception as test_error:
                debug_info['errors'].append("")
                debug_info['errors'].append(f"Test connection error: {str(test_error)}")
        
        if driver.is_connected():
            # Get sample attendance data
            attendance_data = driver.get_attendance_data()
            debug_info['attendance_records'] = attendance_data[:10]  # First 10 records
            
            # Get unique user IDs
            unique_user_ids = set(str(r['user_id']).strip() for r in attendance_data)
            
            # Test matching for each user ID
            for user_id in list(unique_user_ids)[:10]:
                match_info = {
                    'machine_user_id': user_id,
                    'matched': False,
                    'method': None,
                    'employee': None
                }
                
                # Try all matching methods
                employee = Employee.objects.filter(machine_id=user_id).first()
                if employee:
                    match_info['matched'] = True
                    match_info['method'] = 'machine_id (exact)'
                    match_info['employee'] = employee
                else:
                    # Try with stripped
                    all_employees = Employee.objects.exclude(machine_id__isnull=True).exclude(machine_id='')
                    for emp in all_employees:
                        if emp.machine_id and str(emp.machine_id).strip() == user_id:
                            match_info['matched'] = True
                            match_info['method'] = 'machine_id (stripped)'
                            match_info['employee'] = emp
                            break
                
                if not match_info['matched']:
                    try:
                        emp_id = int(user_id)
                        employee = Employee.objects.filter(id=emp_id).first()
                        if employee:
                            match_info['matched'] = True
                            match_info['method'] = 'employee.id'
                            match_info['employee'] = employee
                    except:
                        pass
                
                if not match_info['matched']:
                    try:
                        user_db_id = int(user_id)
                        employee = Employee.objects.filter(user_id=user_db_id).first()
                        if employee:
                            match_info['matched'] = True
                            match_info['method'] = 'user.id'
                            match_info['employee'] = employee
                    except:
                        pass
                
                debug_info['matches'].append(match_info)
            
            driver.disconnect()
        else:
            if not debug_info['errors']:
                debug_info['errors'].append('Failed to connect to machine. Check connection settings and network connectivity.')
    except Exception as e:
        error_type = type(e).__name__
        debug_info['errors'].append(f"Error ({error_type}): {str(e)}")
        import traceback
        debug_info['errors'].append(f"Full traceback:\n{traceback.format_exc()}")
    
    # Get all employees with machine IDs
    debug_info['employees'] = Employee.objects.exclude(machine_id__isnull=True).exclude(machine_id='')[:20]
    
    return render(request, 'core/debug_attendance_matching.html', {
        'debug_info': debug_info
    })

@user_passes_test(is_admin)
def test_machine_connection(request, machine_id):
    """Test connection to a specific machine with detailed feedback"""
    from .attendance_service import AttendanceService
    import json
    
    machine = get_object_or_404(AttendanceMachine, id=machine_id)
    result = AttendanceService.test_machine_connection(machine)
    
    # Store detailed result in session for display
    request.session['connection_test_result'] = {
        'machine_name': machine.name,
        'machine_ip': machine.ip_address,
        'machine_port': machine.port or 4370,
        'success': result['success'],
        'message': result['message'],
        'details': result.get('details', {}),
        'machine_info': result.get('machine_info', {}),
        'troubleshooting': result.get('troubleshooting', [])
    }
    
    if result['success']:
        messages.success(request, f'Connection test successful: {result["message"]}')
    else:
        messages.error(request, f'Connection test failed: {result["message"]}')
        if result.get('troubleshooting'):
            # Add troubleshooting tips as info messages
            for tip in result['troubleshooting'][:3]:  # Show first 3 tips
                messages.info(request, tip)
    
    return redirect('manage_attendance_machines')

@user_passes_test(is_admin)
def manage_attendance_machines(request):
    """Manage attendance machines"""
    machines = AttendanceMachine.objects.all().order_by('name', 'location')
    
    # Check if machine with IP 192.168.18.80 exists
    target_ip = "192.168.18.80"
    machine_with_ip = AttendanceMachine.objects.filter(ip_address=target_ip).first()
    machine_check_info = None
    if machine_with_ip:
        machine_check_info = {
            'exists': True,
            'machine': machine_with_ip,
            'message': f'Machine with IP {target_ip} already exists: "{machine_with_ip.name}"'
        }
    else:
        machine_check_info = {
            'exists': False,
            'message': f'No machine found with IP {target_ip}. You can add it below.'
        }
    
    if request.method == 'POST':
        form = AttendanceMachineForm(request.POST)
        if form.is_valid():
            machine = form.save()
            messages.success(request, f'Attendance machine "{machine.name}" added successfully!')
            return redirect('manage_attendance_machines')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AttendanceMachineForm()
    
    # Get connection test result from session if exists
    connection_test_result = request.session.pop('connection_test_result', None)
    
    return render(request, 'core/manage_attendance_machines.html', {
        'machines': machines,
        'form': form,
        'connection_test_result': connection_test_result,
        'machine_check_info': machine_check_info,
    })

@user_passes_test(is_admin)
def edit_attendance_machine(request, machine_id):
    """Edit attendance machine"""
    machine = get_object_or_404(AttendanceMachine, id=machine_id)
    
    if request.method == 'POST':
        form = AttendanceMachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance machine updated successfully!')
            return redirect('manage_attendance_machines')
    else:
        form = AttendanceMachineForm(instance=machine)
    
    return render(request, 'core/edit_attendance_machine.html', {
        'machine': machine,
        'form': form,
    })

@user_passes_test(is_admin)
def delete_attendance_machine(request, machine_id):
    """Delete attendance machine"""
    machine = get_object_or_404(AttendanceMachine, id=machine_id)
    machine.delete()
    messages.success(request, 'Attendance machine deleted successfully!')
    return redirect('manage_attendance_machines')

@user_passes_test(is_admin)
def manage_employee_machine_ids(request):
    """Manage employee machine IDs"""
    employees = Employee.objects.all()
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        employee = get_object_or_404(Employee, id=employee_id)
        form = EmployeeMachineForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Machine IDs updated for {employee.user.get_full_name() or employee.user.username}!')
            return redirect('manage_employee_machine_ids')
    else:
        form = EmployeeMachineForm()
    
    return render(request, 'core/manage_employee_machine_ids.html', {
        'employees': employees,
        'form': form,
    })

@user_passes_test(is_admin)
def manual_attendance_entry(request):
    """Manual attendance entry - Direct attendance record creation"""
    if request.method == 'POST':
        form = ManualAttendanceForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            date = form.cleaned_data['date']
            status = form.cleaned_data['status']
            check_in = form.cleaned_data.get('check_in')
            check_out = form.cleaned_data.get('check_out')
            break_start = form.cleaned_data.get('break_start')
            break_end = form.cleaned_data.get('break_end')
            is_late = form.cleaned_data.get('is_late', False)
            late_minutes = form.cleaned_data.get('late_minutes', 0) or 0
            notes = form.cleaned_data.get('notes', '') or ''
            
            try:
                # Convert datetime fields to timezone-aware if provided and naive
                if check_in:
                    if timezone.is_naive(check_in):
                        check_in = timezone.make_aware(check_in)
                if check_out:
                    if timezone.is_naive(check_out):
                        check_out = timezone.make_aware(check_out)
                if break_start:
                    if timezone.is_naive(break_start):
                        break_start = timezone.make_aware(break_start)
                if break_end:
                    if timezone.is_naive(break_end):
                        break_end = timezone.make_aware(break_end)
                
                # Get or create attendance record
                attendance, created = Attendance.objects.get_or_create(
                    employee=employee,
                    date=date,
                    defaults={
                        'status': status,
                        'check_in': check_in,
                        'check_out': check_out,
                        'break_start': break_start,
                        'break_end': break_end,
                        'is_late': is_late,
                        'late_minutes': late_minutes,
                        'notes': notes
                    }
                )
                
                # If record already exists, update it
                if not created:
                    attendance.status = status
                    attendance.check_in = check_in if check_in else attendance.check_in
                    attendance.check_out = check_out if check_out else attendance.check_out
                    attendance.break_start = break_start if break_start else attendance.break_start
                    attendance.break_end = break_end if break_end else attendance.break_end
                    attendance.is_late = is_late
                    attendance.late_minutes = late_minutes
                    attendance.notes = notes if notes else attendance.notes
                    attendance.save()
                
                # Calculate work hours if check_in and check_out are provided
                if attendance.check_in and attendance.check_out:
                    attendance.calculate_hours()
                
                messages.success(request, f'Attendance record {"created" if created else "updated"} successfully for {employee.user.get_full_name() or employee.user.username} on {date}!')
                return redirect('all_attendance')
            except Exception as e:
                import traceback
                logger.error(f"Error creating manual attendance: {str(e)}\n{traceback.format_exc()}")
                messages.error(request, f'Error recording attendance: {str(e)}')
    else:
        form = ManualAttendanceForm()
        # Set default date to today
        form.initial['date'] = timezone.now().date()
    
    return render(request, 'core/manual_attendance_entry.html', {
        'form': form,
    })

@user_passes_test(is_admin)
def test_zkt_connection(request):
    """Test ZKT machine connection"""
    try:
        if zkt_service.connect():
            users = zkt_service.get_users()
            zkt_service.disconnect()
            messages.success(request, f'Successfully connected to ZKT machine! Found {len(users)} users.')
        else:
            messages.error(request, 'Failed to connect to ZKT machine. Please check IP address and port.')
    except Exception as e:
        messages.error(request, f'Error testing ZKT connection: {str(e)}')
    
    return redirect('manage_attendance_machines')

class HolidayForm(ModelForm):
    class Meta:
        model = Holiday
        fields = ['name', 'date', 'description']

@user_passes_test(is_admin)
def manage_holidays(request):
    holidays = Holiday.objects.all()
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.created_by = request.user
            holiday.save()
            return redirect('manage_holidays')
    else:
        form = HolidayForm()
    return render(request, 'core/manage_holidays.html', {'holidays': holidays, 'form': form})

@user_passes_test(is_admin)
def delete_holiday(request, holiday_id):
    Holiday.objects.filter(id=holiday_id).delete()
    return redirect('manage_holidays')

@login_required
def holidays(request):
    try:
        employee = request.user.employee
        if not employee.can_view_holidays:
            return HttpResponse('You are restricted from accessing holidays.', status=403)
    except Exception:
        return HttpResponse('You are restricted from accessing holidays.', status=403)
    holidays = Holiday.objects.all()
    return render(request, 'core/holidays.html', {'holidays': holidays})

class LeaveForm(ModelForm):
    class Meta:
        model = Leave
        fields = ['start_date', 'end_date', 'leave_type', 'reason']

@login_required
def apply_leave(request):
    try:
        employee = request.user.employee
        if not employee.can_view_leaves:
            return HttpResponse('You are restricted from accessing leaves.', status=403)
    except Exception:
        return HttpResponse('You are restricted from accessing leaves.', status=403)
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()
            # Create notification for admin
            admin_users = User.objects.filter(is_superuser=True)
            for admin in admin_users:
                create_notification(
                    recipient=admin,
                    sender=request.user,
                    notification_type='leave',
                    title=f'Leave request from {employee.user.get_full_name() or employee.user.username}',
                    message=f'Leave type: {leave.leave_type}, Dates: {leave.start_date} to {leave.end_date}',
                    link=f'/manage-leaves/'
                )
            return redirect('my_leaves')
    else:
        form = LeaveForm()
    return render(request, 'core/apply_leave.html', {'form': form})

@login_required
def my_leaves(request):
    try:
        employee = request.user.employee
        if not employee.can_view_leaves:
            return HttpResponse('You are restricted from accessing leaves.', status=403)
    except Exception:
        return HttpResponse('You are restricted from accessing leaves.', status=403)
    leaves = Leave.objects.filter(employee=employee).order_by('-applied_at')
    return render(request, 'core/my_leaves.html', {'leaves': leaves})

@user_passes_test(is_admin)
def manage_leaves(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    leaves = Leave.objects.select_related('employee__user', 'employee__department', 'reviewed_by').order_by('-applied_at')
    # Filter by employee if provided (from employee profile)
    employee_id = request.GET.get('employee')
    if employee_id:
        try:
            employee = Employee.objects.get(user_id=employee_id)
            leaves = leaves.filter(employee=employee)
        except Employee.DoesNotExist:
            pass
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Employee', 'Department', 'Leave Type', 'Start Date', 'End Date', 'Status', 'Applied Date', 'Reviewed By']
        data = []
        for leave in leaves:
            data.append([
                leave.id,
                leave.employee.user.get_full_name() or leave.employee.user.username,
                leave.employee.department.name if leave.employee.department else 'N/A',
                leave.get_leave_type_display(),
                leave.start_date.strftime('%Y-%m-%d'),
                leave.end_date.strftime('%Y-%m-%d'),
                leave.get_status_display(),
                leave.applied_at.strftime('%Y-%m-%d'),
                leave.reviewed_by.get_full_name() if leave.reviewed_by else 'Pending'
            ])
        filename = f"leaves_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Leaves Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Leaves Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Leaves Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Leaves Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('manage_leaves')
    
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        leave = Leave.objects.get(id=leave_id)
        leave.status = action
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.comments = comments
        leave.save()
        # Create notification for employee
        create_notification(
            recipient=leave.employee.user,
            sender=request.user,
            notification_type='leave',
            title=f'Leave request {action}',
            message=f'Your leave request has been {action}. {comments[:100]}',
            link=f'/my-leaves/'
        )
        return redirect('manage_leaves')
    return render(request, 'core/manage_leaves.html', {'leaves': leaves})

@user_passes_test(is_admin)
def edit_employee(request, employee_id):
    employee = Employee.objects.select_related('user').get(id=employee_id)
    departments = Department.objects.all()
    designations = Designation.objects.all()
    error = None
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        department_id = request.POST.get('department')
        designation_id = request.POST.get('designation')
        date_of_joining = request.POST.get('date_of_joining')
        machine_id = request.POST.get('machine_id')
        fingerprint_id = request.POST.get('fingerprint_id')
        face_id = request.POST.get('face_id')
        card_id = request.POST.get('card_id')
        profile_picture = request.FILES.get('profile_picture')
        
        if not date_of_joining:
            date_of_joining = None
            
        employee.user.first_name = first_name
        employee.user.last_name = last_name
        employee.user.save()
        # Handle salary field - convert to Decimal if provided
        salary = None
        salary_str = request.POST.get('salary', '').strip()
        if salary_str:
            try:
                from decimal import Decimal
                salary = Decimal(salary_str)
            except (ValueError, TypeError):
                salary = None
        
        employee.phone = phone
        employee.address = address
        employee.city = request.POST.get('city', '').strip()
        employee.department_id = department_id
        employee.designation_id = designation_id
        employee.salary = salary
        employee.date_of_joining = date_of_joining
        # Strip whitespace from machine IDs
        employee.machine_id = machine_id.strip() if machine_id and machine_id.strip() else None
        employee.fingerprint_id = fingerprint_id.strip() if fingerprint_id and fingerprint_id.strip() else None
        employee.face_id = face_id.strip() if face_id and face_id.strip() else None
        employee.card_id = card_id.strip() if card_id and card_id.strip() else None
        if profile_picture:
            employee.profile_picture = profile_picture
        employee.save()
        return redirect('employee_list')
    # Get all existing cities for autocomplete
    existing_cities = Employee.objects.exclude(city__isnull=True).exclude(city='').values_list('city', flat=True).distinct().order_by('city')
    return render(request, 'core/edit_employee.html', {
        'employee': employee,
        'departments': departments,
        'designations': designations,
        'error': error,
        'existing_cities': existing_cities
    })

@user_passes_test(is_admin)
def delete_employee(request, employee_id):
    """Completely delete employee and user from the system - FORCE DELETE with FK checks disabled"""
    from django.db import connection
    from django.db.utils import OperationalError, ProgrammingError
    
    try:
        # Get employee
        employee = get_object_or_404(Employee, id=employee_id)
        user = employee.user
        employee_name = employee.user.get_full_name() or employee.user.username
        username = user.username
        user_id = user.id
        
        # Prevent self-deletion
        if user.id == request.user.id:
            messages.warning(request, 'You cannot delete your own account.')
            return redirect('employee_list')
        
        # FORCE DELETE using raw SQL with foreign key checks disabled
        with connection.cursor() as cursor:
            try:
                # Disable foreign key checks temporarily (MySQL)
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                
                # Delete all related records - comprehensive cleanup
                tables_to_clean = [
                    ('core_employeescreenshot', 'employee_id', employee_id),
                    ('core_chatmessage', 'sender_id', user_id),
                    ('core_chatmessage', 'recipient_id', user_id),
                    ('core_notification', 'recipient_id', user_id),
                    ('core_notification', 'sender_id', user_id),
                    ('core_ticket', 'created_by_id', user_id),
                    ('core_ticket', 'assigned_to_id', user_id),
                    ('core_userfamilyinfo', 'user_id', user_id),
                    ('core_onlineuser', 'user_id', user_id),
                    ('core_userprofile', 'user_id', user_id),
                    ('core_attendance', 'employee_id', employee_id),
                    ('core_attendancelog', 'employee_id', employee_id),
                    ('core_leave', 'employee_id', employee_id),
                    ('core_payrollitem', 'employee_id', employee_id),
                    ('core_payslip', 'employee_id', employee_id),
                    ('core_loan', 'employee_id', employee_id),
                    ('core_advancerequest', 'employee_id', employee_id),
                    ('core_task', 'assigned_by_id', employee_id),
                    ('core_task', 'assigned_to_id', employee_id),
                    ('core_taskcomment', 'created_by_id', employee_id),
                    ('core_taskfollower', 'employee_id', employee_id),
                    ('core_subtask', 'assigned_to_id', employee_id),
                    ('core_employeeeducation', 'employee_id', employee_id),
                    ('core_employeeworkexperience', 'employee_id', employee_id),
                    ('core_employeeallowance', 'employee_id', employee_id),
                    ('core_employeededuction', 'employee_id', employee_id),
                ]
                
                for table, column, id_value in tables_to_clean:
                    try:
                        if column.endswith('_id'):
                            cursor.execute(f"DELETE FROM {table} WHERE {column} = %s", [id_value])
                    except (OperationalError, ProgrammingError) as e:
                        logger.warning(f"Could not delete from {table}.{column}: {e}")
                
                # Update tables that use SET_NULL
                try:
                    cursor.execute("UPDATE core_project SET manager_id = NULL WHERE manager_id = %s", [employee_id])
                except:
                    pass
                
                try:
                    cursor.execute("UPDATE core_asset SET asset_user_id = NULL WHERE asset_user_id = %s", [employee_id])
                except:
                    pass
                
                # Delete employee record
                try:
                    cursor.execute("DELETE FROM core_employee WHERE id = %s", [employee_id])
                except Exception as e:
                    logger.error(f"Error deleting employee: {e}")
                
                # Finally delete user - THIS IS CRITICAL
                try:
                    cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])
                    # Verify deletion
                    cursor.execute("SELECT COUNT(*) FROM auth_user WHERE id = %s", [user_id])
                    count = cursor.fetchone()[0]
                    if count > 0:
                        logger.error(f"User {user_id} still exists after deletion!")
                        # Try one more time
                        cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])
                except Exception as e:
                    logger.error(f"Error deleting user: {e}")
                
                # Re-enable foreign key checks
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                
                # Final verification
                cursor.execute("SELECT COUNT(*) FROM auth_user WHERE id = %s", [user_id])
                user_exists = cursor.fetchone()[0] > 0
                
                cursor.execute("SELECT COUNT(*) FROM core_employee WHERE id = %s", [employee_id])
                emp_exists = cursor.fetchone()[0] > 0
                
                if user_exists or emp_exists:
                    logger.error(f"DELETION FAILED: User exists={user_exists}, Employee exists={emp_exists}")
                    messages.error(request, f'Failed to completely delete employee "{employee_name}". User exists: {user_exists}, Employee exists: {emp_exists}. Please check database manually.')
                else:
                    messages.success(request, f'Employee "{employee_name}" (username: {username}) has been completely removed from the system. They can no longer access or login.')
            
            except Exception as inner_error:
                # Error in inner try block - re-enable FK checks and re-raise
                try:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                except:
                    pass
                raise inner_error
        
    except Exception as e:
        logger.error(f"Error deleting employee {employee_id}: {str(e)}")
        # Try to re-enable FK checks even if error occurred
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        except:
            pass
        messages.error(request, f'Error deleting employee: {str(e)}. Please try again or contact support.')
    
    return redirect('employee_list')

@require_POST
@user_passes_test(is_admin)
def change_employee_role(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    # Role system is not implemented yet
    messages.info(request, 'Role system is not implemented yet.')
    return redirect('employee_list')

# Remove all permission matrix and old permission logic

@user_passes_test(is_admin)
def admin_roles(request):
    # Role and Permission models are not implemented yet
    return render(request, 'core/admin_roles.html', {
        'roles': [],
        'role_permissions': {},
    })

@user_passes_test(is_admin)
def client_list(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    clients = Client.objects.prefetch_related('projects').all()
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Name', 'Email', 'Phone', 'Company', 'Total Projects']
        data = []
        for client in clients:
            data.append([
                client.id,
                client.name,
                client.email or 'N/A',
                client.phone or 'N/A',
                client.company or 'N/A',
                client.projects.count()
            ])
        filename = f"clients_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Clients Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Clients Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Clients Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Clients Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('client_list')
    
    return render(request, 'core/client_list.html', {'clients': clients})

@user_passes_test(is_admin)
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Client added successfully!')
                return redirect('client_list')
            except Exception as e:
                messages.error(request, f'Error adding client: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClientForm()
    return render(request, 'core/add_client.html', {'form': form})

@user_passes_test(is_admin)
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Client updated successfully!')
                return redirect('client_list')
            except Exception as e:
                messages.error(request, f'Error updating client: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClientForm(instance=client)
    return render(request, 'core/edit_client.html', {'form': form, 'client': client})

@user_passes_test(is_admin)
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'core/delete_client.html', {'client': client})

@login_required
def project_list(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    
    if request.user.is_superuser:
        # Admin sees all projects
        projects = Project.objects.select_related('client', 'manager__department', 'manager__designation', 'manager__user').prefetch_related('tasks').all()
    else:
        # Employees see projects where they are manager or have tasks
        try:
            employee = request.user.employee
            projects = Project.objects.filter(
                Q(manager=employee) | Q(tasks__assigned_to=employee)
            ).select_related('client', 'manager__department', 'manager__designation', 'manager__user').prefetch_related('tasks').distinct()
        except:
            projects = Project.objects.none()
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Name', 'Client', 'Manager', 'Total Tasks', 'Completed Tasks', 'Pending Tasks']
        data = []
        for proj in projects:
            tasks = proj.tasks.all()
            completed = tasks.filter(status='completed').count()
            pending = tasks.filter(status='pending').count()
            data.append([
                proj.id,
                proj.name,
                proj.client.name if proj.client else 'N/A',
                proj.manager.user.get_full_name() if proj.manager else 'N/A',
                tasks.count(),
                completed,
                pending
            ])
        filename = f"projects_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Projects Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Projects Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Projects Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Projects Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('project_list')
    
    # Calculate statistics
    total_projects = projects.count()
    projects_with_managers = projects.exclude(manager__isnull=True).count()
    unique_clients = projects.values('client').distinct().count()
    total_tasks = sum(project.tasks.count() for project in projects)
    
    return render(request, 'core/project_list.html', {
        'projects': projects,
        'total_projects': total_projects,
        'projects_with_managers': projects_with_managers,
        'unique_clients': unique_clients,
        'total_tasks': total_tasks,
    })

@login_required
def add_project(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only administrators can add projects.')
        return redirect('project_list')
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'core/add_project.html', {'form': form})

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not request.user.is_superuser and not (project.manager and project.manager.user == request.user):
        messages.error(request, 'You do not have permission to edit this project.')
        return redirect('project_list')
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'core/edit_project.html', {'form': form, 'project': project})

@login_required
def delete_project(request, project_id):
    if not request.user.is_superuser:
        messages.error(request, 'Only administrators can delete projects.')
        return redirect('project_list')
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    return redirect('project_list')

@login_required
def assign_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # Permission check
    if not request.user.is_superuser and not (project.manager and project.manager.user == request.user):
        return HttpResponseForbidden('You do not have permission to assign tasks.')
    manager = project.manager if project.manager else None
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, project=project, manager=manager)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.assigned_by = manager if manager else None
            task.save()
            
            # Handle multiple file attachments
            from .models import TaskFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        TaskFile.objects.create(
                            task=task,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            
            # Create notification for assigned employee
            create_notification(
                recipient=task.assigned_to.user,
                sender=request.user,
                notification_type='task',
                title=f'New task assigned: {task.title}',
                message=task.description[:200] if task.description else 'No description',
                link=f'/core/projects/{project.id}/tasks/'
            )
            return redirect(reverse('project_tasks', args=[project.id]))
    else:
        form = TaskForm(project=project, manager=manager)
    return render(request, 'core/assign_task.html', {'form': form, 'project': project})

@login_required
def project_tasks(request, project_id):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    project = get_object_or_404(Project, id=project_id)
    # Permission check - allow admin, project manager, or employees with tasks in this project
    if not request.user.is_superuser:
        try:
            employee = request.user.employee
            if project.manager != employee and not project.tasks.filter(assigned_to=employee).exists():
                messages.error(request, 'You do not have permission to view tasks for this project.')
                return redirect('project_list')
        except:
            messages.error(request, 'You do not have permission to view tasks for this project.')
            return redirect('project_list')
    tasks = Task.objects.filter(project=project).select_related('assigned_to', 'assigned_to__user', 'assigned_by', 'assigned_by__user').all()
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Title', 'Assigned To', 'Assigned By', 'Status', 'Priority', 'Deadline', 'Created Date']
        data = []
        for task in tasks:
            data.append([
                task.id,
                task.title,
                task.assigned_to.user.get_full_name() if task.assigned_to else 'N/A',
                task.assigned_by.user.get_full_name() if task.assigned_by else 'N/A',
                task.get_status_display(),
                task.get_priority_display(),
                task.deadline.strftime('%Y-%m-%d') if task.deadline else 'N/A',
                task.created_at.strftime('%Y-%m-%d')
            ])
        filename = f"project_{project.id}_tasks_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, f'Tasks Report - {project.name}', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, f'Tasks Report - {project.name}', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, f'Tasks Report - {project.name}', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, f'Tasks Report - {project.name}', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('project_tasks', project_id=project.id)
    
    # Calculate statistics
    tasks_pending = tasks.filter(status='pending').count()
    tasks_in_progress = tasks.filter(status='in_progress').count()
    tasks_completed = tasks.filter(status='completed').count()
    
    return render(request, 'core/project_tasks.html', {
        'project': project, 
        'tasks': tasks,
        'tasks_pending': tasks_pending,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
    })

@login_required
def my_tasks(request):
    # If employee filter is provided and user is admin, show tasks for that employee
    employee_id = request.GET.get('employee')
    if employee_id and request.user.is_superuser:
        try:
            employee_user = User.objects.get(id=employee_id)
            employee = Employee.objects.get(user=employee_user)
            tasks = Task.objects.filter(assigned_to=employee).select_related('project', 'assigned_by')
        except (User.DoesNotExist, Employee.DoesNotExist):
            try:
                employee = request.user.employee
                if not employee.can_view_tasks:
                    return HttpResponse('You are restricted from accessing tasks.', status=403)
                tasks = Task.objects.filter(assigned_to=employee).select_related('project', 'assigned_by')
            except Employee.DoesNotExist:
                return render(request, 'core/no_employee.html')
    else:
        try:
            employee = request.user.employee
            if not employee.can_view_tasks:
                return HttpResponse('You are restricted from accessing tasks.', status=403)
        except Employee.DoesNotExist:
            return render(request, 'core/no_employee.html')
        tasks = Task.objects.filter(assigned_to=employee).select_related('project', 'assigned_by')
    
    # Calculate statistics
    tasks_pending = tasks.filter(status='pending').count()
    tasks_in_progress = tasks.filter(status='in_progress').count()
    tasks_completed = tasks.filter(status='completed').count()
    
    return render(request, 'core/my_tasks.html', {
        'tasks': tasks,
        'tasks_pending': tasks_pending,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
    })

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # Check if user has access to this project
    if not request.user.is_superuser:
        try:
            employee = request.user.employee
            if project.manager != employee and not project.tasks.filter(assigned_to=employee).exists():
                messages.error(request, 'You do not have access to this project.')
                return redirect('project_list')
        except:
            messages.error(request, 'You do not have access to this project.')
            return redirect('project_list')
    # Only project manager or admin can assign tasks
    can_assign = request.user.is_superuser or (project.manager and project.manager.user == request.user)
    departments = Department.objects.prefetch_related('employee_set__designation').all()
    employees_by_dept = []
    for dept in departments:
        emps = dept.employee_set.select_related('user', 'designation').all()
        employees_by_dept.append((dept, emps))
    if request.method == 'POST' and can_assign:
        selected_employee_ids = request.POST.getlist('assigned_to')
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid() and selected_employee_ids:
            for emp_id in selected_employee_ids:
                emp = Employee.objects.get(id=emp_id)
                task = form.save(commit=False)
                task.project = project
                task.assigned_by = project.manager if project.manager else None
                task.assigned_to = emp
                task.save()
            return redirect('project_detail', project_id=project.id)
    else:
        form = TaskForm()
    # Get task statistics
    tasks = project.tasks.all()
    tasks_pending = tasks.filter(status='pending').count()
    tasks_in_progress = tasks.filter(status='in_progress').count()
    tasks_completed = tasks.filter(status='completed').count()
    
    return render(request, 'core/project_detail.html', {
        'project': project,
        'can_assign': can_assign,
        'departments': departments,
        'employees_by_dept': employees_by_dept,
        'form': form,
        'tasks_pending': tasks_pending,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
    })

@login_required
def select_project_for_task(request):
    if request.user.is_superuser:
        projects = Project.objects.all()
    elif hasattr(request.user, 'employee') and request.user.employee.designation and request.user.employee.designation.name == 'Project Manager':
        projects = Project.objects.filter(manager=request.user.employee)
    else:
        projects = Project.objects.none()
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        if project_id:
            return redirect('assign_task', project_id=project_id)
    return render(request, 'core/select_project_for_task.html', {'projects': projects})

@login_required
def select_project_for_view_tasks(request):
    if request.user.is_superuser:
        projects = Project.objects.all()
    elif hasattr(request.user, 'employee') and request.user.employee.designation and request.user.employee.designation.name == 'Project Manager':
        projects = Project.objects.filter(manager=request.user.employee)
    else:
        projects = Project.objects.none()
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        if project_id:
            return redirect('project_tasks', project_id=project_id)
    return render(request, 'core/select_project_for_view_tasks.html', {'projects': projects})

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            return redirect('project_tasks', project_id=task.project.id)
    else:
        form = TaskForm(instance=task)
    return render(request, 'core/edit_task.html', {'form': form, 'task': task})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    project_id = task.project.id
    if request.method == 'POST':
        task.delete()
        return redirect('project_tasks', project_id=project_id)
    return render(request, 'core/delete_task.html', {'task': task})

@user_passes_test(is_admin)
def budget_category_list(request):
    categories = BudgetCategory.objects.all()
    return render(request, 'core/budget_category_list.html', {'categories': categories})

@user_passes_test(is_admin)
def budget_category_add(request):
    if request.method == 'POST':
        form = BudgetCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('budget_category_list')
    else:
        form = BudgetCategoryForm()
    return render(request, 'core/budget_category_form.html', {'form': form, 'action': 'Add'})

@user_passes_test(is_admin)
def budget_category_edit(request, pk):
    category = get_object_or_404(BudgetCategory, pk=pk)
    if request.method == 'POST':
        form = BudgetCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('budget_category_list')
    else:
        form = BudgetCategoryForm(instance=category)
    return render(request, 'core/budget_category_form.html', {'form': form, 'action': 'Edit'})

@user_passes_test(is_admin)
def budget_category_delete(request, pk):
    category = get_object_or_404(BudgetCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('budget_category_list')
    return render(request, 'core/budget_category_confirm_delete.html', {'category': category})

def budget_categories(request):
    return render(request, 'core/budget_categories.html')

@user_passes_test(is_admin)
def budget_list(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    # Check for export format
    export_format = request.GET.get('format', '')
    
    budgets = Budget.objects.select_related('category', 'project').all()
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Name', 'Type', 'Category', 'Project', 'Tax', 'Period Start', 'Period End', 'Note']
        data = []
        for budget in budgets:
            data.append([
                str(budget.id),
                str(budget.name),
                str(budget.get_type_display()),
                str(budget.category.name) if budget.category else 'N/A',
                str(budget.project.name) if budget.project else 'N/A',
                f"${float(budget.tax):.2f}" if budget.tax else '$0.00',
                budget.period_start.strftime('%Y-%m-%d') if budget.period_start else 'N/A',
                budget.period_end.strftime('%Y-%m-%d') if budget.period_end else 'N/A',
                str(budget.note)[:50] if budget.note else 'N/A',
            ])
        
        filename = f"budgets_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Budgets Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Budgets Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Budgets Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Budgets Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('budget_list')
    
    return render(request, 'core/budget_list.html', {'budgets': budgets})

@user_passes_test(is_admin)
def budget_add(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, request.FILES)
        if form.is_valid():
            budget = form.save()
            # Handle multiple file attachments
            from .models import BudgetFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        BudgetFile.objects.create(
                            budget=budget,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            return redirect('budget_list')
    else:
        form = BudgetForm()
    return render(request, 'core/budget_form.html', {'form': form, 'action': 'Add'})

@user_passes_test(is_admin)
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        form = BudgetForm(request.POST, request.FILES, instance=budget)
        if form.is_valid():
            form.save()
            # Handle multiple file attachments
            from .models import BudgetFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        BudgetFile.objects.create(
                            budget=budget,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget)
    return render(request, 'core/budget_form.html', {'form': form, 'action': 'Edit'})

@user_passes_test(is_admin)
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        budget.delete()
        return redirect('budget_list')
    return render(request, 'core/budget_confirm_delete.html', {'budget': budget})

def budgets(request):
    return render(request, 'core/budgets.html')

@user_passes_test(is_admin)
def budget_expense_list(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    # Check for export format
    export_format = request.GET.get('format', '')
    
    expenses = BudgetExpense.objects.select_related('budget').all()
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Budget', 'Title', 'Amount', 'Description', 'Date', 'Start Date', 'End Date']
        data = []
        for expense in expenses:
            data.append([
                str(expense.id),
                str(expense.budget.name),
                str(expense.title),
                f"Rs{float(expense.amount):.2f}" if expense.amount else 'Rs0.00',
                str(expense.description)[:50] if expense.description else 'N/A',
                expense.date.strftime('%Y-%m-%d') if expense.date else 'N/A',
                expense.start_date.strftime('%Y-%m-%d') if expense.start_date else 'N/A',
                expense.end_date.strftime('%Y-%m-%d') if expense.end_date else 'N/A',
            ])
        
        filename = f"budget_expenses_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Budget Expenses Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Budget Expenses Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Budget Expenses Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Budget Expenses Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('budget_expense_list')
    
    return render(request, 'core/budget_expense_list.html', {'expenses': expenses})

@user_passes_test(is_admin)
def budget_expense_add(request):
    if request.method == 'POST':
        form = BudgetExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save()
            # Handle multiple file attachments
            from .models import BudgetExpenseFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        BudgetExpenseFile.objects.create(
                            budget_expense=expense,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            return redirect('budget_expense_list')
    else:
        form = BudgetExpenseForm()
    return render(request, 'core/budget_expense_form.html', {'form': form, 'action': 'Add'})

@user_passes_test(is_admin)
def budget_expense_edit(request, pk):
    expense = get_object_or_404(BudgetExpense, pk=pk)
    if request.method == 'POST':
        form = BudgetExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            # Handle multiple file attachments
            from .models import BudgetExpenseFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        BudgetExpenseFile.objects.create(
                            budget_expense=expense,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            return redirect('budget_expense_list')
    else:
        form = BudgetExpenseForm(instance=expense)
    return render(request, 'core/budget_expense_form.html', {'form': form, 'action': 'Edit'})

@user_passes_test(is_admin)
def budget_expense_delete(request, pk):
    expense = get_object_or_404(BudgetExpense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        return redirect('budget_expense_list')
    return render(request, 'core/budget_expense_confirm_delete.html', {'expense': expense})

def budget_expense(request):
    return render(request, 'core/budget_expense.html')

@user_passes_test(is_admin)
def budget_revenue_list(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    # Check for export format
    export_format = request.GET.get('format', '')
    
    revenues = BudgetRevenue.objects.select_related('budget').all()
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Budget', 'Title', 'Amount', 'Description', 'Date', 'Start Date', 'End Date']
        data = []
        for revenue in revenues:
            data.append([
                str(revenue.id),
                str(revenue.budget.name),
                str(revenue.title),
                f"Rs{float(revenue.amount):.2f}" if revenue.amount else 'Rs0.00',
                str(revenue.description)[:50] if revenue.description else 'N/A',
                revenue.date.strftime('%Y-%m-%d') if revenue.date else 'N/A',
                revenue.start_date.strftime('%Y-%m-%d') if revenue.start_date else 'N/A',
                revenue.end_date.strftime('%Y-%m-%d') if revenue.end_date else 'N/A',
            ])
        
        filename = f"budget_revenues_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Budget Revenues Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Budget Revenues Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Budget Revenues Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Budget Revenues Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('budget_revenue_list')
    
    return render(request, 'core/budget_revenue_list.html', {'revenues': revenues})

@user_passes_test(is_admin)
def budget_revenue_add(request):
    if request.method == 'POST':
        form = BudgetRevenueForm(request.POST, request.FILES)
        if form.is_valid():
            revenue = form.save()
            # Handle multiple file attachments
            from .models import BudgetRevenueFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        BudgetRevenueFile.objects.create(
                            budget_revenue=revenue,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            return redirect('budget_revenue_list')
    else:
        form = BudgetRevenueForm()
    return render(request, 'core/budget_revenue_form.html', {'form': form, 'action': 'Add'})

@user_passes_test(is_admin)
def budget_revenue_edit(request, pk):
    revenue = get_object_or_404(BudgetRevenue, pk=pk)
    if request.method == 'POST':
        form = BudgetRevenueForm(request.POST, request.FILES, instance=revenue)
        if form.is_valid():
            form.save()
            # Handle multiple file attachments
            from .models import BudgetRevenueFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        BudgetRevenueFile.objects.create(
                            budget_revenue=revenue,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            return redirect('budget_revenue_list')
    else:
        form = BudgetRevenueForm(instance=revenue)
    return render(request, 'core/budget_revenue_form.html', {'form': form, 'action': 'Edit'})

@user_passes_test(is_admin)
def budget_revenue_delete(request, pk):
    revenue = get_object_or_404(BudgetRevenue, pk=pk)
    if request.method == 'POST':
        revenue.delete()
        return redirect('budget_revenue_list')
    return render(request, 'core/budget_revenue_confirm_delete.html', {'revenue': revenue})

def budget_revenue(request):
    return render(request, 'core/budget_revenue.html')

@user_passes_test(is_admin)
def asset_list(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    assets = Asset.objects.select_related('asset_user').all().order_by('-purchase_date')
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Asset Name', 'Asset ID', 'Brand', 'Model', 'Purchase Date', 'Cost', 'Assigned To', 'Status']
        data = []
        for asset in assets:
            data.append([
                str(asset.id),
                asset.asset_name,
                asset.asset_id,
                asset.brand or 'N/A',
                asset.model or 'N/A',
                asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else 'N/A',
                f"${asset.cost:.2f}" if asset.cost else 'N/A',
                asset.asset_user.user.get_full_name() if asset.asset_user else 'Unassigned',
                asset.get_status_display()
            ])
        
        filename = f"assets_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Assets Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Assets Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Assets Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Assets Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('asset_list')
    
    return render(request, 'core/asset_list.html', {'assets': assets})

@user_passes_test(is_admin)
def asset_add(request):
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save()
            # Handle multiple file attachments
            from .models import AssetFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        AssetFile.objects.create(
                            asset=asset,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            return redirect('asset_list')
    else:
        form = AssetForm()
    return render(request, 'core/asset_form.html', {'form': form, 'action': 'Add'})

@user_passes_test(is_admin)
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('asset_list')
    else:
        form = AssetForm(instance=asset)
    return render(request, 'core/asset_form.html', {'form': form, 'action': 'Edit'})

@user_passes_test(is_admin)
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        asset.delete()
        return redirect('asset_list')
    return render(request, 'core/asset_confirm_delete.html', {'asset': asset})

@user_passes_test(is_admin)
def admin_user_list(request):
    users = User.objects.all().order_by('-date_joined')
    # Calculate statistics
    active_count = users.filter(is_active=True).count()
    staff_count = users.filter(is_staff=True).count()
    admin_count = users.filter(is_superuser=True).count()
    return render(request, 'core/admin_user_list.html', {
        'users': users,
        'active_count': active_count,
        'staff_count': staff_count,
        'admin_count': admin_count,
    })

@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = UserAdminForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, 'User added successfully!')
            return redirect('admin_user_list')
    else:
        form = UserAdminForm()
    return render(request, 'core/add_user.html', {'form': form})

@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, 'User updated successfully!')
            return redirect('admin_user_list')
    else:
        form = UserAdminForm(instance=user)
    return render(request, 'core/add_user.html', {'form': form, 'edit_mode': True, 'user_obj': user})

@user_passes_test(is_admin)
def activate_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = True
    user.save()
    messages.success(request, 'User activated successfully!')
    return redirect('admin_user_list')

@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = False
    user.save()
    messages.success(request, 'User deactivated successfully!')
    return redirect('admin_user_list')

@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully!')
        return redirect('admin_user_list')
    return render(request, 'core/confirm_delete_user.html', {'user_obj': user})

@user_passes_test(is_admin)
def settings_main(request):
    settings_obj, _ = CompanySettings.objects.get_or_create(pk=1)
    
    # Auto-setup Gmail if email settings are empty or update to new email
    if not settings_obj.email_host or settings_obj.email_host_user != 'technologiessbs15@gmail.com':
        settings_obj.email_host = 'smtp.gmail.com'
        settings_obj.email_port = 587
        settings_obj.email_use_tls = True
        settings_obj.email_use_ssl = False
        if not settings_obj.email_host_user or settings_obj.email_host_user == 'it@sbstechnologies.pk':
            settings_obj.email_host_user = 'technologiessbs15@gmail.com'
        settings_obj.email_from_name = 'SBS Technologies HRM'
        settings_obj.save()
    
    if request.method == 'POST':
        # Check if this is a quick setup request
        if 'quick_setup_gmail' in request.POST:
            settings_obj.email_host = 'smtp.gmail.com'
            settings_obj.email_port = 587
            settings_obj.email_use_tls = True
            settings_obj.email_use_ssl = False
            settings_obj.email_host_user = 'technologiessbs15@gmail.com'
            settings_obj.email_from_name = 'SBS Technologies HRM'
            settings_obj.save()
            messages.success(request, 'Gmail settings configured! Now enter your email password and enable email, then save.')
            return redirect('settings_main')
        
        form = CompanySettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Company settings updated successfully!')
                return redirect('settings_main')
            except Exception as e:
                messages.error(request, f'Error saving settings: {str(e)}')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CompanySettingsForm(instance=settings_obj)
        # Ensure email is set if empty
        if not settings_obj.email_host_user or settings_obj.email_host_user == 'it@sbstechnologies.pk':
            settings_obj.email_host_user = 'technologiessbs15@gmail.com'
            settings_obj.save()
            form = CompanySettingsForm(instance=settings_obj)  # Reload form with updated instance
    return render(request, 'core/settings_main.html', {'form': form, 'active_section': 'company', 'settings_obj': settings_obj})

@user_passes_test(is_admin)
def test_email_config(request):
    """Test email configuration by sending a test email"""
    if request.method == 'POST':
        recipient_email = request.POST.get('recipient_email')
        if not recipient_email:
            messages.error(request, 'Please provide a recipient email address.')
            return redirect('settings_main')
        
        from .email_utils import send_test_email
        import traceback
        
        try:
            # Check settings first
            from .models import CompanySettings
            company_settings = CompanySettings.objects.first()
            
            if not company_settings:
                messages.error(request, 'Company settings not found. Please configure company settings first.')
                return redirect('settings_main')
            
            if not company_settings.email_enabled:
                messages.error(request, 'Email is not enabled. Please enable email in settings and save first.')
                return redirect('settings_main')
            
            if not company_settings.email_host_user or not company_settings.email_host_password:
                messages.error(request, 'Email username or password not configured. Please check your email settings.')
                return redirect('settings_main')
            
            success, message = send_test_email(recipient_email)
            
            if success:
                messages.success(request, f'✅ Test email sent successfully to {recipient_email}! Please check the inbox (and spam/junk folder).')
            else:
                # Show the detailed error message
                error_details = message
                
                # Add helpful links and instructions
                help_text = ""
                if "authentication" in message.lower() or "login" in message.lower() or "password" in message.lower():
                    help_text = "<br><br><strong>💡 Solution:</strong> For Gmail, if you have 2-Step Verification enabled, you MUST use an App Password instead of your regular password.<br>Get App Password: <a href='https://myaccount.google.com/apppasswords' target='_blank'>https://myaccount.google.com/apppasswords</a>"
                elif "connection" in message.lower() or "cannot connect" in message.lower():
                    help_text = "<br><br><strong>💡 Solution:</strong> Check your SMTP settings. For Gmail: Host=smtp.gmail.com, Port=587, Use TLS=Yes, Use SSL=No"
                elif "tls" in message.lower() or "ssl" in message.lower():
                    help_text = "<br><br><strong>💡 Solution:</strong> For Gmail with port 587, check 'Use TLS' and uncheck 'Use SSL'. For port 465, check 'Use SSL' and uncheck 'Use TLS'"
                
                messages.error(request, f'❌ Failed to send test email: {error_details}{help_text}', extra_tags='safe')
        except Exception as e:
            error_msg = f"Error sending test email: {str(e)}"
            logger.error(f"Test email error: {error_msg}\n{traceback.format_exc()}")
            messages.error(request, f'❌ Error: {error_msg}. Please check your email settings and try again.')
        
        return redirect('settings_main')
    return redirect('settings_main')

@user_passes_test(is_admin)
def settings_localization(request):
    settings_obj, _ = LocalizationSettings.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = LocalizationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Localization settings updated!')
            return redirect('settings_localization')
    else:
        form = LocalizationSettingsForm(instance=settings_obj)
    return render(request, 'core/settings_localization.html', {'form': form, 'active_section': 'localization'})

@user_passes_test(is_admin)
def settings_invoice(request):
    settings_obj, _ = InvoiceSettings.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = InvoiceSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice settings updated!')
            return redirect('settings_invoice')
    else:
        form = InvoiceSettingsForm(instance=settings_obj)
    return render(request, 'core/settings_invoice.html', {'form': form, 'active_section': 'invoice', 'settings_obj': settings_obj})

@user_passes_test(is_admin)
def settings_salary(request):
    settings_obj, _ = SalarySettings.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = SalarySettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Salary settings updated!')
            return redirect('settings_salary')
    else:
        form = SalarySettingsForm(instance=settings_obj)
    return render(request, 'core/settings_salary.html', {'form': form, 'active_section': 'salary'})

@user_passes_test(is_admin)
def settings_theme(request):
    settings_obj, _ = ThemeSettings.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = ThemeSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Theme settings updated!')
            return redirect('settings_theme')
    else:
        form = ThemeSettingsForm(instance=settings_obj)
    return render(request, 'core/settings_theme.html', {'form': form, 'active_section': 'theme', 'settings_obj': settings_obj})

def theme_settings_context(request):
    from .models import ThemeSettings
    try:
        settings_obj = ThemeSettings.objects.first()
    except Exception:
        settings_obj = None
    return {'theme_settings': settings_obj}

@user_passes_test(is_admin)
def taxes(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    taxes = Tax.objects.all()
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Name', 'Percentage', 'Status']
        data = []
        for tax in taxes:
            data.append([
                str(tax.id),
                tax.name,
                f"{tax.percentage}%",
                'Active' if tax.active else 'Inactive'
            ])
        
        filename = f"taxes_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Taxes Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Taxes Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Taxes Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Taxes Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('taxes')
    
    form = TaxForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('taxes')
    return render(request, 'core/taxes.html', {'taxes': taxes, 'form': form})

@user_passes_test(is_admin)
def expenses(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    expenses = Expense.objects.all().order_by('-purchased_date')
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Item Name', 'Purchased From', 'Purchased Date', 'Amount', 'Paid By', 'Status']
        data = []
        for expense in expenses:
            data.append([
                str(expense.id),
                expense.item_name,
                expense.purchased_from,
                expense.purchased_date.strftime('%Y-%m-%d') if expense.purchased_date else '',
                f"Rs{expense.amount}",
                expense.paid_by,
                expense.get_status_display()
            ])
        
        filename = f"expenses_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Expenses Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Expenses Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Expenses Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Expenses Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('expenses')
    
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('expenses')
    return render(request, 'core/expenses.html', {'expenses': expenses, 'form': form})

@user_passes_test(is_admin)
def estimates(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    estimates = Estimate.objects.all().prefetch_related('items', 'client', 'project').order_by('-estimate_date')
    for estimate in estimates:
        estimate.total_amount = sum(item.amount for item in estimate.items.all())
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Client', 'Project', 'Date', 'Status', 'Total Amount', 'Tax']
        data = []
        for estimate in estimates:
            data.append([
                str(estimate.id),
                estimate.client.name if estimate.client else 'N/A',
                estimate.project.name if estimate.project else 'N/A',
                estimate.estimate_date.strftime('%Y-%m-%d') if estimate.estimate_date else '',
                estimate.get_status_display(),
                f"Rs{estimate.total_amount:.2f}",
                f"{estimate.tax.name} ({estimate.tax.percentage}%)" if estimate.tax else 'N/A'
            ])
        
        filename = f"estimates_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Estimates Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Estimates Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Estimates Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Estimates Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('estimates')
    
    return render(request, 'core/estimates.html', {'estimates': estimates})

@user_passes_test(is_admin)
def invoices(request):
    return render(request, 'core/invoices.html')

@user_passes_test(is_admin)
def invoice_list(request):
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    
    export_format = request.GET.get('format', '')
    invoices = Invoice.objects.all().select_related('client', 'project', 'tax').order_by('-invoice_date')
    for invoice in invoices:
        invoice.total_amount = sum(item.amount for item in invoice.items.all())
    
    # Export if format is specified
    if export_format:
        headers = ['ID', 'Invoice #', 'Client', 'Project', 'Date', 'Due Date', 'Status', 'Total Amount', 'Tax']
        data = []
        for invoice in invoices:
            data.append([
                str(invoice.id),
                f"INV-{invoice.id:06d}",
                invoice.client.name if invoice.client else 'N/A',
                invoice.project.name if invoice.project else 'N/A',
                invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
                invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
                invoice.get_status_display(),
                f"Rs{invoice.total_amount:.2f}",
                f"{invoice.tax.name} ({invoice.tax.percentage}%)" if invoice.tax else 'N/A'
            ])
        
        filename = f"invoices_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, 'Invoices Report', headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, 'Invoices Report', headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, 'Invoices Report', headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, 'Invoices Report', headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('invoices')
    
    return render(request, 'core/invoices.html', {'invoices': invoices})

@user_passes_test(is_admin)
def add_invoice(request):
    InvoiceItemFormSet = inlineformset_factory(Invoice, InvoiceItem, form=InvoiceItemForm, extra=1, can_delete=True)
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            items = formset.save(commit=False)
            for item in items:
                item.invoice = invoice
                item.amount = item.unit_cost * item.quantity
                item.save()
            formset.save_m2m()
            return redirect('invoices')
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()
    return render(request, 'core/add_invoice.html', {'form': form, 'formset': formset})

@user_passes_test(is_admin)
def add_estimate(request):
    EstimateItemFormSet = inlineformset_factory(Estimate, EstimateItem, form=EstimateItemForm, extra=1, can_delete=True)
    if request.method == 'POST':
        form = EstimateForm(request.POST)
        formset = EstimateItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            estimate = form.save()
            items = formset.save(commit=False)
            for item in items:
                item.estimate = estimate
                item.amount = item.unit_cost * item.quantity
                item.save()
            formset.save_m2m()
            return redirect('estimates')
    else:
        form = EstimateForm()
        formset = EstimateItemFormSet()
    return render(request, 'core/add_estimate.html', {'form': form, 'formset': formset})

def edit_tax(request, tax_id):
    tax = get_object_or_404(Tax, id=tax_id)
    if request.method == 'POST':
        form = TaxForm(request.POST, instance=tax)
        if form.is_valid():
            form.save()
            return redirect('taxes')
    else:
        form = TaxForm(instance=tax)
    return render(request, 'core/edit_tax.html', {'form': form, 'tax': tax})

def delete_tax(request, tax_id):
    tax = get_object_or_404(Tax, id=tax_id)
    if request.method == 'POST':
        tax.delete()
        return redirect('taxes')
    return render(request, 'core/delete_tax.html', {'tax': tax})

def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expenses')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'core/edit_expense.html', {'form': form, 'expense': expense})

def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        expense.delete()
        return redirect('expenses')
    return render(request, 'core/delete_expense.html', {'expense': expense})

def edit_estimate(request, estimate_id):
    estimate = get_object_or_404(Estimate, id=estimate_id)
    EstimateItemFormSet = inlineformset_factory(Estimate, EstimateItem, form=EstimateItemForm, extra=0, can_delete=True)
    if request.method == 'POST':
        form = EstimateForm(request.POST, instance=estimate)
        formset = EstimateItemFormSet(request.POST, instance=estimate)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('estimates')
    else:
        form = EstimateForm(instance=estimate)
        formset = EstimateItemFormSet(instance=estimate)
    return render(request, 'core/edit_estimate.html', {'form': form, 'formset': formset, 'estimate': estimate})

def delete_estimate(request, estimate_id):
    estimate = get_object_or_404(Estimate, id=estimate_id)
    if request.method == 'POST':
        estimate.delete()
        return redirect('estimates')
    return render(request, 'core/delete_estimate.html', {'estimate': estimate})

def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    InvoiceItemFormSet = inlineformset_factory(Invoice, InvoiceItem, form=InvoiceItemForm, extra=0, can_delete=True)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('invoices')
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice)
    return render(request, 'core/edit_invoice.html', {'form': form, 'formset': formset, 'invoice': invoice})

def delete_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        invoice.delete()
        return redirect('invoices')
    return render(request, 'core/delete_invoice.html', {'invoice': invoice})

@login_required
def permissions(request):
    is_admin = request.user.is_superuser
    from .models import Employee
    if is_admin:
        employees = Employee.objects.select_related('user').all()
    else:
        employees = Employee.objects.select_related('user').filter(user=request.user)
    
    # EmployeePermission model is not implemented yet
    return render(request, 'core/permissions.html', {
        'employees': employees,
        'modules': [],
        'actions': [],
        'permissions': {},
        'is_admin': is_admin,
    })

@staff_member_required
def permissions_management(request):
    from .models import Employee
    features = [
        ('can_view_attendance', 'Attendance'),
        ('can_view_tasks', 'Tasks'),
        ('can_view_department', 'Department'),
        ('can_view_designation', 'Designation'),
        ('can_view_holidays', 'Holidays'),
        ('can_view_leaves', 'Leaves'),
    ]
    employees = Employee.objects.select_related('user', 'department', 'designation').all().order_by('user__first_name', 'user__last_name')
    
    # Calculate permission counts for each employee
    employee_permissions = {}
    for employee in employees:
        count = 0
        for field, _ in features:
            if getattr(employee, field, False):
                count += 1
        employee_permissions[employee.id] = count
    
    if request.method == 'POST':
        for employee in employees:
            for field, _ in features:
                key = f"{employee.id}_{field}"
                value = request.POST.get(key) == 'on'
                setattr(employee, field, value)
            employee.save()
        messages.success(request, 'Permissions updated successfully!')
        return redirect('permissions_management')
    return render(request, 'core/permissions.html', {
        'employees': employees,
        'features': features,
        'employee_permissions': employee_permissions,
    })

# ===================== PAYROLL =====================

def _render_payslip_pdf_to_bytes(payslip, items, context_extra=None):
    from reportlab.lib import colors
    from reportlab.lib.units import mm, inch
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    # Get currency symbol from settings
    try:
        from .models import LocalizationSettings
        loc_settings = LocalizationSettings.objects.first()
        currency_symbol = loc_settings.currency_symbol if loc_settings else '$'
    except:
        currency_symbol = '$'
    from reportlab.pdfgen import canvas
    from datetime import datetime
    from reportlab.lib.colors import HexColor
    
    base_salary = 0
    unpaid_leave_deduction = 0
    tax_amount = 0
    loan_installment_total = 0
    late_deduction = 0
    
    if context_extra:
        base_salary = float(context_extra.get('base_salary', 0))
        unpaid_leave_deduction = float(context_extra.get('unpaid_leave_deduction', 0))
        tax_amount = float(context_extra.get('tax_amount', 0))
        loan_installment_total = float(context_extra.get('loan_installment_total', 0))
        late_deduction = float(context_extra.get('late_deduction', 0))
    
    # Get company settings
    try:
        company_settings = CompanySettings.objects.first()
    except:
        company_settings = None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           topMargin=8*mm, bottomMargin=10*mm,
                           leftMargin=12*mm, rightMargin=12*mm)
    story = []
    styles = getSampleStyleSheet()
    
    # Import Image for logo
    from reportlab.platypus import Image
    
    # Custom styles - Reduced sizes for single page
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=2,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=20
    )
    
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HexColor('#2c3e50'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=1
    )
    
    company_info_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=0.5
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#ffffff'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#666666'),
        fontName='Helvetica-Bold',
        spaceAfter=0
    )
    
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=0
    )
    
    # Company Header with Logo
    company_name = company_settings.company_name if company_settings else "COMPANY NAME"
    company_address = company_settings.address if company_settings else ""
    company_phone = company_settings.phone_number if company_settings else ""
    company_email = company_settings.email if company_settings else ""
    company_city = company_settings.city if company_settings else ""
    company_country = company_settings.country if company_settings else ""
    
    # Logo handling
    logo_path = None
    if company_settings and company_settings.logo:
        try:
            logo_path = company_settings.logo.path
        except:
            logo_path = None
    
    # Header with Logo and Company Info
    if logo_path:
        try:
            logo_img = Image(logo_path, width=40*mm, height=15*mm, kind='proportional')
        except:
            logo_img = None
    else:
        logo_img = None
    
    # Create header table with logo on left, company info on right
    company_info_text = f"<b>{company_name}</b><br/>"
    if company_address:
        company_info_text += f"{company_address}<br/>"
    if company_city and company_country:
        company_info_text += f"{company_city}, {company_country}<br/>"
    elif company_city:
        company_info_text += f"{company_city}<br/>"
    if company_phone:
        company_info_text += f"Tel: {company_phone}<br/>"
    if company_email:
        company_info_text += f"Email: {company_email}"
    
    # Header table: Logo left, Company info right
    if logo_img:
        # Two column layout with logo
        company_info_para = Paragraph(company_info_text, ParagraphStyle('CompanyInfoAll', parent=company_info_style, alignment=TA_CENTER))
        header_data = [[logo_img, company_info_para]]
        header_table = Table(header_data, colWidths=[50*mm, 140*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (0, 0), 5),
            ('RIGHTPADDING', (0, 0), (0, 0), 5),
            ('LEFTPADDING', (1, 0), (1, 0), 5),
            ('RIGHTPADDING', (1, 0), (1, 0), 5),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
            ('BOX', (0, 0), (-1, -1), 1.5, HexColor('#2c3e50')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, HexColor('#2c3e50')),
        ]))
    else:
        # Single column layout without logo
        header_data = [[Paragraph(company_info_text, ParagraphStyle('CompanyInfoAll', parent=company_info_style, alignment=TA_CENTER))]]
        header_table = Table(header_data, colWidths=[doc.width])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
            ('BOX', (0, 0), (-1, -1), 1.5, HexColor('#2c3e50')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, HexColor('#2c3e50')),
        ]))
    story.append(header_table)
    story.append(Spacer(1, 3*mm))
    
    # Title
    story.append(Paragraph("SALARY PAYSLIP", title_style))
    story.append(Spacer(1, 3*mm))
    
    # Employee and Payslip Info Side by Side
    employee = payslip.employee
    emp_name = employee.user.get_full_name() or employee.user.username
    emp_designation = str(employee.designation) if employee.designation else "N/A"
    emp_department = str(employee.department) if employee.department else "N/A"
    emp_id = f"EMP-{employee.id:04d}"
    emp_email = employee.user.email or "N/A"
    emp_phone = employee.phone or "N/A"
    
    period_start_str = payslip.period_start.strftime('%B %d, %Y') if payslip.period_start else 'N/A'
    period_end_str = payslip.period_end.strftime('%B %d, %Y') if payslip.period_end else 'N/A'
    payment_date_str = payslip.date.strftime('%B %d, %Y')
    
    # Two Column Layout - Employee and Payslip Info
    info_data = [
        [Paragraph("<b>EMPLOYEE INFORMATION</b>", section_title_style), Paragraph("<b>PAYSLIP INFORMATION</b>", section_title_style)],
        [f"Employee Name: {emp_name}", f"Payslip No.: PSL-{payslip.id:06d}"],
        [f"Employee ID: {emp_id}", f"Pay Period: {period_start_str} to {period_end_str}"],
        [f"Designation: {emp_designation}", f"Payment Date: {payment_date_str}"],
        [f"Department: {emp_department}", f"Status: {payslip.get_status_display().upper()}"],
        [f"Email: {emp_email}", ''],
        [f"Phone: {emp_phone}", ''],
    ]
    
    info_table = Table(info_data, colWidths=[95*mm, 95*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#2c3e50')),
        ('BACKGROUND', (0, 1), (0, -1), HexColor('#ffffff')),
        ('BACKGROUND', (1, 1), (1, -1), HexColor('#ffffff')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))
    
    # Earnings Section with Professional Form Style
    earnings_data = [[Paragraph("<b>EARNINGS</b>", section_title_style), '']]
    earnings_total = 0
    
    # Base Salary
    if base_salary > 0:
        earnings_data.append([Paragraph("Base Salary", value_style), Paragraph(f"{currency_symbol}{base_salary:,.2f}", value_style)])
        earnings_total += base_salary
    
    # Additional Earnings
    for item in items:
        if item.item_type == PayrollItem.EARNING:
            amount = float(item.amount)
            earnings_data.append([Paragraph(item.name, value_style), Paragraph(f"{currency_symbol}{amount:,.2f}", value_style)])
            earnings_total += amount
    
    if len(earnings_data) == 1:
        earnings_data.append([Paragraph("No additional earnings", value_style), Paragraph(f'{currency_symbol}0.00', value_style)])
    
    earnings_data.append([Paragraph("<b>TOTAL EARNINGS</b>", ParagraphStyle('BoldTotal', parent=value_style, fontName='Helvetica-Bold', fontSize=9)), 
                         Paragraph(f"<b>{currency_symbol}{earnings_total:,.2f}</b>", ParagraphStyle('BoldTotal', parent=value_style, fontName='Helvetica-Bold', fontSize=9))])
    
    earnings_table = Table(earnings_data, colWidths=[140*mm, 50*mm])
    earnings_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#2c3e50')),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#e9ecef')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, HexColor('#2c3e50')),
    ]))
    story.append(earnings_table)
    story.append(Spacer(1, 4*mm))
    
    # Deductions Section with Professional Form Style
    deductions_data = [[Paragraph("<b>DEDUCTIONS</b>", section_title_style), '']]
    deductions_total = 0
    
    # Tax
    if tax_amount > 0:
        deductions_data.append([Paragraph("Income Tax", value_style), Paragraph(f"{currency_symbol}{tax_amount:,.2f}", value_style)])
        deductions_total += tax_amount
    
    # Loan Installments
    if loan_installment_total > 0:
        deductions_data.append([Paragraph("Loan Repayment", value_style), Paragraph(f"{currency_symbol}{loan_installment_total:,.2f}", value_style)])
        deductions_total += loan_installment_total
    
    # Unpaid Leaves
    if unpaid_leave_deduction > 0:
        deductions_data.append([Paragraph("Unpaid Leave Deduction", value_style), Paragraph(f"{currency_symbol}{unpaid_leave_deduction:,.2f}", value_style)])
        deductions_total += unpaid_leave_deduction
    
    # Late Deduction
    if late_deduction > 0:
        deductions_data.append([Paragraph("Late Arrival Deduction", value_style), Paragraph(f"{currency_symbol}{late_deduction:,.2f}", value_style)])
        deductions_total += late_deduction
    
    # Additional Deductions
    for item in items:
        if item.item_type == PayrollItem.DEDUCTION:
            amount = float(item.amount)
            deductions_data.append([Paragraph(item.name, value_style), Paragraph(f"{currency_symbol}{amount:,.2f}", value_style)])
            deductions_total += amount
    
    if len(deductions_data) == 1:
        deductions_data.append([Paragraph("No deductions", value_style), Paragraph(f'{currency_symbol}0.00', value_style)])
    
    deductions_data.append([Paragraph("<b>TOTAL DEDUCTIONS</b>", ParagraphStyle('BoldTotal', parent=value_style, fontName='Helvetica-Bold', fontSize=9)), 
                            Paragraph(f"<b>{currency_symbol}{deductions_total:,.2f}</b>", ParagraphStyle('BoldTotal', parent=value_style, fontName='Helvetica-Bold', fontSize=9))])
    
    deductions_table = Table(deductions_data, colWidths=[140*mm, 50*mm])
    deductions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#2c3e50')),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#e9ecef')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, HexColor('#2c3e50')),
    ]))
    story.append(deductions_table)
    story.append(Spacer(1, 4*mm))
    
    # Summary Section with Professional Form Style
    gross_pay = float(payslip.gross_pay) if payslip.gross_pay else earnings_total
    net_pay = float(payslip.total) if payslip.total else (gross_pay - deductions_total)
    
    summary_data = [
        [Paragraph("<b>PAYMENT SUMMARY</b>", section_title_style), ''],
        [Paragraph("Gross Pay:", ParagraphStyle('SummaryLabel', parent=value_style, fontName='Helvetica-Bold', fontSize=9)), 
         Paragraph(f"{currency_symbol}{gross_pay:,.2f}", value_style)],
        [Paragraph("Total Deductions:", ParagraphStyle('SummaryLabel', parent=value_style, fontName='Helvetica-Bold', fontSize=9)), 
         Paragraph(f"{currency_symbol}{deductions_total:,.2f}", value_style)],
        ['', ''],
        [Paragraph("<b>NET PAY</b>", ParagraphStyle('NetPayLabel', parent=value_style, fontName='Helvetica-Bold', fontSize=12, textColor=HexColor('#28a745'))), 
         Paragraph(f"<b>{currency_symbol}{net_pay:,.2f}</b>", ParagraphStyle('NetPayValue', parent=value_style, fontName='Helvetica-Bold', fontSize=13, textColor=HexColor('#28a745')))],
    ]
    
    summary_table = Table(summary_data, colWidths=[140*mm, 50*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
        ('BOX', (0, 0), (-1, -1), 1.5, HexColor('#2c3e50')),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#d4edda')),
        ('LINEABOVE', (0, -2), (-1, -2), 2, HexColor('#2c3e50')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 5*mm))
    
    # Signature Section
    signature_data = [
        ['', ''],
        [Paragraph("_________________________", ParagraphStyle('Signature', parent=value_style, alignment=TA_CENTER)), 
         Paragraph("_________________________", ParagraphStyle('Signature', parent=value_style, alignment=TA_CENTER))],
        [Paragraph("Employee Signature", ParagraphStyle('SignatureLabel', parent=value_style, fontSize=8, alignment=TA_CENTER)), 
         Paragraph("Authorized Signature", ParagraphStyle('SignatureLabel', parent=value_style, fontSize=8, alignment=TA_CENTER))],
    ]
    
    signature_table = Table(signature_data, colWidths=[95*mm, 95*mm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(signature_table)
    story.append(Spacer(1, 2*mm))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=HexColor('#888888'),
        alignment=TA_CENTER,
        spaceBefore=2
    )
    
    footer_text = f"This is a computer-generated payslip. Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    if company_settings and company_settings.contact_person:
        footer_text += f" | For queries, contact: {company_settings.contact_person}"
    if company_settings and company_settings.phone_number:
        footer_text += f" | Tel: {company_settings.phone_number}"
    
    story.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

@user_passes_test(is_admin)
def payroll_items(request):
    items = PayrollItem.objects.select_related('employee__user').order_by('-date')
    if request.method == 'POST':
        form = PayrollItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payroll_items')
    else:
        form = PayrollItemForm()
    return render(request, 'core/payroll_items.html', {'items': items, 'form': form})

@user_passes_test(is_admin)
def edit_payroll_item(request, item_id):
    item = get_object_or_404(PayrollItem, id=item_id)
    if request.method == 'POST':
        form = PayrollItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('payroll_items')
    else:
        form = PayrollItemForm(instance=item)
    return render(request, 'core/edit_payroll_item.html', {'form': form})

@user_passes_test(is_admin)
def delete_payroll_item(request, item_id):
    item = get_object_or_404(PayrollItem, id=item_id)
    if request.method == 'POST':
        item.delete()
        return redirect('payroll_items')
    return HttpResponse(status=405)

@user_passes_test(is_admin)
def admin_payslips(request):
    payslips = Payslip.objects.select_related('employee__user').order_by('-created_at')
    if request.method == 'POST':
        form = PayslipCreateForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            period_start = form.cleaned_data['period_start']
            period_end = form.cleaned_data['period_end']
            send_email = form.cleaned_data['send_email']
            form_base_salary = form.cleaned_data.get('base_salary')

            # Sum payroll items for the period, including recurring items that overlap period
            period_items = PayrollItem.objects.filter(employee=employee).filter(
                (
                    Q(is_recurring=False) & Q(date__gte=period_start, date__lte=period_end)
                ) | (
                    Q(is_recurring=True) & (
                        (Q(start_date__lte=period_end) | Q(start_date__isnull=True)) & (Q(end_date__gte=period_start) | Q(end_date__isnull=True))
                    )
                )
            )
            total_earnings = period_items.filter(item_type=PayrollItem.EARNING).aggregate(s=Sum('amount'))['s'] or 0
            total_deductions = period_items.filter(item_type=PayrollItem.DEDUCTION).aggregate(s=Sum('amount'))['s'] or 0

            base_salary = form_base_salary if form_base_salary is not None else (employee.salary or 0)

            # Late policy: 3 lates = 1 day salary deduction
            late_days = Attendance.objects.filter(employee=employee, date__gte=period_start, date__lte=period_end, is_late=True).count()
            late_day_equivalents = late_days // 3
            late_deduction = 0
            if base_salary and late_day_equivalents:
                late_deduction = round((float(base_salary) / 30.0) * late_day_equivalents, 2)
                total_deductions += late_deduction

            # Unpaid leave deduction from attendance
            absent_days = Attendance.objects.filter(employee=employee, date__gte=period_start, date__lte=period_end, status='absent').count()
            unpaid_leave_deduction = 0
            if base_salary and absent_days:
                unpaid_leave_deduction = round((base_salary / 30) * absent_days, 2)
                total_deductions += unpaid_leave_deduction

            # Tax Slab
            taxable_income = float(base_salary) + float(total_earnings)
            slab = TaxSlab.objects.order_by('min_income').filter(min_income__lte=taxable_income).filter(
                Q(max_income__gte=taxable_income) | Q(max_income__isnull=True)
            ).first()
            tax_amount = 0
            if slab:
                tax_amount = round((taxable_income * float(slab.rate_percent) / 100.0) + float(slab.fixed_deduction), 2)
                if tax_amount > 0:
                    total_deductions += tax_amount

            # Loan repayments
            loan_installment_total = 0
            active_loans = Loan.objects.filter(employee=employee, is_active=True)
            for loan in active_loans:
                if float(loan.balance) > 0 and float(loan.monthly_installment) > 0:
                    installment = float(loan.monthly_installment)
                    if installment > float(loan.balance):
                        installment = float(loan.balance)
                    loan_installment_total += installment
            if loan_installment_total:
                total_deductions += loan_installment_total

            gross_pay = float(base_salary) + float(total_earnings)
            net_total = gross_pay - float(total_deductions)

            payslip = Payslip.objects.create(
                employee=employee,
                date=timezone.now().date(),
                period_start=period_start,
                period_end=period_end,
                gross_pay=gross_pay,
                total_earnings=total_earnings,
                total_deductions=total_deductions,
                total=net_total,
                created_by=request.user,
                status=Payslip.STATUS_PROCESSED,
            )

            # Generate PDF
            pdf_bytes = _render_payslip_pdf_to_bytes(
                payslip,
                period_items,
                context_extra={
                    'base_salary': base_salary,
                    'unpaid_leave_deduction': unpaid_leave_deduction,
                    'late_deduction': late_deduction,
                    'tax_amount': tax_amount,
                    'loan_installment_total': loan_installment_total,
                }
            )
            filename = f"payslip_{employee.user.username}_{period_start}_{period_end}.pdf"
            payslip.pdf.save(filename, ContentFile(pdf_bytes))
            payslip.save()

            # Optional email delivery
            if send_email and employee.user.email:
                try:
                    email = EmailMessage(
                        subject=f"Payslip {period_start} - {period_end}",
                        body="Please find your payslip attached.",
                        to=[employee.user.email],
                    )
                    email.attach(filename, pdf_bytes, 'application/pdf')
                    email.send(fail_silently=True)
                except Exception:
                    pass

            return redirect('admin_payslips')
    else:
        form = PayslipCreateForm()
    return render(request, 'core/admin_payslips.html', {'payslips': payslips, 'form': form})

@user_passes_test(is_admin)
def edit_payslip(request, payslip_id):
    payslip = get_object_or_404(Payslip, id=payslip_id)
    redirect_to = request.GET.get('redirect_to') or request.POST.get('redirect_to', 'admin_payslips')
    if request.method == 'POST':
        form = PayslipEditForm(request.POST, instance=payslip)
        if form.is_valid():
            form.save()
            if redirect_to == 'register' and payslip.period_start and payslip.period_end:
                return redirect('monthly_payroll_register', month=payslip.period_start.month, year=payslip.period_start.year)
            return redirect(redirect_to)
    else:
        form = PayslipEditForm(instance=payslip)
    return render(request, 'core/edit_payslip.html', {'form': form, 'payslip': payslip, 'redirect_to': redirect_to})

@user_passes_test(is_admin)
def edit_payslip_register(request, payslip_id):
    """Edit all payslip amounts as shown in the register"""
    from calendar import monthrange
    from datetime import date
    
    payslip = get_object_or_404(Payslip, id=payslip_id)
    employee = payslip.employee
    redirect_to = request.GET.get('redirect_to', 'register')
    
    # Get period dates
    period_start = payslip.period_start or date.today()
    period_end = payslip.period_end or date.today()
    
    # Get current register data
    attendances = Attendance.objects.filter(
        employee=employee,
        date__gte=period_start,
        date__lte=period_end
    )
    work_days = attendances.filter(status='present').count()
    absences = attendances.filter(status='absent').count()
    
    # Get leaves
    leaves = Leave.objects.filter(
        employee=employee,
        status='approved',
        start_date__lte=period_end,
        end_date__gte=period_start
    )
    leave_days = 0
    for leave in leaves:
        overlap_start = max(leave.start_date, period_start)
        overlap_end = min(leave.end_date, period_end)
        if overlap_start <= overlap_end:
            leave_days += (overlap_end - overlap_start).days + 1
    
    # Get payroll items
    period_items = PayrollItem.objects.filter(employee=employee).filter(
        (
            Q(is_recurring=False) & Q(date__gte=period_start, date__lte=period_end)
        ) | (
            Q(is_recurring=True) & (
                (Q(start_date__lte=period_end) | Q(start_date__isnull=True)) & 
                (Q(end_date__gte=period_start) | Q(end_date__isnull=True))
            )
        )
    )
    
    # Calculate current values
    base_pay = float(employee.salary or 0)
    basic_salary = base_pay
    if work_days > 0:
        days_of_month = monthrange(period_start.year, period_start.month)[1]
        per_day_salary = base_pay / days_of_month
        basic_salary = base_pay - (per_day_salary * absences)
    
    # Calculate allowances
    allowance_fuel = 0
    allowance_mobile = 0
    allowance_other = 0
    
    for item in period_items.filter(item_type=PayrollItem.EARNING):
        amount = float(item.amount)
        if 'fuel' in item.name.lower():
            allowance_fuel += amount
        elif 'mobile' in item.name.lower():
            allowance_mobile += amount
        else:
            allowance_other += amount
    
    # Calculate deductions
    deduction_add = 0
    deduction_ded = 0
    deduction_other = 0
    
    for item in period_items.filter(item_type=PayrollItem.DEDUCTION):
        amount = float(item.amount)
        if 'add' in item.name.lower() or 'advance' in item.name.lower():
            deduction_add += amount
        elif 'ded' in item.name.lower() or 'deduction' in item.name.lower():
            deduction_ded += amount
        else:
            deduction_other += amount
    
    opening_balance = 0
    closing_balance = opening_balance + deduction_add - deduction_ded
    gross_pay = float(payslip.gross_pay or 0)
    net_pay = float(payslip.total or 0)
    
    if request.method == 'POST':
        form = PayslipRegisterEditForm(request.POST)
        if form.is_valid():
            # Update payslip amounts
            payslip.gross_pay = form.cleaned_data['gross_pay']
            payslip.total_earnings = form.cleaned_data['allowance_fuel'] + form.cleaned_data['allowance_mobile'] + form.cleaned_data['allowance_other']
            payslip.total_deductions = form.cleaned_data['deduction_add'] + form.cleaned_data['deduction_ded'] + form.cleaned_data['deduction_other']
            payslip.total = form.cleaned_data['net_pay']
            payslip.date = form.cleaned_data['date']
            payslip.period_start = form.cleaned_data.get('period_start') or payslip.period_start
            payslip.period_end = form.cleaned_data.get('period_end') or payslip.period_end
            payslip.status = form.cleaned_data['status']
            payslip.save()
            
            # Optionally update employee salary if base_pay changed
            new_base_pay = form.cleaned_data['base_pay']
            if new_base_pay != base_pay:
                employee.salary = new_base_pay
                employee.save()
            
            messages.success(request, 'Payslip updated successfully!')
            if redirect_to == 'register' and payslip.period_start and payslip.period_end:
                return redirect('monthly_payroll_register', month=payslip.period_start.month, year=payslip.period_start.year)
            return redirect('admin_payslips')
    else:
        # Initialize form with current values
        form = PayslipRegisterEditForm(initial={
            'base_pay': base_pay,
            'work_days': work_days,
            'absences': absences,
            'leaves': leave_days,
            'basic_salary': basic_salary,
            'allowance_fuel': allowance_fuel,
            'allowance_mobile': allowance_mobile,
            'allowance_other': allowance_other,
            'gross_pay': gross_pay,
            'opening_balance': opening_balance,
            'deduction_add': deduction_add,
            'deduction_ded': deduction_ded,
            'deduction_other': deduction_other,
            'closing_balance': closing_balance,
            'net_pay': net_pay,
            'date': payslip.date,
            'period_start': payslip.period_start,
            'period_end': payslip.period_end,
            'status': payslip.status,
        })
    
    context = {
        'form': form,
        'payslip': payslip,
        'employee': employee,
        'redirect_to': redirect_to,
    }
    return render(request, 'core/edit_payslip_register.html', context)

@user_passes_test(is_admin)
def delete_payslip(request, payslip_id):
    payslip = get_object_or_404(Payslip, id=payslip_id)
    if request.method == 'POST':
        payslip.delete()
        return redirect('admin_payslips')
    return render(request, 'core/delete_payslip.html', {'payslip': payslip})

@login_required
def my_payslips(request):
    try:
        employee = request.user.employee
    except Exception:
        return HttpResponse('Not an employee', status=403)
    payslips = Payslip.objects.filter(employee=employee).order_by('-created_at')
    return render(request, 'core/employee_payslips.html', {'payslips': payslips})

@login_required
def view_payslip_detail(request, payslip_id):
    """View detailed payslip information"""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    # Check if user has permission to view this payslip
    if not request.user.is_superuser and payslip.employee.user != request.user:
        messages.error(request, "You don't have permission to view this payslip.")
        return redirect('my_payslips' if not request.user.is_superuser else 'admin_payslips')
    
    # Get payroll items
    items = PayrollItem.objects.filter(employee=payslip.employee).order_by('-date', 'item_type')
    
    # Get context extra data if available
    from .models import TaxSlab, Loan
    
    # Calculate base salary
    base_salary = float(payslip.employee.salary) if payslip.employee.salary else 0
    
    # Calculate tax
    tax_amount = 0
    if payslip.period_start and payslip.period_end:
        taxable_income = float(payslip.gross_pay) if payslip.gross_pay else base_salary
        slab = TaxSlab.objects.filter(
            min_income__lte=taxable_income
        ).filter(
            Q(max_income__gte=taxable_income) | Q(max_income__isnull=True)
        ).first()
        if slab:
            tax_amount = round((taxable_income * float(slab.rate_percent) / 100.0) + float(slab.fixed_deduction), 2)
    
    # Calculate loan installments
    loan_installment_total = 0
    loans = Loan.objects.filter(employee=payslip.employee, is_active=True)
    for loan in loans:
        if float(loan.balance) > 0 and float(loan.monthly_installment) > 0:
            installment = float(loan.monthly_installment)
            if installment > float(loan.balance):
                installment = float(loan.balance)
            loan_installment_total += installment
    
    # Get earnings and deductions
    earnings = [item for item in items if item.item_type == PayrollItem.EARNING]
    deductions = [item for item in items if item.item_type == PayrollItem.DEDUCTION]
    
    context = {
        'payslip': payslip,
        'base_salary': base_salary,
        'earnings': earnings,
        'deductions': deductions,
        'tax_amount': tax_amount,
        'loan_installment_total': loan_installment_total,
        'total_earnings': float(payslip.total_earnings) + base_salary,
        'total_deductions': float(payslip.total_deductions),
        'gross_pay': float(payslip.gross_pay) if payslip.gross_pay else (float(payslip.total_earnings) + base_salary),
        'net_pay': float(payslip.total) if payslip.total else 0,
    }
    
    return render(request, 'core/view_payslip_detail.html', context)

@user_passes_test(is_admin)
def tax_slabs(request):
    slabs = TaxSlab.objects.all().order_by('min_income')
    form = TaxSlabForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tax slab added successfully!')
        return redirect('tax_slabs')
    return render(request, 'core/tax_slabs.html', {'slabs': slabs, 'form': form})

@user_passes_test(is_admin)
def edit_tax_slab(request, slab_id):
    slab = get_object_or_404(TaxSlab, id=slab_id)
    if request.method == 'POST':
        form = TaxSlabForm(request.POST, instance=slab)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tax slab updated successfully!')
            return redirect('tax_slabs')
    else:
        form = TaxSlabForm(instance=slab)
    return render(request, 'core/edit_tax_slab.html', {'form': form, 'slab': slab})

@user_passes_test(is_admin)
def delete_tax_slab(request, slab_id):
    slab = get_object_or_404(TaxSlab, id=slab_id)
    if request.method == 'POST':
        slab_name = slab.name
        slab.delete()
        messages.success(request, f'Tax slab "{slab_name}" deleted successfully!')
        return redirect('tax_slabs')
    return render(request, 'core/delete_tax_slab.html', {'slab': slab})

@user_passes_test(is_admin)
def loans(request):
    loans_qs = Loan.objects.select_related('employee__user').all()
    form = LoanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        loan = form.save()
        messages.success(request, 'Loan added successfully!')
        return redirect('loans')
    
    # Calculate stats
    total_loans = loans_qs.count()
    active_loans = loans_qs.filter(is_active=True).count()
    total_principal = sum(loan.principal_amount for loan in loans_qs)
    
    return render(request, 'core/loans.html', {
        'loans': loans_qs, 
        'form': form,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'total_principal': total_principal
    })

@user_passes_test(is_admin)
def edit_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan updated successfully!')
            return redirect('loans')
    else:
        form = LoanForm(instance=loan)
    return render(request, 'core/edit_loan.html', {'form': form, 'loan': loan})

@user_passes_test(is_admin)
def delete_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    if request.method == 'POST':
        employee_name = loan.employee.user.get_full_name() or loan.employee.user.username
        loan.delete()
        messages.success(request, f'Loan for {employee_name} deleted successfully!')
        return redirect('loans')
    return render(request, 'core/delete_loan.html', {'loan': loan})

@user_passes_test(is_admin)
def monthly_payroll_create(request):
    """Monthly payroll creation form and processing"""
    from calendar import monthrange
    from datetime import date
    
    # Get selected city from GET parameter
    selected_city_get = request.GET.get('city', None)
    
    # Get all unique cities from employees for display
    all_cities = Employee.objects.exclude(city__isnull=True).exclude(city='').values_list('city', flat=True).distinct().order_by('city')
    
    # Get selected department from GET parameter (before form initialization)
    selected_department_get = request.GET.get('department', None)
    
    # Initialize form with city filter if provided
    form = MonthlyPayrollForm(request.POST or None, city_filter=selected_city_get)
    
    # Set initial department value if provided in GET
    if selected_department_get and not request.POST:
        try:
            form.initial['department'] = selected_department_get
        except:
            pass
    
    # Set default values
    if not request.POST:
        today = timezone.now().date()
        form.initial = {
            'month': today.month,
            'year': today.year,
            'days_of_month': monthrange(today.year, today.month)[1],
        }
        # Set city from GET parameter or company settings
        if selected_city_get:
            form.initial['city'] = selected_city_get
        else:
            try:
                settings_obj = CompanySettings.objects.first()
                if settings_obj and settings_obj.city:
                    form.initial['city'] = settings_obj.city
            except:
                pass
    
    # Get employees count for display (before filtering)
    total_employees_all = Employee.objects.count()
    
    if request.method == 'POST' and form.is_valid():
        city = form.cleaned_data['city']
        department = form.cleaned_data.get('department')
        month = int(form.cleaned_data['month'])
        year = int(form.cleaned_data['year'])
        days_of_month = int(form.cleaned_data['days_of_month'])
        
        # Calculate period dates
        period_start = date(year, month, 1)
        period_end = date(year, month, days_of_month)
        
        # Get employees - filter by city and/or department if selected
        employees = Employee.objects.select_related('user', 'designation', 'company', 'department').all()
        if city:
            employees = employees.filter(city=city)
        if department:
            employees = employees.filter(department=department)
        
        # Count employees that already have payslips for this period
        existing_payslips = Payslip.objects.filter(
            period_start=period_start,
            period_end=period_end
        ).values_list('employee_id', flat=True)
        
        employees_to_process = employees.exclude(id__in=existing_payslips)
        employees_count = employees_to_process.count()
        total_employees = employees.count()
        
        # Process payroll for all employees
        created_count = 0
        for employee in employees_to_process:
            try:
                # Calculate attendance-based values
                attendances = Attendance.objects.filter(
                    employee=employee,
                    date__gte=period_start,
                    date__lte=period_end
                )
                
                # Work days = present days
                work_days = attendances.filter(status='present').count()
                
                # Absences
                absences = attendances.filter(status='absent').count()
                
                # Leaves (approved leaves from Leave model)
                leaves = Leave.objects.filter(
                    employee=employee,
                    status='approved',
                    start_date__lte=period_end,
                    end_date__gte=period_start
                )
                leave_days = 0
                for leave in leaves:
                    # Calculate overlapping days
                    overlap_start = max(leave.start_date, period_start)
                    overlap_end = min(leave.end_date, period_end)
                    if overlap_start <= overlap_end:
                        leave_days += (overlap_end - overlap_start).days + 1
                
                # Base salary calculation
                base_pay = float(employee.salary or 0)
                basic_salary = base_pay
                
                # Adjust for absences and leaves (if unpaid)
                if work_days > 0 and days_of_month > 0:
                    # Calculate per day salary
                    per_day_salary = base_pay / days_of_month
                    # Deduct for absences
                    basic_salary = base_pay - (per_day_salary * absences)
                else:
                    basic_salary = 0
                
                # Get payroll items for the period
                period_items = PayrollItem.objects.filter(employee=employee).filter(
                    (
                        Q(is_recurring=False) & Q(date__gte=period_start, date__lte=period_end)
                    ) | (
                        Q(is_recurring=True) & (
                            (Q(start_date__lte=period_end) | Q(start_date__isnull=True)) & 
                            (Q(end_date__gte=period_start) | Q(end_date__isnull=True))
                        )
                    )
                )
                
                # Calculate allowances (Fuel, Mobile, Other)
                allowance_fuel = 0
                allowance_mobile = 0
                allowance_other = 0
                total_earnings = 0
                
                for item in period_items.filter(item_type=PayrollItem.EARNING):
                    amount = float(item.amount)
                    total_earnings += amount
                    # Categorize allowances
                    if 'fuel' in item.name.lower():
                        allowance_fuel += amount
                    elif 'mobile' in item.name.lower():
                        allowance_mobile += amount
                    else:
                        allowance_other += amount
                
                # Calculate deductions
                deduction_add = 0
                deduction_ded = 0
                deduction_other = 0
                total_deductions = 0
                
                for item in period_items.filter(item_type=PayrollItem.DEDUCTION):
                    amount = float(item.amount)
                    total_deductions += amount
                    # Categorize deductions
                    if 'add' in item.name.lower() or 'advance' in item.name.lower():
                        deduction_add += amount
                    elif 'ded' in item.name.lower() or 'deduction' in item.name.lower():
                        deduction_ded += amount
                    else:
                        deduction_other += amount
                
                # Late policy: 3 lates = 1 day salary deduction
                late_days = attendances.filter(is_late=True).count()
                late_day_equivalents = late_days // 3
                late_deduction = 0
                if base_pay and late_day_equivalents:
                    late_deduction = round((base_pay / 30.0) * late_day_equivalents, 2)
                    total_deductions += late_deduction
                    deduction_ded += late_deduction
                
                # Unpaid leave deduction
                unpaid_leave_deduction = 0
                if base_pay and absences:
                    unpaid_leave_deduction = round((base_pay / 30.0) * absences, 2)
                    total_deductions += unpaid_leave_deduction
                    deduction_ded += unpaid_leave_deduction
                
                # Tax calculation
                taxable_income = basic_salary + total_earnings
                slab = TaxSlab.objects.order_by('min_income').filter(
                    min_income__lte=taxable_income
                ).filter(
                    Q(max_income__gte=taxable_income) | Q(max_income__isnull=True)
                ).first()
                tax_amount = 0
                if slab:
                    tax_amount = round((taxable_income * float(slab.rate_percent) / 100.0) + float(slab.fixed_deduction), 2)
                    if tax_amount > 0:
                        total_deductions += tax_amount
                        deduction_other += tax_amount
                
                # Loan repayments
                loan_installment_total = 0
                active_loans = Loan.objects.filter(employee=employee, is_active=True)
                for loan in active_loans:
                    if float(loan.balance) > 0 and float(loan.monthly_installment) > 0:
                        installment = float(loan.monthly_installment)
                        if installment > float(loan.balance):
                            installment = float(loan.balance)
                        loan_installment_total += installment
                if loan_installment_total:
                    total_deductions += loan_installment_total
                    deduction_ded += loan_installment_total
                
                # Opening balance (from previous period's closing balance)
                prev_payslip = Payslip.objects.filter(
                    employee=employee,
                    period_end__lt=period_start
                ).order_by('-period_end').first()
                opening_balance = 0
                if prev_payslip:
                    # Get closing balance from previous payslip metadata if stored
                    opening_balance = 0  # Can be enhanced to store in Payslip model
                
                # Closing balance
                closing_balance = opening_balance + deduction_add - deduction_ded
                
                # Gross salary (basic salary + all allowances/earnings)
                gross_salary = basic_salary + total_earnings
                
                # Net pay
                net_pay = gross_salary - total_deductions
                
                # Create payslip
                payslip = Payslip.objects.create(
                    employee=employee,
                    date=timezone.now().date(),
                    period_start=period_start,
                    period_end=period_end,
                    gross_pay=gross_salary,
                    total_earnings=total_earnings,
                    total_deductions=total_deductions,
                    total=net_pay,
                    created_by=request.user,
                    status=Payslip.STATUS_PROCESSED,
                )
                
                # Generate PDF
                pdf_bytes = _render_payslip_pdf_to_bytes(
                    payslip,
                    period_items,
                    context_extra={
                        'base_salary': basic_salary,
                        'unpaid_leave_deduction': unpaid_leave_deduction,
                        'late_deduction': late_deduction,
                        'tax_amount': tax_amount,
                        'loan_installment_total': loan_installment_total,
                    }
                )
                filename = f"payslip_{employee.user.username}_{period_start}_{period_end}.pdf"
                payslip.pdf.save(filename, ContentFile(pdf_bytes))
                payslip.save()
                
                created_count += 1
            except Exception as e:
                logger.error(f"Error processing payroll for employee {employee.id}: {str(e)}")
                continue
        
        messages.success(request, f'Payroll processed successfully! Created {created_count} payslips for {month}/{year}.')
        return redirect('monthly_payroll_register', month=month, year=year)
    
    # Get employees list for display (filtered by city and department if selected)
    employees_list = Employee.objects.select_related('user', 'designation', 'department').all()
    selected_city = selected_city_get
    selected_department = None
    
    # Set selected_department from GET parameter or form data
    if request.method == 'GET':
        # Get from GET parameters
        if selected_city:
            employees_list = employees_list.filter(city=selected_city)
        if selected_department_get:
            try:
                selected_department = Department.objects.get(id=selected_department_get)
                employees_list = employees_list.filter(department=selected_department)
            except (Department.DoesNotExist, ValueError):
                selected_department = None
    elif request.method == 'POST' and form.is_valid():
        selected_city = form.cleaned_data.get('city')
        if selected_city:
            employees_list = employees_list.filter(city=selected_city)
        selected_department = form.cleaned_data.get('department')
        if selected_department:
            employees_list = employees_list.filter(department=selected_department)
    else:
        # For initial page load, try to get department from GET if not already set
        if selected_department_get and not selected_department:
            try:
                selected_department = Department.objects.get(id=selected_department_get)
            except (Department.DoesNotExist, ValueError):
                selected_department = None
    
    # Get departments for the selected city
    departments_for_city = Department.objects.none()
    if selected_city:
        departments_for_city = Department.objects.filter(
            employees__city=selected_city
        ).distinct().order_by('name')
    
    # Get employee count for display (filtered by both city and department)
    # Use the same query as employees_list to ensure consistency
    employees = Employee.objects.all()
    if selected_city:
        employees = employees.filter(city=selected_city)
    if selected_department:
        employees = employees.filter(department=selected_department)
    elif selected_department_get:
        # If selected_department is None but we have selected_department_get, try to use it
        try:
            dept_obj = Department.objects.get(id=selected_department_get)
            employees = employees.filter(department=dept_obj)
            # Also set selected_department for context
            if not selected_department:
                selected_department = dept_obj
        except (Department.DoesNotExist, ValueError):
            pass
    
    departments = Department.objects.all().order_by('name')
    existing_payslips_count = 0
    if request.method == 'POST' and form.is_valid():
        month = int(form.cleaned_data['month'])
        year = int(form.cleaned_data['year'])
        days_of_month = int(form.cleaned_data['days_of_month'])
        department = form.cleaned_data.get('department')
        period_start = date(year, month, 1)
        period_end = date(year, month, days_of_month)
        existing_payslips = Payslip.objects.filter(
            period_start=period_start,
            period_end=period_end
        )
        if selected_city:
            existing_payslips = existing_payslips.filter(employee__city=selected_city)
        if department:
            existing_payslips = existing_payslips.filter(employee__department=department)
        existing_payslips_count = existing_payslips.count()
    
    context = {
        'form': form,
        'total_employees': employees.count(),
        'existing_payslips_count': existing_payslips_count,
        'departments': departments,
        'all_cities': all_cities,
        'employees_list': employees_list[:50],  # Limit to 50 for display
        'selected_city': selected_city,
        'selected_department': selected_department,
        'departments_for_city': departments_for_city,
    }
    return render(request, 'core/monthly_payroll_create.html', context)

@user_passes_test(is_admin)
def monthly_payroll_register(request, month=None, year=None):
    """Display monthly payroll register"""
    from calendar import monthrange
    from datetime import date
    
    # Get month and year from URL, GET parameters, or use current
    if not month:
        month = request.GET.get('month')
    if not year:
        year = request.GET.get('year')
    
    if not month or not year:
        today = timezone.now().date()
        month = today.month
        year = today.year
    
    month = int(month)
    year = int(year)
    
    # Calculate period
    days_of_month = monthrange(year, month)[1]
    period_start = date(year, month, 1)
    period_end = date(year, month, days_of_month)
    
    # Get all payslips for this period
    payslips = Payslip.objects.filter(
        period_start=period_start,
        period_end=period_end
    ).select_related('employee__user', 'employee__designation').order_by('employee__user__first_name', 'employee__user__last_name')
    
    # Build register data
    register_data = []
    for payslip in payslips:
        employee = payslip.employee
        
        # Get attendance data
        attendances = Attendance.objects.filter(
            employee=employee,
            date__gte=period_start,
            date__lte=period_end
        )
        work_days = attendances.filter(status='present').count()
        absences = attendances.filter(status='absent').count()
        
        # Get leaves
        leaves = Leave.objects.filter(
            employee=employee,
            status='approved',
            start_date__lte=period_end,
            end_date__gte=period_start
        )
        leave_days = 0
        for leave in leaves:
            overlap_start = max(leave.start_date, period_start)
            overlap_end = min(leave.end_date, period_end)
            if overlap_start <= overlap_end:
                leave_days += (overlap_end - overlap_start).days + 1
        
        # Get payroll items
        period_items = PayrollItem.objects.filter(employee=employee).filter(
            (
                Q(is_recurring=False) & Q(date__gte=period_start, date__lte=period_end)
            ) | (
                Q(is_recurring=True) & (
                    (Q(start_date__lte=period_end) | Q(start_date__isnull=True)) & 
                    (Q(end_date__gte=period_start) | Q(end_date__isnull=True))
                )
            )
        )
        
        # Calculate allowances
        allowance_fuel = 0
        allowance_mobile = 0
        allowance_other = 0
        
        for item in period_items.filter(item_type=PayrollItem.EARNING):
            amount = float(item.amount)
            if 'fuel' in item.name.lower():
                allowance_fuel += amount
            elif 'mobile' in item.name.lower():
                allowance_mobile += amount
            else:
                allowance_other += amount
        
        # Calculate deductions
        deduction_add = 0
        deduction_ded = 0
        deduction_other = 0
        
        for item in period_items.filter(item_type=PayrollItem.DEDUCTION):
            amount = float(item.amount)
            if 'add' in item.name.lower() or 'advance' in item.name.lower():
                deduction_add += amount
            elif 'ded' in item.name.lower() or 'deduction' in item.name.lower():
                deduction_ded += amount
            else:
                deduction_other += amount
        
        # Base pay and basic salary
        base_pay = float(employee.salary or 0)
        basic_salary = base_pay
        if work_days > 0 and days_of_month > 0:
            per_day_salary = base_pay / days_of_month
            basic_salary = base_pay - (per_day_salary * absences)
        else:
            basic_salary = 0
        
        # Opening and closing balance (simplified)
        opening_balance = 0
        closing_balance = opening_balance + deduction_add - deduction_ded
        
        # Gross and net (use payslip data)
        gross_salary = float(payslip.gross_pay or 0)
        net_pay = float(payslip.total or 0)
        
        register_data.append({
            'employee_no': employee.id,
            'employee': employee,
            'designation': employee.designation.name if employee.designation else '',
            'base_pay': base_pay,
            'work_days': work_days,
            'absences': absences,
            'leaves': leave_days,
            'basic_salary': basic_salary,
            'allowance_fuel': allowance_fuel,
            'allowance_mobile': allowance_mobile,
            'allowance_other': allowance_other,
            'gross_salary': gross_salary,
            'opening_balance': opening_balance,
            'deduction_add': deduction_add,
            'deduction_ded': deduction_ded,
            'deduction_other': deduction_other,
            'closing_balance': closing_balance,
            'net_pay': net_pay,
            'payslip': payslip,
        })
    
    # Get city from company settings
    city = 'N/A'
    try:
        settings_obj = CompanySettings.objects.first()
        if settings_obj and settings_obj.city:
            city = settings_obj.city
    except:
        pass
    
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
    month_list = [(i, month_names[i]) for i in range(1, 13)]
    month_name = month_names[month]
    
    # Check for export format
    export_format = request.GET.get('format', '')
    if export_format and register_data:
        from .report_utils import export_to_pdf, export_to_excel, export_to_csv
        
        # Prepare export data
        headers = [
            'No.', 'Name', 'Designation', 'Basic Pay', 'Work Days', 'Abs', 'Lvs',
            'Basic Salary', 'Fuel Allowance', 'Mobile Allowance', 'Other Allowance',
            'Gross Salary', 'Open Bal.', 'Add Deduction', 'Ded Deduction', 'Other Deduction',
            'Close Bal.', 'Net Pay'
        ]
        
        export_data = []
        for idx, data in enumerate(register_data, 1):
            export_data.append([
                idx,
                data['employee'].user.get_full_name() or data['employee'].user.username,
                data['designation'] or 'N/A',
                round(data['base_pay'], 2),
                data['work_days'],
                data['absences'],
                data['leaves'],
                round(data['basic_salary'], 2),
                round(data['allowance_fuel'], 2),
                round(data['allowance_mobile'], 2),
                round(data['allowance_other'], 2),
                round(data['gross_salary'], 2),
                round(data['opening_balance'], 2),
                round(data['deduction_add'], 2),
                round(data['deduction_ded'], 2),
                round(data['deduction_other'], 2),
                round(data['closing_balance'], 2),
                round(data['net_pay'], 2),
            ])
        
        title = f"Monthly Payroll Register - {month_name}, {year}"
        filename = f"payroll_register_{month_name}_{year}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            if export_format == 'pdf':
                return export_to_pdf(export_data, title, headers, filename)
            elif export_format == 'excel':
                return export_to_excel(export_data, title, headers, filename)
            elif export_format == 'csv':
                return export_to_csv(export_data, title, headers, filename)
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Export error: {str(e)}')
            # Continue to show the page with error message
    
    context = {
        'register_data': register_data,
        'month': month,
        'year': year,
        'month_name': month_name,
        'month_list': month_list,
        'days_of_month': days_of_month,
        'period_start': period_start,
        'period_end': period_end,
        'city': city,
        'total_employees': len(register_data),
    }
    return render(request, 'core/monthly_payroll_register.html', context)

# Notification views
def create_notification(recipient, sender, notification_type, title, message, link=None):
    """Helper function to create notifications"""
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message=message[:200] + ('...' if len(message) > 200 else ''),
        link=link or '#',
    )

@login_required
def get_notifications(request):
    """Get unread notifications count and recent notifications"""
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'type': notif.notification_type,
            'title': notif.title,
            'message': notif.message,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat(),
            'link': notif.link or '#',
        })
    
    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notifications_data,
    })

@login_required
def all_notifications(request):
    """View all notifications with pagination"""
    from django.core.paginator import Paginator
    
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/all_notifications.html', {
        'notifications': page_obj,
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.mark_as_read()
        if request.method == 'POST':
            return JsonResponse({'success': True})
        else:
            if notification.link and notification.link != '#':
                return redirect(notification.link)
            return redirect('all_notifications')
    except Notification.DoesNotExist:
        if request.method == 'POST':
            return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)
        return redirect('all_notifications')

# Notice Board Views
@user_passes_test(is_admin)
@login_required
def notice_list(request):
    """Admin view to list all notices"""
    notices = Notice.objects.all().order_by('-created_at')
    active_count = notices.filter(is_active=True).count()
    with_attachments = notices.exclude(attachment='').count()
    return render(request, 'core/notice_list.html', {
        'notices': notices,
        'active_count': active_count,
        'with_attachments': with_attachments,
    })

@user_passes_test(is_admin)
@login_required
def notice_add(request):
    """Admin view to add a new notice"""
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            # Handle multiple file attachments
            from .models import NoticeFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        NoticeFile.objects.create(
                            notice=notice,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            messages.success(request, 'Notice created successfully!')
            return redirect('notice_list')
    else:
        form = NoticeForm()
    return render(request, 'core/notice_form.html', {'form': form, 'title': 'Add Notice'})

@user_passes_test(is_admin)
@login_required
def notice_edit(request, notice_id):
    """Admin view to edit a notice"""
    notice = get_object_or_404(Notice, id=notice_id)
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        if form.is_valid():
            form.save()
            # Handle multiple file attachments
            from .models import NoticeFile
            if request.FILES.getlist('attachments'):
                for file in request.FILES.getlist('attachments'):
                    try:
                        NoticeFile.objects.create(
                            notice=notice,
                            file=file,
                            file_name=file.name,
                            file_size=file.size,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        print(f"Error saving attachment: {e}")
            messages.success(request, 'Notice updated successfully!')
            return redirect('notice_list')
    else:
        form = NoticeForm(instance=notice)
    return render(request, 'core/notice_form.html', {'form': form, 'notice': notice, 'title': 'Edit Notice'})

@user_passes_test(is_admin)
@login_required
def notice_delete(request, notice_id):
    """Admin view to delete a notice"""
    notice = get_object_or_404(Notice, id=notice_id)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, 'Notice deleted successfully!')
        return redirect('notice_list')
    return render(request, 'core/notice_confirm_delete.html', {'notice': notice})

# Dashboard Layout Views
@login_required
@require_POST
def save_dashboard_layout(request):
    """Save dashboard layout preferences"""
    try:
        layout_data = json.loads(request.body)
        dashboard_type = layout_data.get('dashboard_type', 'admin')
        
        layout, created = DashboardLayout.objects.get_or_create(
            user=request.user,
            dashboard_type=dashboard_type,
            defaults={'layout_data': layout_data.get('order', [])}
        )
        
        if not created:
            layout.layout_data = layout_data.get('order', [])
            layout.save()
        
        return JsonResponse({'success': True, 'message': 'Layout saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def get_dashboard_layout(request):
    """Get saved dashboard layout preferences"""
    try:
        dashboard_type = request.GET.get('dashboard_type', 'admin')
        layout = DashboardLayout.objects.filter(user=request.user, dashboard_type=dashboard_type).first()
        
        if layout:
            return JsonResponse({'success': True, 'layout': layout.layout_data})
        else:
            return JsonResponse({'success': True, 'layout': []})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

# ===================== REPORTS =====================

@user_passes_test(is_admin)
def reports(request):
    """Comprehensive reporting system for all entities"""
    from .report_utils import export_to_pdf, export_to_docx, export_to_excel, export_to_csv
    from .models import (
        Employee, Department, Designation, Project, Task, Ticket, 
        Attendance, Leave, Client, Budget, BudgetExpense, BudgetRevenue,
        Asset, Invoice, Estimate, Expense, Loan, AdvanceRequest, Payslip
    )
    from django.db.models import Q
    
    # Get report type and format
    report_type = request.GET.get('type', 'employees')
    export_format = request.GET.get('format', '')
    
    # Get filter parameters
    department_id = request.GET.get('department', '')
    designation_id = request.GET.get('designation', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Prepare data based on report type
    data = []
    headers = []
    title = ""
    
    if report_type == 'employees':
        title = "Employees Report"
        queryset = Employee.objects.select_related('user', 'department', 'designation').all()
        
        # Apply filters
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if designation_id:
            queryset = queryset.filter(designation_id=designation_id)
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )
        
        headers = ['ID', 'Username', 'Full Name', 'Email', 'Phone', 'Department', 'Designation', 'Salary', 'Date of Joining', 'Status']
        for emp in queryset:
            data.append([
                emp.id,
                emp.user.username,
                emp.user.get_full_name() or emp.user.username,
                emp.user.email,
                emp.phone or 'N/A',
                emp.department.name if emp.department else 'N/A',
                emp.designation.name if emp.designation else 'N/A',
                f"Rs{emp.salary:.2f}" if emp.salary else 'N/A',
                emp.date_of_joining.strftime('%Y-%m-%d') if emp.date_of_joining else 'N/A',
                'Active' if not emp.is_restricted else 'Restricted'
            ])
    
    elif report_type == 'departments':
        title = "Departments Report"
        queryset = Department.objects.prefetch_related('employee_set').all()
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        headers = ['ID', 'Name', 'Description', 'Total Employees']
        for dept in queryset:
            data.append([
                dept.id,
                dept.name,
                dept.description[:50] + '...' if dept.description and len(dept.description) > 50 else (dept.description or 'N/A'),
                dept.employee_set.count()
            ])
    
    elif report_type == 'designations':
        title = "Designations Report"
        queryset = Designation.objects.all()
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        headers = ['ID', 'Name', 'Description', 'Total Employees']
        for desg in queryset:
            emp_count = Employee.objects.filter(designation=desg).count()
            data.append([
                desg.id,
                desg.name,
                desg.description[:50] + '...' if desg.description and len(desg.description) > 50 else (desg.description or 'N/A'),
                emp_count
            ])
    
    elif report_type == 'projects':
        title = "Projects Report"
        queryset = Project.objects.select_related('client', 'manager', 'manager__user').all()
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        if status_filter:
            # Filter by task status if needed
            pass
        
        headers = ['ID', 'Name', 'Client', 'Manager', 'Total Tasks', 'Completed Tasks']
        for proj in queryset:
            tasks = proj.tasks.all()
            completed = tasks.filter(status='completed').count()
            data.append([
                proj.id,
                proj.name,
                proj.client.name if proj.client else 'N/A',
                proj.manager.user.get_full_name() if proj.manager else 'N/A',
                tasks.count(),
                completed
            ])
    
    elif report_type == 'tasks':
        title = "Tasks Report"
        queryset = Task.objects.select_related('project', 'assigned_to', 'assigned_to__user', 'assigned_by', 'assigned_by__user').all()
        
        if department_id:
            queryset = queryset.filter(assigned_to__department_id=department_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
        
        headers = ['ID', 'Title', 'Project', 'Assigned To', 'Assigned By', 'Status', 'Priority', 'Deadline', 'Created Date']
        for task in queryset:
            data.append([
                task.id,
                task.title,
                task.project.name,
                task.assigned_to.user.get_full_name() if task.assigned_to else 'N/A',
                task.assigned_by.user.get_full_name() if task.assigned_by else 'N/A',
                task.get_status_display(),
                task.get_priority_display(),
                task.deadline.strftime('%Y-%m-%d') if task.deadline else 'N/A',
                task.created_at.strftime('%Y-%m-%d')
            ])
    
    elif report_type == 'tickets':
        title = "Tickets Report"
        queryset = Ticket.objects.select_related('created_by', 'assigned_to', 'related_task').all()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        if search_query:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(tk_id__icontains=search_query))
        
        headers = ['Ticket ID', 'Title', 'Created By', 'Assigned To', 'Status', 'Priority', 'Progress %', 'Created Date', 'Due Date']
        for ticket in queryset:
            data.append([
                ticket.tk_id,
                ticket.title,
                ticket.created_by.get_full_name() or ticket.created_by.username,
                ticket.assigned_to.get_full_name() if ticket.assigned_to else 'Unassigned',
                ticket.get_status_display(),
                ticket.get_priority_display(),
                f"{ticket.progress_percentage}%" if ticket.related_task else 'N/A',
                ticket.created_at.strftime('%Y-%m-%d %H:%M'),
                ticket.end_date.strftime('%Y-%m-%d') if ticket.end_date else 'N/A'
            ])
    
    elif report_type == 'attendance':
        title = "Attendance Report"
        queryset = Attendance.objects.select_related('employee', 'employee__user', 'employee__department').all()
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        headers = ['ID', 'Employee', 'Department', 'Date', 'Check In', 'Check Out', 'Status', 'Work Hours', 'Late Minutes']
        for att in queryset:
            data.append([
                att.id,
                att.employee.user.get_full_name() or att.employee.user.username,
                att.employee.department.name if att.employee.department else 'N/A',
                att.date.strftime('%Y-%m-%d'),
                att.check_in.strftime('%H:%M') if att.check_in else 'N/A',
                att.check_out.strftime('%H:%M') if att.check_out else 'N/A',
                att.get_status_display(),
                f"{att.total_work_hours:.2f}" if att.total_work_hours else 'N/A',
                att.late_minutes
            ])
    
    elif report_type == 'leaves':
        title = "Leaves Report"
        queryset = Leave.objects.select_related('employee', 'employee__user', 'employee__department', 'reviewed_by').all()
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        headers = ['ID', 'Employee', 'Department', 'Leave Type', 'Start Date', 'End Date', 'Status', 'Applied Date', 'Reviewed By']
        for leave in queryset:
            data.append([
                leave.id,
                leave.employee.user.get_full_name() or leave.employee.user.username,
                leave.employee.department.name if leave.employee.department else 'N/A',
                leave.get_leave_type_display(),
                leave.start_date.strftime('%Y-%m-%d'),
                leave.end_date.strftime('%Y-%m-%d'),
                leave.get_status_display(),
                leave.applied_at.strftime('%Y-%m-%d'),
                leave.reviewed_by.get_full_name() if leave.reviewed_by else 'Pending'
            ])
    
    elif report_type == 'clients':
        title = "Clients Report"
        queryset = Client.objects.prefetch_related('projects').all()
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query))
        
        headers = ['ID', 'Name', 'Email', 'Phone', 'Company', 'Total Projects']
        for client in queryset:
            data.append([
                client.id,
                client.name,
                client.email or 'N/A',
                client.phone or 'N/A',
                client.company or 'N/A',
                client.projects.count()
            ])
    
    elif report_type == 'budgets':
        title = "Budgets Report"
        queryset = Budget.objects.select_related('project', 'category').prefetch_related('expenses', 'revenues').all()
        
        if date_from:
            queryset = queryset.filter(period_start__gte=date_from)
        if date_to:
            queryset = queryset.filter(period_end__lte=date_to)
        
        headers = ['ID', 'Name', 'Type', 'Category/Project', 'Period Start', 'Period End', 'Total Expenses', 'Total Revenue']
        for budget in queryset:
            total_expenses = sum(exp.amount for exp in budget.expenses.all())
            total_revenue = sum(rev.amount for rev in budget.revenues.all())
            type_name = budget.category.name if budget.category else (budget.project.name if budget.project else 'N/A')
            data.append([
                budget.id,
                budget.name,
                budget.get_type_display(),
                type_name,
                budget.period_start.strftime('%Y-%m-%d'),
                budget.period_end.strftime('%Y-%m-%d'),
                f"${total_expenses:.2f}",
                f"${total_revenue:.2f}"
            ])
    
    elif report_type == 'assets':
        title = "Assets Report"
        queryset = Asset.objects.select_related('asset_user', 'asset_user__user').all()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search_query:
            queryset = queryset.filter(Q(asset_name__icontains=search_query) | Q(asset_id__icontains=search_query))
        
        headers = ['ID', 'Asset Name', 'Asset ID', 'Status', 'Assigned To', 'Cost', 'Purchase Date', 'Condition']
        for asset in queryset:
            data.append([
                asset.id,
                asset.asset_name,
                asset.asset_id,
                asset.get_status_display(),
                asset.asset_user.user.get_full_name() if asset.asset_user else 'Unassigned',
                f"${asset.cost:.2f}" if asset.cost else 'N/A',
                asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else 'N/A',
                asset.condition or 'N/A'
            ])
    
    elif report_type == 'invoices':
        title = "Invoices Report"
        queryset = Invoice.objects.select_related('client', 'project', 'tax').prefetch_related('items').all()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(invoice_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(invoice_date__lte=date_to)
        
        headers = ['ID', 'Client', 'Project', 'Invoice Date', 'Due Date', 'Status', 'Total Amount', 'Tax']
        for inv in queryset:
            total = sum(item.amount for item in inv.items.all())
            tax_amount = (total * float(inv.tax.percentage) / 100) if inv.tax else 0
            data.append([
                inv.id,
                inv.client.name,
                inv.project.name if inv.project else 'N/A',
                inv.invoice_date.strftime('%Y-%m-%d'),
                inv.due_date.strftime('%Y-%m-%d'),
                inv.get_status_display(),
                f"Rs{total:.2f}",
                f"Rs{tax_amount:.2f}" if tax_amount else 'N/A'
            ])
    
    elif report_type == 'loans':
        title = "Loans Report"
        queryset = Loan.objects.select_related('employee', 'employee__user').all()
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        headers = ['ID', 'Employee', 'Principal Amount', 'Monthly Installment', 'Balance', 'Start Date', 'End Date', 'Status']
        for loan in queryset:
            data.append([
                loan.id,
                loan.employee.user.get_full_name() or loan.employee.user.username,
                f"Rs{loan.principal_amount:.2f}",
                f"Rs{loan.monthly_installment:.2f}",
                f"Rs{loan.balance:.2f}",
                loan.start_date.strftime('%Y-%m-%d'),
                loan.end_date.strftime('%Y-%m-%d') if loan.end_date else 'N/A',
                'Active' if loan.is_active else 'Inactive'
            ])
    
    elif report_type == 'advances':
        title = "Advance Requests Report"
        queryset = AdvanceRequest.objects.select_related('employee', 'employee__user', 'reviewed_by').all()
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(requested_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(requested_at__lte=date_to)
        
        headers = ['ID', 'Employee', 'Amount', 'Status', 'Requested Date', 'Reviewed By', 'Reviewed Date']
        for adv in queryset:
            data.append([
                adv.id,
                adv.employee.user.get_full_name() or adv.employee.user.username,
                f"Rs{adv.amount:.2f}",
                adv.get_status_display(),
                adv.requested_at.strftime('%Y-%m-%d'),
                adv.reviewed_by.get_full_name() if adv.reviewed_by else 'Pending',
                adv.reviewed_at.strftime('%Y-%m-%d') if adv.reviewed_at else 'N/A'
            ])
    
    elif report_type == 'payslips':
        title = "Payslips Report"
        queryset = Payslip.objects.select_related('employee', 'employee__user', 'created_by').all()
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(period_start__gte=date_from)
        if date_to:
            queryset = queryset.filter(period_end__lte=date_to)
        
        headers = ['ID', 'Employee', 'Period Start', 'Period End', 'Gross Pay', 'Total Earnings', 'Total Deductions', 'Net Pay', 'Status', 'Date']
        for payslip in queryset:
            data.append([
                payslip.id,
                payslip.employee.user.get_full_name() or payslip.employee.user.username,
                payslip.period_start.strftime('%Y-%m-%d') if payslip.period_start else 'N/A',
                payslip.period_end.strftime('%Y-%m-%d') if payslip.period_end else 'N/A',
                f"${payslip.gross_pay:.2f}",
                f"${payslip.total_earnings:.2f}",
                f"${payslip.total_deductions:.2f}",
                f"${payslip.total:.2f}",
                payslip.get_status_display(),
                payslip.date.strftime('%Y-%m-%d')
            ])
    
    # Export if format is specified
    if export_format:
        filename = f"{report_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if export_format == 'pdf':
                return export_to_pdf(data, title, headers, filename)
            elif export_format == 'docx':
                return export_to_docx(data, title, headers, filename)
            elif export_format == 'excel':
                return export_to_excel(data, title, headers, filename)
            elif export_format == 'csv':
                return export_to_csv(data, title, headers, filename)
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('reports')
    
    # Get filter options for template
    departments = Department.objects.all().order_by('name')
    designations = Designation.objects.all().order_by('name')
    
    # Report types
    report_types = [
        ('employees', 'Employees'),
        ('departments', 'Departments'),
        ('designations', 'Designations'),
        ('projects', 'Projects'),
        ('tasks', 'Tasks'),
        ('tickets', 'Tickets'),
        ('attendance', 'Attendance'),
        ('leaves', 'Leaves'),
        ('clients', 'Clients'),
        ('budgets', 'Budgets'),
        ('assets', 'Assets'),
        ('invoices', 'Invoices'),
        ('loans', 'Loans'),
        ('advances', 'Advance Requests'),
        ('payslips', 'Payslips'),
    ]
    
    return render(request, 'core/reports.html', {
        'report_type': report_type,
        'data': data,
        'headers': headers,
        'title': title,
        'departments': departments,
        'designations': designations,
        'report_types': report_types,
        'department_id': department_id,
        'designation_id': designation_id,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'search_query': search_query,
    })
