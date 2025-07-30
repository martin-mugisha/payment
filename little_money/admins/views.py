from django.views.decorators.http import require_POST
from django.contrib.admin.models import LogEntry
from decimal import Decimal
from clients.models import Client, RecentTransaction
from config.aggregator import GetBalance
from core.mailcow import sync_mailcow_mailbox
from .models import AdminCommissionHistory, AuthLog
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import AuthLog
from core.models import CustomUser
from finance.models import Payout, PlatformSettings, StaffCommissionAggregate, MonthlyEarnings, SystemEarnings
from django.db.models.functions import TruncDate
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.db.models import Sum
from finance.models import PlatformSettings, PlatformFeeHistory
from staff.models import Balance, ClientAssignment, Staff, StaffCommissionHistory, WithdrawHistory
import json
from django.contrib import messages
from core.utils import is_admin
from django.shortcuts import render
from django.utils.timezone import localtime
from finance.models import SystemEarnings
from django.db import models
from django.views.decorators.http import require_http_methods

# Admin Dashboard View
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get the most recent earnings entry
    latest_earning = SystemEarnings.objects.order_by('-last_updated').first()

    # Fetch balance from external source
    balances = GetBalance()
    response = balances.get_balance()
    balance = response.get("query_response", {}).get("Data", {}).get("Balance", 0.0)

    # Safely update balance if a record exists
    if latest_earning:
        latest_earning.balance += Decimal(balance or 0.0)
        latest_earning.save()

    # Prepare the 10 most recent earnings for chart data
    recent_earnings = SystemEarnings.objects.order_by('-last_updated')[:10][::-1]

    chart_labels = [e.last_updated.strftime("%Y-%m-%d") for e in recent_earnings]
    chart_data = [float(e.total_earnings or 0.0) for e in recent_earnings]

    return render(request, 'dashboard/admin.html', {
        'earnings': recent_earnings,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    })


@login_required
@user_passes_test(is_admin)
def finance_dashboard(request):
    # Monthly summary
    latest_monthly_earnings = MonthlyEarnings.objects.order_by('-year', '-month').first()
    monthly_earnings = latest_monthly_earnings.total_earnings if latest_monthly_earnings else 0.00
    platform_earnings = latest_monthly_earnings.total_volume if latest_monthly_earnings else 0.00

    # System earnings
    system_earnings = SystemEarnings.load()
    staff_commissions = StaffCommissionAggregate.load().total_commission
    net_platform_balance = system_earnings.net_platform_earnings
    total_balance = system_earnings.total_earnings

    # Admin personal balance (assuming profile)
    admin_balance = request.user.profile.balance if hasattr(request.user, 'profile') else 0.00

    context = {
        'monthly_earnings': monthly_earnings,
        'platform_earnings': platform_earnings,
        'total_balance': total_balance,
        'net_platform_balance': net_platform_balance,
        'staff_commissions': staff_commissions,
        'admin_balance': admin_balance,
    }
    return render(request, 'dashboard/finance.html', context)


