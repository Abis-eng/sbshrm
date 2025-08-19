from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib import messages
from .models import Employee, Department, Designation, Attendance, AttendanceLog, AttendanceMachine, Ticket, Client, Holiday, Leave
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from core.models import ChatMessage
from django.db.models import Q, Max
from .models import OnlineUser
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from django.db.models import Count
from .models import PayrollItem, Payslip, Employee
from .models import TaxSlab, Loan
from .models import AdvanceRequest
from django import forms
from django.db.models import Sum
from .forms import ClientForm, UserAdminForm, ProjectForm
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
from .models import Invoice, InvoiceItem
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
    from django.db.models import Count, Sum
    from django.db.models.functions import TruncMonth
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
        'expense_stats': list(expense_stats),
        'revenue_stats': list(revenue_stats),
    })

@user_passes_test(is_admin)
def employee_list(request):
    employees = Employee.objects.all()
    departments = Department.objects.all()
    designations = Designation.objects.all()
    return render(request, 'core/employee_list.html', {'employees': employees, 'departments': departments, 'designations': designations})

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
        fields = ['name']

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

@permission_required('core.view_department', raise_exception=True)
@login_required
def my_department(request):
    try:
        employee = request.user.employee
        if not employee.can_view_department:
            return HttpResponse('You are restricted from accessing department.', status=403)
        department = employee.department
    except Exception:
        department = None
    return render(request, 'core/my_department.html', {'department': department})

@permission_required('core.view_designation', raise_exception=True)
@login_required
def my_designation(request):
    try:
        employee = request.user.employee
        if not employee.can_view_designation:
            return HttpResponse('You are restricted from accessing designation.', status=403)
        designation = employee.designation
    except Exception:
        designation = None
    return render(request, 'core/my_designation.html', {'designation': designation})

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
    # Salary graph: Payroll and Payslip stats will be added here
    return render(request, 'core/employee_dashboard.html', {
        'attendance_stats': list(attendance_stats),
        'dept_counts': list(dept_counts),
        'desig_counts': list(desig_counts),
        # 'payroll_stats': ...
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def chat_user_list(request):
    user = request.user
    if user.is_superuser:
        users = User.objects.exclude(id=user.id)
    else:
        users = User.objects.filter(is_superuser=False).exclude(id=user.id)
    online_ids = set(OnlineUser.objects.values_list('user_id', flat=True))
    user_data = []
    for u in users:
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
def my_tickets(request):
    tickets = Ticket.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'core/my_tickets.html', {'tickets': tickets})

@login_required
def my_advances(request):
    try:
        employee = request.user.employee
    except Exception:
        return HttpResponse('Not an employee', status=403)
    advances = AdvanceRequest.objects.filter(employee=employee).order_by('-requested_at')
    if request.method == 'POST':
        form = AdvanceRequestForm(request.POST)
        if form.is_valid():
            advance = form.save(commit=False)
            advance.employee = employee
            advance.save()
            return redirect('my_advances')
    else:
        form = AdvanceRequestForm()
    return render(request, 'core/my_advances.html', {'advances': advances, 'form': form})

@user_passes_test(is_admin)
def manage_advances(request):
    advances = AdvanceRequest.objects.select_related('employee__user').order_by('-requested_at')
    if request.method == 'POST':
        advance_id = request.POST.get('advance_id')
        action = request.POST.get('action')
        admin_comment = request.POST.get('admin_comment', '')
        adv = get_object_or_404(AdvanceRequest, id=advance_id)
        if action == 'approve':
            adv.status = AdvanceRequest.STATUS_APPROVED
            # Create a Loan record
            installments = int(request.POST.get('desired_installments') or (adv.desired_installments or 1))
            monthly_installment = float(adv.amount) / max(1, installments)
            Loan.objects.create(
                employee=adv.employee,
                principal_amount=adv.amount,
                monthly_installment=monthly_installment,
                balance=adv.amount,
                start_date=timezone.now().date(),
                is_active=True,
            )
        elif action == 'reject':
            adv.status = AdvanceRequest.STATUS_REJECTED
        adv.reviewed_by = request.user
        adv.reviewed_at = timezone.now()
        adv.admin_comment = admin_comment
        adv.save()
        return redirect('manage_advances')
    return render(request, 'core/manage_advances.html', {'advances': advances})

@login_required
def submit_ticket(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        Ticket.objects.create(title=title, description=description, created_by=request.user)
        return redirect('my_tickets')
    return render(request, 'core/submit_ticket.html')

@user_passes_test(is_admin)
def all_tickets(request):
    tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, 'core/all_tickets.html', {'tickets': tickets})

@user_passes_test(is_admin)
def update_ticket_status(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    if request.method == 'POST':
        ticket.status = request.POST.get('status')
        ticket.save()
        return redirect('all_tickets')
    return render(request, 'core/update_ticket.html', {'ticket': ticket})

@login_required
def delete_ticket(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    if request.user.is_superuser or ticket.created_by == request.user:
        ticket.delete()
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

@user_passes_test(is_admin)
def project_list(request):
    projects = Project.objects.select_related('client', 'manager__department', 'manager__designation').all()
    return render(request, 'core/project_list.html', {'projects': projects})

@user_passes_test(is_admin)
def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'core/add_project.html', {'form': form})

@user_passes_test(is_admin)
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'core/edit_project.html', {'form': form, 'project': project})

@user_passes_test(is_admin)
def delete_project(request, project_id):
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
            return redirect(reverse('project_tasks', args=[project.id]))
    else:
        form = TaskForm(project=project, manager=manager)
    return render(request, 'core/assign_task.html', {'form': form, 'project': project})

@login_required
def project_tasks(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # Permission check
    if not request.user.is_superuser and not (project.manager and project.manager.user == request.user):
        return HttpResponseForbidden('You do not have permission to view tasks.')
    tasks = Task.objects.filter(project=project).select_related('assigned_to')
    return render(request, 'core/project_tasks.html', {'project': project, 'tasks': tasks})

@login_required
def my_tasks(request):
    try:
        employee = request.user.employee
        if not employee.can_view_tasks:
            return HttpResponse('You are restricted from accessing tasks.', status=403)
    except Employee.DoesNotExist:
        return render(request, 'core/no_employee.html')
    tasks = Task.objects.filter(assigned_to=employee).select_related('project', 'assigned_by')
    return render(request, 'core/my_tasks.html', {'tasks': tasks})

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
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
    return render(request, 'core/project_detail.html', {
        'project': project,
        'can_assign': can_assign,
        'departments': departments,
        'employees_by_dept': employees_by_dept,
        'form': form,
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
    users = User.objects.all()
    return render(request, 'core/admin_user_list.html', {'users': users})

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
    employees = Employee.objects.select_related('user').all()
    if request.method == 'POST':
        for employee in employees:
            for field, _ in features:
                key = f"{employee.id}_{field}"
                value = request.POST.get(key) == 'on'
                setattr(employee, field, value)
            employee.save()
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
