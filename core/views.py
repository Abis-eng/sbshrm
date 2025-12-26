from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib import messages
from .models import Employee, Department, Designation, Attendance, AttendanceLog, AttendanceMachine, Ticket, Client, Holiday, Leave, Notice
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from core.models import ChatMessage, Notification
from django.db.models import Q, Max
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
from .forms import PayrollItemForm, PayslipCreateForm, PayslipEditForm, TaxSlabForm, LoanForm, AdvanceRequestForm, AdvanceReviewForm
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


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('dashboard')
            else:
                return redirect('employee_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')

def is_admin(user):
    return user.is_superuser

def is_employee(user):
    return user.is_authenticated and not user.is_superuser

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
def employee_list(request):
    if request.user.is_superuser:
        employees = Employee.objects.all()
        departments = Department.objects.all()
        designations = Designation.objects.all()
    else:
        # Employees can only see their own information
        try:
            employee = request.user.employee
            employees = Employee.objects.filter(id=employee.id)
            # Don't show department/designation filters for employees
            departments = Department.objects.none()
            designations = Designation.objects.none()
        except Exception:
            employees = Employee.objects.none()
            departments = Department.objects.none()
            designations = Designation.objects.none()
    return render(request, 'core/employee_list.html', {'employees': employees, 'departments': departments, 'designations': designations})

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
    
    return render(request, 'core/view_employee_profile.html', {
        'employee': employee,
        'attendance_count': attendance_count,
        'leaves_count': leaves_count,
        'projects_count': projects_count,
        'tasks_count': tasks_count,
        'advances_count': advances_count,
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
        date_of_joining = request.POST.get('date_of_joining')
        if not date_of_joining:
            date_of_joining = None
        machine_id = request.POST.get('machine_id')
        fingerprint_id = request.POST.get('fingerprint_id')
        face_id = request.POST.get('face_id')
        card_id = request.POST.get('card_id')
        
        if User.objects.filter(username=username).exists():
            error = 'Username already exists. Please choose another.'
            return render(request, 'core/add_employee.html', {'departments': departments, 'designations': designations, 'error': error})
        
        user = User.objects.create(
            username=username,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
        )
        salary = request.POST.get('salary') or None
        employee = Employee.objects.create(
            user=user,
            department_id=department_id,
            designation_id=designation_id,
            salary=salary if salary else None,
            phone=phone,
            address=address,
            date_of_joining=date_of_joining,
            machine_id=machine_id if machine_id else None,
            fingerprint_id=fingerprint_id if fingerprint_id else None,
            face_id=face_id if face_id else None,
            card_id=card_id if card_id else None,
        )
        return render(request, 'core/employee_created.html', {'username': username, 'password': password})
    return render(request, 'core/add_employee.html', {'departments': departments, 'designations': designations, 'error': error})

class DepartmentForm(ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']

@user_passes_test(is_admin)
def manage_departments(request):
    departments = Department.objects.all().order_by('name')
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_departments')
    else:
        form = DepartmentForm()
    # For graph: employee count per department
    from django.db.models import Count
    dept_counts = Department.objects.annotate(emp_count=Count('employee')).values('name', 'emp_count')
    return render(request, 'core/manage_departments.html', {'departments': departments, 'form': form, 'dept_counts': list(dept_counts)})

@user_passes_test(is_admin)
def manage_designations(request):
    designations = Designation.objects.all().order_by('name')
    if request.method == 'POST':
        form = DesignationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_designations')
    else:
        form = DesignationForm()
    # For graph: employee count per designation
    from django.db.models import Count
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
        user_data.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'initials': (u.first_name[:1] + u.last_name[:1]).upper() if u.first_name or u.last_name else u.username[:2].upper(),
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
    from django.db.models import Q, Count
    
    # Employees can only see tickets they created or are assigned to
    # Admin can see all tickets when accessing all_tickets, but my_tickets shows their own
    if request.user.is_superuser:
        base_query = Ticket.objects.all()
    else:
        base_query = Ticket.objects.filter(
            Q(created_by=request.user) | Q(assigned_to=request.user)
        )
    
    # Filter by type: all, sent, received
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'sent':
        tickets = base_query.filter(created_by=request.user)
    elif filter_type == 'received':
        tickets = base_query.filter(assigned_to=request.user)
    else:
        if request.user.is_superuser:
            tickets = base_query
        else:
            tickets = base_query.filter(Q(created_by=request.user) | Q(assigned_to=request.user))
    
    tickets = tickets.select_related('created_by', 'assigned_to').annotate(
        reply_count=Count('replies')
    ).order_by('-created_at')
    
    # Filtering
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
    
    # Statistics - only for employee's own tickets
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
                    message=f'Your advance request of ${adv.amount} has been approved for ${approved_amount:.2f}.',
                    link=f'/my-advances/'
                )
            else:
                create_notification(
                    recipient=adv.employee.user,
                    sender=request.user,
                    notification_type='system',
                    title='Advance request approved',
                    message=f'Your advance request of ${adv.amount} has been approved.',
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
    from .models import TicketReply
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject', '')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'medium')
        assigned_to_id = request.POST.get('assigned_to')
        end_date_str = request.POST.get('end_date', '')
        
        from datetime import datetime
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date)
            except:
                pass
        
        # Get assigned user
        assigned_to = None
        if assigned_to_id:
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                messages.error(request, 'Selected recipient not found.')
                return redirect('submit_ticket')
        
        # Get related task if admin is creating ticket and selected a task
        related_task = None
        if request.user.is_superuser:
            related_task_id = request.POST.get('related_task', '')
            if related_task_id:
                try:
                    from .models import Task
                    related_task = Task.objects.get(id=related_task_id)
                except Task.DoesNotExist:
                    pass
        
        # Create ticket with assigned user
        ticket = Ticket.objects.create(
            title=title,
            subject=subject,
            description=description,
            priority=priority,
            created_by=request.user,
            assigned_to=assigned_to,
            related_task=related_task,
            end_date=end_date,
            status='new'  # New tickets start as 'new'
        )
        
        # Handle file attachments - use TicketFile model instead
        from .models import TicketFile
        if request.FILES.getlist('attachments'):
            for file in request.FILES.getlist('attachments'):
                TicketFile.objects.create(
                    ticket=ticket,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                    uploaded_by=request.user
                )
        
        # Create notification for assigned user or all admins if not assigned
        if assigned_to:
            create_notification(
                recipient=assigned_to,
                sender=request.user,
                notification_type='ticket',
                title=f'New ticket: {ticket.tk_id} - {title}',
                message=description[:200],
                link=f'/ticket/{ticket.id}/'
            )
            messages.success(request, f'Ticket {ticket.tk_id} created and sent to {assigned_to.get_full_name() or assigned_to.username}!')
        else:
            # If no assignment, notify all admins
            admin_users = User.objects.filter(is_superuser=True)
            for admin in admin_users:
                create_notification(
                    recipient=admin,
                    sender=request.user,
                    notification_type='ticket',
                    title=f'New ticket: {ticket.tk_id} - {title}',
                    message=description[:200],
                    link=f'/ticket/{ticket.id}/'
                )
            messages.success(request, f'Ticket {ticket.tk_id} created successfully! Admin will be notified.')
        return redirect('ticket_detail', ticket_id=ticket.id)
    
    # Get users for dropdown
    if request.user.is_superuser:
        employees = User.objects.filter(is_superuser=False, employee__isnull=False).select_related('employee')
        admins = []
        # Get all tasks for admin to link to ticket
        from .models import Task
        tasks = Task.objects.select_related('project', 'assigned_to', 'assigned_by').all().order_by('-created_at')
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
    from django.db.models import Q, Count
    tickets = Ticket.objects.select_related('created_by', 'assigned_to').annotate(
        reply_count=Count('replies')
    ).order_by('-created_at')
    
    # Filtering
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
    
    # Statistics
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
    from .models import TicketReply
    ticket = get_object_or_404(Ticket.objects.select_related('created_by', 'assigned_to', 'related_task', 'related_task__project', 'related_task__assigned_to', 'related_task__assigned_to__user'), id=ticket_id)
    
    # Check permissions - employees can only see their own tickets
    if not request.user.is_superuser:
        if ticket.created_by != request.user and ticket.assigned_to != request.user:
            messages.error(request, 'You do not have permission to view this ticket.')
            return redirect('my_tickets')
    
    replies = ticket.replies.select_related('created_by', 'reply_to').order_by('created_at')
    # Get files separately
    from .models import TicketFile
    files = TicketFile.objects.filter(ticket=ticket).select_related('uploaded_by')
    employees = User.objects.filter(is_superuser=False, employee__isnull=False).select_related('employee')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'reply':
            message = request.POST.get('message', '').strip()
            if message:
                try:
                    reply = TicketReply.objects.create(
                        ticket=ticket,
                        message=message,
                        created_by=request.user,
                        reply_to_id=request.POST.get('reply_to') or None
                    )
                    
                    # Handle file attachment
                    if request.FILES.get('attachment'):
                        try:
                            reply.attachment = request.FILES['attachment']
                            reply.save()
                        except Exception as e:
                            print(f"Error saving attachment: {e}")
                    
                    # Mark reply as read for replier
                    reply.is_read = True
                    reply.save()
                    
                    # Create notification
                    if request.user.is_superuser:
                        # Admin replied - notify ticket creator
                        if ticket.created_by != request.user:
                            Notification.objects.create(
                                recipient=ticket.created_by,
                                sender=request.user,
                                notification_type='ticket',
                                title=f'Reply on ticket {ticket.tk_id}',
                                message=message[:200],
                                link=f'/ticket/{ticket.id}/'
                            )
                    else:
                        # Employee replied - notify assigned admin or all admins
                        if ticket.assigned_to and ticket.assigned_to != request.user:
                            Notification.objects.create(
                                recipient=ticket.assigned_to,
                                sender=request.user,
                                notification_type='ticket',
                                title=f'Reply on ticket {ticket.tk_id}',
                                message=message[:200],
                                link=f'/ticket/{ticket.id}/'
                            )
                        elif not ticket.assigned_to:
                            # Notify all admins if no one is assigned
                            for admin in User.objects.filter(is_superuser=True):
                                if admin != request.user:
                                    Notification.objects.create(
                                        recipient=admin,
                                        sender=request.user,
                                        notification_type='ticket',
                                        title=f'Reply on ticket {ticket.tk_id}',
                                        message=message[:200],
                                        link=f'/ticket/{ticket.id}/'
                                    )
                    
                    messages.success(request, 'Reply added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding reply: {str(e)}')
                    print(f"Error creating reply: {e}")
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
                # Notify assigned user
                assigned_user = User.objects.get(id=assigned_user_id)
                create_notification(
                    recipient=assigned_user,
                    sender=request.user,
                    notification_type='ticket',
                    title=f'You have been assigned ticket {ticket.tk_id}',
                    message=ticket.description[:200],
                    link=f'/ticket/{ticket.id}/'
                )
                messages.success(request, f'Ticket assigned to {assigned_user.get_full_name() or assigned_user.username}!')
        
        elif action == 'update_priority' and request.user.is_superuser:
            ticket.priority = request.POST.get('priority')
            ticket.save()
            messages.success(request, 'Ticket priority updated!')
        
        elif action == 'update_progress':
            # Only allow employee assigned to ticket to update progress if ticket is related to task
            if ticket.related_task and ticket.assigned_to == request.user:
                # Check if progress is locked
                if ticket.progress_locked:
                    messages.error(request, 'Progress is locked at 100% and cannot be changed. Contact admin to unlock it.')
                else:
                    try:
                        progress = int(request.POST.get('progress_percentage', 0))
                        if 0 <= progress <= 100:
                            old_progress = ticket.progress_percentage
                            ticket.progress_percentage = progress
                            
                            # If reaching 100%, check if user wants to lock it
                            lock_progress = request.POST.get('lock_progress', 'false') == 'true'
                            if progress == 100 and lock_progress:
                                ticket.progress_locked = True
                                messages.success(request, 'Progress updated to 100% and locked! You will not be able to change it anymore.')
                            elif progress == 100:
                                # Reached 100% but didn't lock - keep unlocked
                                ticket.progress_locked = False
                                messages.success(request, 'Progress updated to 100%! You can lock it to prevent further changes.')
                            else:
                                # Not 100%, ensure it's unlocked
                                ticket.progress_locked = False
                                messages.success(request, f'Progress updated to {progress}%!')
                            
                            ticket.save()
                        else:
                            messages.error(request, 'Progress must be between 0 and 100.')
                    except ValueError:
                        messages.error(request, 'Invalid progress value.')
            else:
                messages.error(request, 'You can only update progress for tickets related to tasks that are assigned to you.')
        
        elif action == 'unlock_progress' and request.user.is_superuser:
            # Admin can unlock progress
            ticket.progress_locked = False
            ticket.save()
            messages.success(request, 'Progress unlocked. Employee can now update it again.')
        
        return redirect('ticket_detail', ticket_id=ticket.id)
    
    # Mark unread replies as read for current user
    ticket.replies.filter(is_read=False).exclude(created_by=request.user).update(is_read=True)
    
    # Check if employee can update progress (only if ticket is related to task and assigned to them, and not locked)
    can_update_progress = False
    if ticket.related_task and ticket.assigned_to == request.user and not request.user.is_superuser:
        can_update_progress = not ticket.progress_locked
    
    return render(request, 'core/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'files': files,
        'employees': employees,
        'can_update_progress': can_update_progress,
    })

@user_passes_test(is_admin)
def edit_ticket(request, ticket_id):
    from .models import TicketReply
    from datetime import datetime
    ticket = get_object_or_404(Ticket, id=ticket_id)
    employees = User.objects.filter(is_superuser=False, employee__isnull=False).select_related('employee')
    # Get all tasks for admin to link to ticket
    from .models import Task
    tasks = Task.objects.select_related('project', 'assigned_to', 'assigned_to__user').all().order_by('-created_at')
    
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
        
        # Handle related task
        related_task_id = request.POST.get('related_task', '')
        if related_task_id:
            try:
                from .models import Task
                ticket.related_task = Task.objects.get(id=related_task_id)
            except Task.DoesNotExist:
                ticket.related_task = None
        else:
            ticket.related_task = None
        
        # Handle progress percentage
        try:
            progress = int(request.POST.get('progress_percentage', ticket.progress_percentage))
            if 0 <= progress <= 100:
                ticket.progress_percentage = progress
        except (ValueError, TypeError):
            pass
        
        # Handle progress locked (only if ticket is related to task)
        if ticket.related_task:
            ticket.progress_locked = request.POST.get('progress_locked') == 'on'
        else:
            ticket.progress_locked = False
        
        end_date_str = request.POST.get('end_date', '')
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                ticket.end_date = timezone.make_aware(end_date)
            except:
                pass
        else:
            ticket.end_date = None
        
        ticket.save()
        
        # Handle file attachments - use TicketFile model
        from .models import TicketFile
        if request.FILES.getlist('attachments'):
            for file in request.FILES.getlist('attachments'):
                TicketFile.objects.create(
                    ticket=ticket,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                    uploaded_by=request.user
                )
        
        messages.success(request, f'Ticket {ticket.tk_id} updated successfully!')
        return redirect('ticket_detail', ticket_id=ticket.id)
    
    return render(request, 'core/edit_ticket.html', {
        'ticket': ticket,
        'employees': employees,
        'tasks': tasks,
    })

@user_passes_test(is_admin)
def update_ticket_status(request, ticket_id):
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

@user_passes_test(is_admin)
def all_attendance(request):
    employees = Employee.objects.all()
    form = AttendanceFilterForm(request.GET)
    
    records = Attendance.objects.select_related('employee__user').order_by('-date')
    
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
    
    # For graph: attendance count by status
    status_counts = Attendance.objects.values('status').annotate(count=Count('id'))
    
    return render(request, 'core/all_attendance.html', {
        'records': records,
        'status_counts': list(status_counts),
        'employees': employees,
        'form': form,
    })

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
    """Sync attendance data from ZKT machine"""
    if request.method == 'POST':
        try:
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            synced_count = zkt_service.sync_attendance(start_date, end_date)
            zkt_service.process_attendance_logs()
            
            messages.success(request, f'Successfully synced {synced_count} attendance records from ZKT machine!')
        except Exception as e:
            messages.error(request, f'Error syncing with ZKT machine: {str(e)}')
    
    return redirect('all_attendance')

@user_passes_test(is_admin)
def manage_attendance_machines(request):
    """Manage attendance machines"""
    machines = AttendanceMachine.objects.all()
    
    if request.method == 'POST':
        form = AttendanceMachineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance machine added successfully!')
            return redirect('manage_attendance_machines')
    else:
        form = AttendanceMachineForm()
    
    return render(request, 'core/manage_attendance_machines.html', {
        'machines': machines,
        'form': form,
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
    """Manual attendance entry"""
    if request.method == 'POST':
        form = ManualAttendanceForm(request.POST)
        if form.is_valid():
            # Create attendance log
            AttendanceLog.objects.create(
                employee=form.cleaned_data['employee'],
                attendance_type=form.cleaned_data['attendance_type'],
                source='manual',
                timestamp=form.cleaned_data['timestamp'],
                notes=form.cleaned_data['notes']
            )
            
            # Process attendance logs
            zkt_service.process_attendance_logs()
            
            messages.success(request, 'Manual attendance entry recorded successfully!')
            return redirect('manual_attendance_entry')
    else:
        form = ManualAttendanceForm()
    
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
    leaves = Leave.objects.select_related('employee__user').order_by('-applied_at')
    # Filter by employee if provided (from employee profile)
    employee_id = request.GET.get('employee')
    if employee_id:
        try:
            employee = Employee.objects.get(user_id=employee_id)
            leaves = leaves.filter(employee=employee)
        except Employee.DoesNotExist:
            pass
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
        
        if not date_of_joining:
            date_of_joining = None
            
        employee.user.first_name = first_name
        employee.user.last_name = last_name
        employee.user.save()
        salary = request.POST.get('salary') or None
        employee.phone = phone
        employee.address = address
        employee.department_id = department_id
        employee.designation_id = designation_id
        employee.salary = salary if salary else None
        employee.date_of_joining = date_of_joining
        employee.machine_id = machine_id if machine_id else None
        employee.fingerprint_id = fingerprint_id if fingerprint_id else None
        employee.face_id = face_id if face_id else None
        employee.card_id = card_id if card_id else None
        employee.save()
        return redirect('employee_list')
    return render(request, 'core/edit_employee.html', {
        'employee': employee,
        'departments': departments,
        'designations': designations,
        'error': error
    })

@user_passes_test(is_admin)
def delete_employee(request, employee_id):
    from django.contrib.auth.models import User
    from django.db import transaction
    employee = Employee.objects.select_related('user').get(id=employee_id)
    user = employee.user
    if user == request.user:
        messages.warning(request, 'You cannot delete your own account while logged in.')
        return redirect('employee_list')
    # Delete all related objects for this user
    with transaction.atomic():
        for related_object in user._meta.get_fields():
            if (related_object.one_to_many or related_object.one_to_one) and related_object.auto_created:
                accessor_name = related_object.get_accessor_name()
                related_manager = getattr(user, accessor_name, None)
                if related_manager:
                    if related_object.one_to_one:
                        rel_obj = related_manager
                        if rel_obj:
                            rel_obj.delete()
                    else:
                        related_manager.all().delete()
        user.delete()
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
    clients = Client.objects.all()
    return render(request, 'core/client_list.html', {'clients': clients})

@user_passes_test(is_admin)
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'core/add_client.html', {'form': form})

@user_passes_test(is_admin)
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_list')
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
    if request.user.is_superuser:
        # Admin sees all projects
        projects = Project.objects.select_related('client', 'manager__department', 'manager__designation').prefetch_related('tasks').all()
    else:
        # Employees see projects where they are manager or have tasks
        try:
            employee = request.user.employee
            projects = Project.objects.filter(
                Q(manager=employee) | Q(tasks__assigned_to=employee)
            ).select_related('client', 'manager__department', 'manager__designation').prefetch_related('tasks').distinct()
        except:
            projects = Project.objects.none()
    
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
        form = TaskForm(request.POST, project=project, manager=manager)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.assigned_by = manager if manager else None
            task.save()
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
    tasks = Task.objects.filter(project=project).select_related('assigned_to', 'assigned_by').all()
    
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
    budgets = Budget.objects.select_related('category').all()
    return render(request, 'core/budget_list.html', {'budgets': budgets})

@user_passes_test(is_admin)
def budget_add(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('budget_list')
    else:
        form = BudgetForm()
    return render(request, 'core/budget_form.html', {'form': form, 'action': 'Add'})

@user_passes_test(is_admin)
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
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
    expenses = BudgetExpense.objects.select_related('budget').all()
    return render(request, 'core/budget_expense_list.html', {'expenses': expenses})

@user_passes_test(is_admin)
def budget_expense_add(request):
    if request.method == 'POST':
        form = BudgetExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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
    revenues = BudgetRevenue.objects.select_related('budget').all()
    return render(request, 'core/budget_revenue_list.html', {'revenues': revenues})

@user_passes_test(is_admin)
def budget_revenue_add(request):
    if request.method == 'POST':
        form = BudgetRevenueForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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
    assets = Asset.objects.select_related('asset_user').all()
    return render(request, 'core/asset_list.html', {'assets': assets})

@user_passes_test(is_admin)
def asset_add(request):
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company settings updated!')
            return redirect('settings_main')
    else:
        form = CompanySettingsForm(instance=settings_obj)
    return render(request, 'core/settings_main.html', {'form': form, 'active_section': 'company'})

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
    taxes = Tax.objects.all()
    form = TaxForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('taxes')
    return render(request, 'core/taxes.html', {'taxes': taxes, 'form': form})

@user_passes_test(is_admin)
def expenses(request):
    expenses = Expense.objects.all()
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('expenses')
    return render(request, 'core/expenses.html', {'expenses': expenses, 'form': form})

@user_passes_test(is_admin)
def estimates(request):
    estimates = Estimate.objects.all().prefetch_related('items', 'client', 'project')
    for estimate in estimates:
        estimate.total_amount = sum(item.amount for item in estimate.items.all())
    return render(request, 'core/estimates.html', {'estimates': estimates})

@user_passes_test(is_admin)
def invoices(request):
    return render(request, 'core/invoices.html')

@user_passes_test(is_admin)
def invoice_list(request):
    invoices = Invoice.objects.all().select_related('client', 'project', 'tax')
    for invoice in invoices:
        invoice.total_amount = sum(item.amount for item in invoice.items.all())
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
    })

# ===================== PAYROLL =====================

def _render_payslip_pdf_to_bytes(payslip, items, context_extra=None):
    base_salary = 0
    unpaid_leave_deduction = 0
    if context_extra:
        base_salary = context_extra.get('base_salary', 0)
        unpaid_leave_deduction = context_extra.get('unpaid_leave_deduction', 0)
        tax_amount = context_extra.get('tax_amount', 0)
        loan_installment_total = context_extra.get('loan_installment_total', 0)
        late_deduction = context_extra.get('late_deduction', 0)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 20 * mm

    def draw_line(text, offset_mm=7, bold=False):
        nonlocal y
        if bold:
            c.setFont('Helvetica-Bold', 11)
        else:
            c.setFont('Helvetica', 10)
        c.drawString(20 * mm, y, str(text))
        y -= offset_mm * mm

    # Header
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width / 2, height - 15 * mm, 'Salary Payslip')
    c.setFont('Helvetica', 10)
    draw_line(f"Employee: {payslip.employee.user.get_full_name() or payslip.employee.user.username}")
    draw_line(f"Designation: {payslip.employee.designation}")
    draw_line(f"Period: {payslip.period_start} - {payslip.period_end}")
    draw_line(f"Date of Payment: {payslip.date}")
    draw_line(f"Payslip No.: {payslip.id}")

    # Earnings
    y -= 4 * mm
    draw_line('Earnings', bold=True)
    draw_line(f"Base Salary: {base_salary}")
    for item in items:
        if item.item_type == PayrollItem.EARNING:
            draw_line(f"{item.name}: {item.amount}")
    draw_line(f"Total Earnings: {payslip.total_earnings + base_salary}", bold=True)

    # Deductions
    y -= 4 * mm
    draw_line('Deductions', bold=True)
    if unpaid_leave_deduction:
        draw_line(f"Unpaid Leaves: {unpaid_leave_deduction}")
    if 'late_deduction' in locals() and late_deduction:
        draw_line(f"Late Policy Deduction: {late_deduction}")
    for item in items:
        if item.item_type == PayrollItem.DEDUCTION:
            draw_line(f"{item.name}: {item.amount}")
    draw_line(f"Total Deductions: {payslip.total_deductions}", bold=True)

    # Summary
    y -= 4 * mm
    draw_line('Summary', bold=True)
    draw_line(f"Gross Pay: {payslip.gross_pay}")
    draw_line(f"Net Pay: {payslip.total}")
    # Optional extras
    # tax_amount and loan_installment_total already set above when context provided

    if tax_amount or loan_installment_total:
        y -= 4 * mm
        draw_line('Additional Deductions', bold=True)
        if tax_amount:
            draw_line(f"Income Tax: {tax_amount}")
        if loan_installment_total:
            draw_line(f"Loan Repayment: {loan_installment_total}")

    draw_line(f"Status: {payslip.get_status_display()}")

    c.showPage()
    c.save()
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
    if request.method == 'POST':
        form = PayslipEditForm(request.POST, instance=payslip)
        if form.is_valid():
            form.save()
            return redirect('admin_payslips')
    else:
        form = PayslipEditForm(instance=payslip)
    return render(request, 'core/edit_payslip.html', {'form': form})

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

@user_passes_test(is_admin)
def tax_slabs(request):
    slabs = TaxSlab.objects.all().order_by('min_income')
    form = TaxSlabForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('tax_slabs')
    return render(request, 'core/tax_slabs.html', {'slabs': slabs, 'form': form})

@user_passes_test(is_admin)
def loans(request):
    loans_qs = Loan.objects.select_related('employee__user').all()
    form = LoanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        loan = form.save()
        return redirect('loans')
    return render(request, 'core/loans.html', {'loans': loans_qs, 'form': form})

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