@login_required
@user_passes_test(is_admin)
def platform_settings(request):
    settings_obj = PlatformSettings.objects.first()
    platform_fee_history = PlatformFeeHistory.objects.all().order_by('-created_at')
    staff_commission_history = StaffCommissionHistory.objects.all().order_by('-created_at')
    admin_commission_history = AdminCommissionHistory.objects.all().order_by('-created_at')

    if request.method == 'POST':
        if 'platform_fee_percent' in request.POST:
            new_fee = float(request.POST['platform_fee_percent'])
            if not settings_obj:
                settings_obj = PlatformSettings.objects.create(platform_fee_percent=new_fee)
            else:
                settings_obj.platform_fee_percent = new_fee
                settings_obj.save()
            PlatformFeeHistory.objects.create(percentage=new_fee)
            messages.success(request, f"Platform fee updated to {new_fee}%")
        elif 'staff_commission_percent' in request.POST:
            new_commission = float(request.POST['staff_commission_percent'])
            StaffCommissionHistory.objects.create(percentage=new_commission)
            messages.success(request, f"Staff commission updated to {new_commission}%")
        elif 'admin_commission_percent' in request.POST:
            new_commission = float(request.POST['admin_commission_percent'])
            AdminCommissionHistory.objects.create(percentage=new_commission)
            messages.success(request, f"Admin commission updated to {new_commission}%")
            

    return render(request, 'dashboard/platform_settings.html', {
        'settings': settings_obj,
        'platform_fee_history': platform_fee_history,
        'staff_commission_history': staff_commission_history,
        'admin_commission_history': admin_commission_history,
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

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import AdminProfileForm, AdminPasswordChangeForm

# Profile View
@login_required
@user_passes_test(is_admin)
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        if 'profile_form' in request.POST:
            profile_form = AdminProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('admins:profile_view')
            else:
                messages.error(request, 'Please correct the errors below.')
            password_form = AdminPasswordChangeForm(user)
        elif 'password_form' in request.POST:
            password_form = AdminPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
                return redirect('admins:profile_view')
            else:
                messages.error(request, 'Please correct the errors below.')
            profile_form = AdminProfileForm(instance=user)
    else:
        profile_form = AdminProfileForm(instance=user)
        password_form = AdminPasswordChangeForm(user)

    return render(request, 'dashboard/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'user': user,
    })

def force_password_change_view(request):
    user = request.user
    if request.method == 'POST':
        password_form = AdminPasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            user.is_first_login = False
            user.save()

            # 🔁 Mailcow sync here
            new_password = password_form.cleaned_data['new_password1']
            try:
                sync_mailcow_mailbox(user, new_password)
            except Exception as e:
                messages.warning(request, f"Password changed, but Mailbox sync failed: {e}")

            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('admins:admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        password_form = AdminPasswordChangeForm(user)

    return render(request, 'dashboard/force_password_change.html', {
        'password_form': password_form,
        'user': user,
    })

@login_required
@user_passes_test(is_admin)
def payouts_overview(request):
    payouts = WithdrawHistory.objects.select_related('staff').order_by('status', '-requested_on')
    return render(request, 'dashboard/payouts_overview.html', {'payouts': payouts})

@login_required
@user_passes_test(is_admin)
@require_POST
def approve_payout(request, payout_id):
    payout = get_object_or_404(WithdrawHistory, id=payout_id, status='Pending')
    balance = Balance.objects.filter(staff=payout.staff).first()

    if balance and balance.balance >= payout.amount:
        payout.status = 'Approved'
        payout.save()
        balance.balance -= payout.amount
        balance.save()
    return redirect('payouts')


@login_required
@user_passes_test(is_admin)
def assignclient(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff")
        client_id = request.POST.get("client")

        if staff_id and client_id:
            staff = Staff.objects.get(id=staff_id)
            client = Client.objects.get(id=client_id)

            # Check if this assignment already exists
            if not ClientAssignment.objects.filter(staff=staff, client=client).exists():
                ClientAssignment.objects.create(staff=staff, client=client)

        return redirect("admins:assignclient")  # Redirect after successful assignment to prevent resubmission

    # For GET request, render form with available staff and clients
    staff_list = Staff.objects.all()
    client_list = Client.objects.all()
    assignments = ClientAssignment.objects.select_related('staff', 'client').all()

    # Fetch unassigned staff and clients
    assigned_staff_ids = ClientAssignment.objects.values_list('staff_id', flat=True)
    assigned_client_ids = ClientAssignment.objects.values_list('client_id', flat=True)
    unassigned_staff = Staff.objects.exclude(id__in=assigned_staff_ids)
    unassigned_clients = Client.objects.exclude(id__in=assigned_client_ids)

    return render(request, 'dashboard/assignclient.html', {
        'staff_list': staff_list,
        'client_list': client_list,
        'assignments': assignments,
        'unassigned_staff': unassigned_staff,
        'unassigned_clients': unassigned_clients,
    })

from django.http import JsonResponse
from django.middleware.csrf import get_token

@login_required
@user_passes_test(is_admin)
def unassign_client(request, assignment_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        assignment = get_object_or_404(ClientAssignment, id=assignment_id)
        assignment.delete()
        return JsonResponse({'success': True})
    else:
        assignment = get_object_or_404(ClientAssignment, id=assignment_id)
        assignment.delete()
        return redirect('admins:assignclient')

@login_required
@user_passes_test(is_admin)
def assignments_api(request):
    assignments = ClientAssignment.objects.select_related('staff__user', 'client').all()
    assignments_data = []
    for a in assignments:
        assignments_data.append({
            'id': a.id,
            'staff_username': a.staff.user.username,
            'client_name': a.client.name,
            'assigned_at': a.assigned_at.strftime('%Y-%m-%d %H:%M'),
        })
    csrf_token = get_token(request)
    return JsonResponse({'assignments': assignments_data, 'csrf_token': csrf_token})

from django.db.models import Q, Exists, OuterRef

@login_required
@user_passes_test(is_admin)
def risk_alerts(request):
    # Clients with zero or no balance
    clients_with_no_balance = Client.objects.annotate(
        balance_sum=Sum('finances__balance')
    ).filter(Q(balance_sum__isnull=True) | Q(balance_sum=0))

    # Clients with no recent transactions
    recent_transactions = RecentTransaction.objects.filter(client=OuterRef('pk'))
    clients_with_no_transactions = Client.objects.annotate(
        has_transactions=Exists(recent_transactions)
    ).filter(has_transactions=False)

    # Combine clients who have no balance or no transactions
    clients_to_alert = clients_with_no_balance.union(clients_with_no_transactions)

    return render(request, 'dashboard/risk_alerts.html', {
        'clients_to_alert': clients_to_alert
    })

@login_required
@user_passes_test(is_admin)
def profile_admin(request):
    return render(request, 'dashboard/profile.html')

@login_required
@user_passes_test(is_admin)
def staff_user(request):
    return render(request, 'dashboard/staff_user.html')

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
