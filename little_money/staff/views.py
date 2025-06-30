from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models.functions import TruncWeek, TruncMonth, TruncDate
from .models import Withdrawal
from payment.models import Transaction
from django.db.models import Sum
import csv
from django.http import HttpResponse

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def earnings(request):
    transactions = Transaction.objects.filter(user=request.user, status='SUCCESS')

    total_staff_earnings = transactions.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00

    daily_earnings = (
        transactions
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total_earnings=Sum('total_amount'))
        .order_by('day')
    )

    weekly_earnings = (
        transactions
        .annotate(week=TruncWeek('created_at'))
        .values('week')
        .annotate(total_earnings=Sum('total_amount'))
        .order_by('week')
    )

    monthly_earnings = (
        transactions
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total_earnings=Sum('total_amount'))
        .order_by('month')
    )

    withdrawals = Withdrawal.objects.filter(user=request.user).order_by('-requested_on')

    return render(request, 'dashboard/earnings.html', {
        'daily_earnings': daily_earnings,
        'weekly_earnings': weekly_earnings,
        'monthly_earnings': monthly_earnings,
        'total_staff_earnings': total_staff_earnings,
        'withdrawals': withdrawals,
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
    })

# Export Transactions CSV
@login_required
@user_passes_test(lambda u: u.is_staff_user)
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    return response
# Profile View
@login_required
def profile_view(request):
    return render(request, 'dashboard/admin/profile.html', {'user': request.user})

# Placeholder views for missing staff templates
@login_required
@user_passes_test(lambda u: u.is_staff_user)
def merchant_list(request):
    return render(request, 'dashboard/merchant_list.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def profile_staff(request):
    return render(request, 'dashboard/profile_staff.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def earnings(request):
    return render(request, 'dashboard/earnings.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def dispute_management(request):
    disputes = [
        {'id': 1, 'transaction_id': 'TXN10001', 'reason': 'Product not delivered', 'status': 'Open', 'created_at': '2025-06-20'},
        {'id': 2, 'transaction_id': 'TXN10002', 'reason': 'Duplicate charge', 'status': 'Closed', 'created_at': '2025-06-19'},
    ]
    return render(request, 'dashboard/dispute_management.html', {'disputes': disputes})


@login_required
@user_passes_test(lambda u: u.is_staff_user)
def refund_processing(request):
    return render(request, 'dashboard/refund_processing.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def failed_transactions(request):
    failed_transactions = Transaction.objects.filter(user=request.user, status='FAILED')
    return render(request, 'dashboard/failed_transactions.html', {
        'failed_transactions': failed_transactions
    })

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def support_tickets(request):
    tickets = [
        {'id': 501, 'subject': 'Refund request', 'status': 'Pending', 'created_at': '2025-06-22'},
        {'id': 502, 'subject': 'Account issue', 'status': 'Resolved', 'created_at': '2025-06-21'},
    ]
    return render(request, 'dashboard/support_tickets.html', {'tickets': tickets})


@login_required
@user_passes_test(lambda u: u.is_staff_user)
def suspicious_activity(request):
    activities = [
        {'id': 1, 'activity': 'Multiple failed login attempts', 'user': 'staff1', 'timestamp': '2025-06-23 10:30'},
        {'id': 2, 'activity': 'Unusual withdrawal pattern', 'user': 'staff2', 'timestamp': '2025-06-22 14:15'},
    ]
    return render(request, 'dashboard/suspicious_activity.html', {'activities': activities})

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def audit_logs(request):
    logs = [
        {'id': 1, 'action': 'Updated profile', 'user': 'staff1', 'timestamp': '2025-06-23 09:45'},
        {'id': 2, 'action': 'Approved transaction', 'user': 'staff2', 'timestamp': '2025-06-22 16:10'},
    ]
    return render(request, 'dashboard/audit_logs.html', {'logs': logs})


@login_required
@user_passes_test(lambda u: u.is_staff_user)
def base_staff(request):
    return render(request, 'dashboard/base_staff.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def staff(request):
    return render(request, 'dashboard/staff.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def payout_management(request):
    payouts = [
        {'id': 1, 'merchant': 'Employee 1', 'amount': 1200000, 'status': 'Processing', 'requested_on': '2025-06-20'},
        {'id': 2, 'merchant': 'Emploee 2', 'amount': 800000, 'status': 'Completed', 'requested_on': '2025-06-19'},
    ]
    return render(request, 'dashboard/payout_management.html', {'payouts': payouts})

# Staff Dashboard with Chart Data
@login_required
@user_passes_test(lambda u: u.is_staff_user)
def staff_dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'dashboard/staff.html', {
        'transactions': transactions,
    })