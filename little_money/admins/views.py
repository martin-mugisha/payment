from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from core.models import CustomUser
from payment.models import PlatformSettings, Transaction
from django.db.models.functions import TruncDate
import csv
from django.http import HttpResponse
from django.db.models import Sum
import json
from django.contrib import messages

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

    return render(request, 'dashboard/admin.html', {
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

    return render(request, 'dashboard/platform_settings.html', {
        'settings': settings_obj
    })

# Export Transactions CSV
@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_csv(request):
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

    return render(request, 'dashboard/staff_user.html', {
        'staff_users': staff_users
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def staff_user_delete(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, is_staff_user=True)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"Staff user '{user.username}' deleted.")
    return redirect('admins:staff_users')

# Profile View
@login_required
def profile_view(request):
    return render(request, 'dashboard/profile.html', {'user': request.user})

# Payouts Overview View
@login_required
@user_passes_test(lambda u: u.is_superuser)
def payouts_overview(request):
    # Sample payout data for demonstration
    payouts = [
        {'id': 1, 'merchant_name': 'Employee A', 'amount': 1000000, 'status': 'Pending', 'requested_on': '2025-06-20'},
        {'id': 2, 'merchant_name': 'Emploee B', 'amount': 1500000, 'status': 'Completed', 'requested_on': '2025-06-18'},
    ]
    return render(request, 'dashboard/payouts_overview.html', {'payouts': payouts})

# Placeholder views for missing admin templates
@login_required
@user_passes_test(lambda u: u.is_superuser)
def kyc_status(request):
    kyc_entries = [
        {'id': 1, 'merchant_name': 'Merchant A', 'kyc_status': 'Approved', 'last_updated': '2025-06-21'},
        {'id': 2, 'merchant_name': 'Merchant B', 'kyc_status': 'Pending', 'last_updated': '2025-06-20'},
        {'id': 3, 'merchant_name': 'Merchant C', 'kyc_status': 'Rejected', 'last_updated': '2025-06-19'},
    ]
    return render(request, 'dashboard/kyc_status.html', {'kyc_entries': kyc_entries})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def chargebacks(request):
    chargebacks = [
        {'id': 101, 'merchant_name': 'Merchant A', 'amount': 250, 'reason': 'Fraud', 'status': 'Under Review', 'created_at': '2025-06-18'},
        {'id': 102, 'merchant_name': 'Merchant B', 'amount': 500, 'reason': 'Unauthorized', 'status': 'Resolved', 'created_at': '2025-06-17'},
    ]
    return render(request, 'dashboard/chargebacks.html', {'chargebacks': chargebacks})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def risk_alerts(request):
    return render(request, 'dashboard/risk_alerts.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def profile_admin(request):
    return render(request, 'dashboard/profile.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def staff_user(request):
    return render(request, 'dashboard/staff_user.html')

