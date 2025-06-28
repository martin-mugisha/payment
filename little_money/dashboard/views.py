from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from core.models import CustomUser
from payment.models import PlatformSettings, Transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncDate
import json

def index(request):
    return render(request, 'index.html')

# Admin Dashboard - Transactions with Chart Data
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    transactions = Transaction.objects.all()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(created_at__date__lte=end_date)

    total_platform_earnings = transactions.filter(status='SUCCESS').aggregate(Sum('platform_fee_amount'))['platform_fee_amount__sum'] or 0.00

    # CHART DATA
    daily_earnings = (
        transactions.filter(status='SUCCESS')
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total_fee=Sum('platform_fee_amount'))
        .order_by('day')
    )

    chart_labels = [entry['day'].strftime("%Y-%m-%d") for entry in daily_earnings]
    chart_data = [float(entry['total_fee']) for entry in daily_earnings]

    return render(request, 'dashboard/admin/admin.html', {
        'transactions': transactions,
        'total_platform_earnings': total_platform_earnings,
        'start_date': start_date,
        'end_date': end_date,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    })

# Platform Fee Settings
@login_required
@user_passes_test(lambda u: u.is_superuser)
def platform_settings(request):
    settings_obj = PlatformSettings.objects.first()

    if request.method == 'POST':
        new_fee = float(request.POST['platform_fee_percent'])
        if not settings_obj:
            settings_obj = PlatformSettings.objects.create(platform_fee_percent=new_fee)
        else:
            settings_obj.platform_fee_percent = new_fee
            settings_obj.save()
        messages.success(request, f"Platform fee updated to {new_fee}%")

    return render(request, 'dashboard/admin/platform_settings.html', {
        'settings': settings_obj
    })

# Export Transactions CSV
@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_transactions_csv(request):
    transactions = Transaction.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Transaction ID', 'User', 'Base Amount', 'Platform Fee %', 'Platform Fee Amount', 'Total', 'Status', 'Created At'])

    for txn in transactions:
        writer.writerow([
            txn.transaction_id,
            txn.user.username,
            txn.base_amount,
            txn.platform_fee_percent,
            txn.platform_fee_amount,
            txn.total_amount,
            txn.status,
            txn.created_at
        ])

    return response

# Staff Dashboard with Chart Data
@login_required
@user_passes_test(lambda u: u.is_staff_user)
def staff_dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'dashboard/staff/staff.html', {
        'transactions': transactions,
    })

from django.db.models.functions import TruncWeek, TruncMonth
from dashboard.models import Withdrawal

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

    return render(request, 'dashboard/staff/earnings.html', {
        'daily_earnings': daily_earnings,
        'weekly_earnings': weekly_earnings,
        'monthly_earnings': monthly_earnings,
        'total_staff_earnings': total_staff_earnings,
        'withdrawals': withdrawals,
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
    })

# Manage Staff Users (Admin Only)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def staff_users(request):
    staff_users = CustomUser.objects.filter(is_staff_user=True)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            if not CustomUser.objects.filter(username=username).exists():
                new_user = CustomUser.objects.create_user(username=username, password=password)
                new_user.is_staff_user = True
                new_user.save()
                messages.success(request, f"Staff user '{username}' created.")
            else:
                messages.error(request, "Username already exists.")

    return render(request, 'dashboard/admin/staff_user.html', {
        'staff_users': staff_users
    })

# Login View
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif user.is_staff_user:
                return redirect('staff_dashboard')
            else:
                messages.error(request, "Unauthorized user.")
                logout(request)
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'dashboard/login.html')

# Logout View
def user_logout(request):
    logout(request)
    return redirect('login')

# Profile View
@login_required
def profile_view(request):
    return render(request, 'dashboard/admin/profile.html', {'user': request.user})

# Payouts Overview View
@login_required
@user_passes_test(lambda u: u.is_superuser)
def payouts_overview(request):
    # Sample payout data for demonstration
    payouts = [
        {'id': 1, 'merchant_name': 'Employee A', 'amount': 1000000, 'status': 'Pending', 'requested_on': '2025-06-20'},
        {'id': 2, 'merchant_name': 'Emploee B', 'amount': 1500000, 'status': 'Completed', 'requested_on': '2025-06-18'},
    ]
    return render(request, 'dashboard/admin/payouts_overview.html', {'payouts': payouts})

