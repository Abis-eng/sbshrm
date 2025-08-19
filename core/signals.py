from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Q, Sum
from django.conf import settings
from core.models import MonthlyPayrollRun, Employee, PayrollItem, Payslip, Attendance, TaxSlab, Loan
from core.views import _render_payslip_pdf_to_bytes
from django.core.files.base import ContentFile


@receiver(post_migrate)
def generate_payslips_if_month_ended(sender, **kwargs):
    # Only run for our core app
    if sender.name != 'core':
        return
    today = timezone.now().date()
    # If today is the first 3 days of a new month, generate for previous month (idempotent)
    if today.day > 3:
        return
    first_day_this_month = date(today.year, today.month, 1)
    period_end = first_day_this_month - timedelta(days=1)
    period_start = date(period_end.year, period_end.month, 1)
    # Check if already run
    if MonthlyPayrollRun.objects.filter(period_start=period_start, period_end=period_end).exists():
        return

    employees = Employee.objects.select_related('user').all()
    created = 0
    for employee in employees:
        if Payslip.objects.filter(employee=employee, period_start=period_start, period_end=period_end).exists():
            continue
        base_salary = float(employee.salary or 0)

        period_items = PayrollItem.objects.filter(employee=employee).filter(
            (
                Q(is_recurring=False) & Q(date__gte=period_start, date__lte=period_end)
            ) | (
                Q(is_recurring=True) & (
                    (Q(start_date__lte=period_end) | Q(start_date__isnull=True)) & (Q(end_date__gte=period_start) | Q(end_date__isnull=True))
                )
            )
        )
        total_earnings = float(period_items.filter(item_type=PayrollItem.EARNING).aggregate(s=Sum('amount'))['s'] or 0)
        total_deductions = float(period_items.filter(item_type=PayrollItem.DEDUCTION).aggregate(s=Sum('amount'))['s'] or 0)

        late_days = Attendance.objects.filter(employee=employee, date__gte=period_start, date__lte=period_end, is_late=True).count()
        late_day_equivalents = late_days // 3
        late_deduction = round((base_salary / 30.0) * late_day_equivalents, 2) if base_salary and late_day_equivalents else 0
        if late_deduction:
            total_deductions += late_deduction

        absent_days = Attendance.objects.filter(employee=employee, date__gte=period_start, date__lte=period_end, status='absent').count()
        unpaid_leave_deduction = round((base_salary / 30.0) * absent_days, 2) if base_salary and absent_days else 0
        if unpaid_leave_deduction:
            total_deductions += unpaid_leave_deduction

        taxable_income = base_salary + total_earnings
        slab = TaxSlab.objects.order_by('min_income').filter(min_income__lte=taxable_income).filter(Q(max_income__gte=taxable_income) | Q(max_income__isnull=True)).first()
        tax_amount = 0
        if slab:
            tax_amount = round((taxable_income * float(slab.rate_percent) / 100.0) + float(slab.fixed_deduction), 2)
            if tax_amount:
                total_deductions += tax_amount

        loan_installment_total = 0
        for loan in Loan.objects.filter(employee=employee, is_active=True):
            if float(loan.balance) > 0 and float(loan.monthly_installment) > 0:
                installment = float(loan.monthly_installment)
                if installment > float(loan.balance):
                    installment = float(loan.balance)
                loan_installment_total += installment
        if loan_installment_total:
            total_deductions += loan_installment_total

        gross_pay = base_salary + total_earnings
        net_total = gross_pay - total_deductions

        payslip = Payslip.objects.create(
            employee=employee,
            date=today,
            period_start=period_start,
            period_end=period_end,
            gross_pay=gross_pay,
            total_earnings=total_earnings,
            total_deductions=total_deductions,
            total=net_total,
            status=Payslip.STATUS_PROCESSED,
        )
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
        created += 1

    if created:
        MonthlyPayrollRun.objects.create(period_start=period_start, period_end=period_end)

