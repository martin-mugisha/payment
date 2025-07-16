from django.contrib.admin.models import LogEntry
from .models import AuthLog
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import AuthLog
from core.models import CustomUser
from finance.models import PlatformSettings
from django.db.models.functions import TruncDate
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.db.models import Sum
import json
from django.contrib import messages
from core.utils import is_admin
from django.shortcuts import render
from django.utils.timezone import localtime
from finance.models import SystemEarnings
from django.db import models

# Admin Dashboard View
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Fetch all system earnings/statistics
    earnings = SystemEarnings.objects.all().order_by('-last_updated')
    total_revenue = earnings.aggregate(total=models.Sum('total_earnings'))['total'] or 0.00

    # Prepare chart data for the last 10 records (or whatever makes sense)
    recent_earnings = earnings[:10][::-1]  # reverse for chronological order
    chart_labels = [e.last_updated.strftime("%Y-%m-%d") for e in recent_earnings]
    chart_data = [float(e.total_earnings) for e in recent_earnings]

    return render(request, 'dashboard/admin.html', {
        'earnings': earnings,
        'total_revenue': total_revenue,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    })

# Platform Fee Settings
@login_required
@user_passes_test(is_admin)
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


@login_required
@user_passes_test(is_admin)
def staff_users(request):
    staff_users = CustomUser.objects.filter(is_active=True)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'halfadmin')  # default to halfadmin

        if username and password:
            if not CustomUser.objects.filter(username=username).exists():
                new_user = CustomUser.objects.create_user(username=username, password=password)
                new_user.is_staff_user = True
                new_user.role = role  
                new_user.save()
                messages.success(request, f"Staff user '{username}' with role '{role}' created.")
            else:
                messages.error(request, "Username already exists.")

    return render(request, 'dashboard/staff_user.html', {
        'staff_users': staff_users
    })

@login_required
@user_passes_test(is_admin)
def staff_user_delete(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, is_active=True)
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
@user_passes_test(is_admin)
def payouts_overview(request):
    # Sample payout data for demonstration
    payouts = [
        {'id': 1, 'merchant_name': 'Employee A', 'amount': 1000000, 'status': 'Pending', 'requested_on': '2025-06-20'},
        {'id': 2, 'merchant_name': 'Emploee B', 'amount': 1500000, 'status': 'Completed', 'requested_on': '2025-06-18'},
    ]
    return render(request, 'dashboard/payouts_overview.html', {'payouts': payouts})

# Placeholder views for missing admin templates
@login_required
@user_passes_test(is_admin)
def kyc_status(request):
    kyc_entries = [
        {'id': 1, 'merchant_name': 'Merchant A', 'kyc_status': 'Approved', 'last_updated': '2025-06-21'},
        {'id': 2, 'merchant_name': 'Merchant B', 'kyc_status': 'Pending', 'last_updated': '2025-06-20'},
        {'id': 3, 'merchant_name': 'Merchant C', 'kyc_status': 'Rejected', 'last_updated': '2025-06-19'},
    ]
    return render(request, 'dashboard/kyc_status.html', {'kyc_entries': kyc_entries})


@login_required
@user_passes_test(is_admin)
def chargebacks(request):
    chargebacks = [
        {'id': 101, 'merchant_name': 'Merchant A', 'amount': 250, 'reason': 'Fraud', 'status': 'Under Review', 'created_at': '2025-06-18'},
        {'id': 102, 'merchant_name': 'Merchant B', 'amount': 500, 'reason': 'Unauthorized', 'status': 'Resolved', 'created_at': '2025-06-17'},
    ]
    return render(request, 'dashboard/chargebacks.html', {'chargebacks': chargebacks})


@login_required
@user_passes_test(is_admin)
def risk_alerts(request):
    return render(request, 'dashboard/risk_alerts.html')

@login_required
@user_passes_test(is_admin)
def profile_admin(request):
    return render(request, 'dashboard/profile.html')

@login_required
@user_passes_test(is_admin)
def staff_user(request):
    return render(request, 'dashboard/staff_user.html')

"""@login_required
@user_passes_test(is_admin)  
def activity_logs(request):
    # Fetch all log entries ordered by action time descending
    logs = LogEntry.objects.select_related('user').order_by('-action_time')[:100]  # limit to last 100 entries

    # Pass logs to template
    return render(request, 'dashboard/activity_logs.html', {'logs': logs})
"""

@login_required
@user_passes_test(is_admin)
def activity_logs(request):
    admin_logs = list(LogEntry.objects.select_related('user', 'content_type').all())
    auth_logs = list(AuthLog.objects.select_related('user').all())

    # Annotate each with a type
    for log in admin_logs:
        log.log_type = 'logentry'
    for log in auth_logs:
        log.log_type = 'authlog'

    # Separate logs by user role
    staff_logs = []
    client_logs = []

    for log in admin_logs + auth_logs:
        user = getattr(log, 'user', None)
        if user and hasattr(user, 'role'):
            if user.role == 'staff':
                staff_logs.append(log)
            elif user.role == 'client':
                client_logs.append(log)
        else:
            # Logs without user or unknown role can be added to staff_logs by default
            staff_logs.append(log)

    # Sort logs by timestamp descending
    staff_logs = sorted(staff_logs, key=lambda x: x.timestamp if hasattr(x, 'timestamp') else x.action_time, reverse=True)
    client_logs = sorted(client_logs, key=lambda x: x.timestamp if hasattr(x, 'timestamp') else x.action_time, reverse=True)

    return render(request, 'dashboard/activity_logs.html', {'staff_logs': staff_logs, 'client_logs': client_logs})