# Placeholder views for missing admin templates
@login_required
@user_passes_test(lambda u: u.is_superuser)
def kyc_status(request):
    kyc_entries = [
        {'id': 1, 'merchant_name': 'Merchant A', 'kyc_status': 'Approved', 'last_updated': '2025-06-21'},
        {'id': 2, 'merchant_name': 'Merchant B', 'kyc_status': 'Pending', 'last_updated': '2025-06-20'},
        {'id': 3, 'merchant_name': 'Merchant C', 'kyc_status': 'Rejected', 'last_updated': '2025-06-19'},
    ]
    return render(request, 'dashboard/admin/kyc_status.html', {'kyc_entries': kyc_entries})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def chargebacks(request):
    chargebacks = [
        {'id': 101, 'merchant_name': 'Merchant A', 'amount': 250, 'reason': 'Fraud', 'status': 'Under Review', 'created_at': '2025-06-18'},
        {'id': 102, 'merchant_name': 'Merchant B', 'amount': 500, 'reason': 'Unauthorized', 'status': 'Resolved', 'created_at': '2025-06-17'},
    ]
    return render(request, 'dashboard/admin/chargebacks.html', {'chargebacks': chargebacks})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def risk_alerts(request):
    return render(request, 'dashboard/admin/risk_alerts.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def profile_admin(request):
    return render(request, 'dashboard/admin/profile.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def staff_user(request):
    return render(request, 'dashboard/admin/staff_user.html')

# Placeholder views for missing staff templates
@login_required
@user_passes_test(lambda u: u.is_staff_user)
def merchant_list(request):
    return render(request, 'dashboard/staff/merchant_list.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def profile_staff(request):
    return render(request, 'dashboard/staff/profile_staff.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def earnings(request):
    return render(request, 'dashboard/staff/earnings.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def dispute_management(request):
    disputes = [
        {'id': 1, 'transaction_id': 'TXN10001', 'reason': 'Product not delivered', 'status': 'Open', 'created_at': '2025-06-20'},
        {'id': 2, 'transaction_id': 'TXN10002', 'reason': 'Duplicate charge', 'status': 'Closed', 'created_at': '2025-06-19'},
    ]
    return render(request, 'dashboard/staff/dispute_management.html', {'disputes': disputes})


@login_required
@user_passes_test(lambda u: u.is_staff_user)
def refund_processing(request):
    return render(request, 'dashboard/staff/refund_processing.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def failed_transactions(request):
    failed_transactions = Transaction.objects.filter(user=request.user, status='FAILED')
    return render(request, 'dashboard/staff/failed_transactions.html', {
        'failed_transactions': failed_transactions
    })

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def support_tickets(request):
    tickets = [
        {'id': 501, 'subject': 'Refund request', 'status': 'Pending', 'created_at': '2025-06-22'},
        {'id': 502, 'subject': 'Account issue', 'status': 'Resolved', 'created_at': '2025-06-21'},
    ]
    return render(request, 'dashboard/staff/support_tickets.html', {'tickets': tickets})


@login_required
@user_passes_test(lambda u: u.is_staff_user)
def suspicious_activity(request):
    activities = [
        {'id': 1, 'activity': 'Multiple failed login attempts', 'user': 'staff1', 'timestamp': '2025-06-23 10:30'},
        {'id': 2, 'activity': 'Unusual withdrawal pattern', 'user': 'staff2', 'timestamp': '2025-06-22 14:15'},
    ]
    return render(request, 'dashboard/staff/suspicious_activity.html', {'activities': activities})

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def audit_logs(request):
    logs = [
        {'id': 1, 'action': 'Updated profile', 'user': 'staff1', 'timestamp': '2025-06-23 09:45'},
        {'id': 2, 'action': 'Approved transaction', 'user': 'staff2', 'timestamp': '2025-06-22 16:10'},
    ]
    return render(request, 'dashboard/staff/audit_logs.html', {'logs': logs})


@login_required
@user_passes_test(lambda u: u.is_staff_user)
def base_staff(request):
    return render(request, 'dashboard/staff/base_staff.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def staff(request):
    return render(request, 'dashboard/staff/staff.html')

@login_required
@user_passes_test(lambda u: u.is_staff_user)
def payout_management(request):
    payouts = [
        {'id': 1, 'merchant': 'Employee 1', 'amount': 1200000, 'status': 'Processing', 'requested_on': '2025-06-20'},
        {'id': 2, 'merchant': 'Emploee 2', 'amount': 800000, 'status': 'Completed', 'requested_on': '2025-06-19'},
    ]
    return render(request, 'dashboard/staff/payout_management.html', {'payouts': payouts})
