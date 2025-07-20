from calendar import monthrange
from datetime import date, timedelta
import datetime
from decimal import Decimal
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models.functions import TruncWeek, TruncMonth, TruncDate
from django.shortcuts import render
from django.db.models import Sum, Exists, OuterRef
from clients.models import Client, RecentTransaction
from .models import Staff, Transaction, Balance, WithdrawHistory
from django.db.models import Sum
from django.utils.timezone import localdate
from django.http import HttpResponse
from core.utils import is_staff

# Profile View
@login_required
@user_passes_test(is_staff)
def profile_view(request):
    return render(request, 'dashboard/admin/profile.html', {'user': request.user})

def is_all_zero(data):
    """Check if all values in the data list are zero."""
    return all(float(x) == 0 for x in data)

@login_required
@user_passes_test(is_staff)
def summary_dashboard(request):
    staff_user, created = Staff.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    assigned_clients = Client.objects.filter(assigned_staff__staff=staff_user).distinct()
    transactions = Transaction.objects.all()
    balance = Balance.objects.filter(staff=staff_user).first()

    # KPIs
    current_balance = balance.balance if balance else 0.00
    transactions_count = transactions.count()
    active_clients = assigned_clients.filter(recent_transactions__isnull=False).distinct().count()



    today = localdate()
    current_weekday = (today.weekday() + 1) % 7  # Sunday = 0

    # ------------------ WEEKLY PAYMENTS -------------------
    week_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    week_start = today - datetime.timedelta(days=current_weekday)
    week_data = []

    for i in range(7):
        day = week_start + datetime.timedelta(days=i) 
        if day <= today:
            count = transactions.filter(created_at__date=day).count()
            week_labels.append(day.strftime('%A'))  # Sunday, Monday, ...
            week_data.append(count)

    week_transaction ={
        'labels':week_labels,
        'data': week_data if not is_all_zero(week_data) else [],
    }
    # === MONTHLY TRANSACTIONS ===
    start_of_month = today.replace(day=1)
    days_in_month = monthrange(today.year, today.month)[1]
    monthly_labels = []
    monthly_data = []

    for day in range(1, days_in_month + 1):
        date_day = start_of_month.replace(day=day)
        count = transactions.filter(created_at__date=date_day).count()
        monthly_labels.append(str(day))
        monthly_data.append(count)

    context = {
        'current_balance': current_balance,
        'transactions': transactions_count,
        'active_clients': active_clients,
        'week_transaction': week_transaction,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
    }

    return render(request, 'dashboard/summary_dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def balance(request):
    staff_user, _ = Staff.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    balance_obj = Balance.objects.filter(staff=staff_user).first()
    current_balance = balance_obj.balance if balance_obj else 0.00
    last_updated = balance_obj.last_updated if balance_obj else None

    if request.method == "POST":
        name = request.POST.get("name")
        number = request.POST.get("number")
        amount = float(request.POST.get("amount"))
        network = request.POST.get("network")

        if amount <= current_balance:
            # Don't deduct balance here yet — admin will approve it
            WithdrawHistory.objects.create(
                staff=staff_user,
                name=name,
                number=number,
                network=network,
                amount=amount,
                status='Pending'
            )
            return redirect('staff:balance')

    withdraw_history = WithdrawHistory.objects.filter(staff=staff_user).order_by('-requested_on')

    context = {
        'current_balance': current_balance,
        'last_updated': last_updated,
        'withdraw_history': withdraw_history,
    }
    return render(request, 'dashboard/balance.html', context)

@login_required
@user_passes_test(is_staff)
def transactions(request):
    transactions_list = Transaction.objects.all()

    context = {
        'transactions': transactions_list,
    }
    return render(request, 'dashboard/transaction.html', context)

@login_required
@user_passes_test(is_staff)
def clients(request):
    staff_user, created = Staff.objects.get_or_create(user=request.user, defaults={'name': request.user.username})

    assigned_clients = Client.objects.filter(assigned_staff__staff=staff_user).distinct()

    total_clients = assigned_clients.count()
    active_clients = assigned_clients.filter(recent_transactions__isnull=False).distinct().count()
    inactive_clients = assigned_clients.filter(recent_transactions__isnull=True).distinct().count()

    # Compute total balance manually from finance
    total_balance = sum((Decimal(str(client.balance)) for client in assigned_clients), Decimal(0))

    # Build client data list manually since balance is a property
    clients_list = [{
        'id': client.id,
        'name': client.name,
        'business_type': client.business_type,
        'status': client.status,
        'balance': client.balance,
    } for client in assigned_clients]

    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'total_balance': total_balance,
        'clients': clients_list,
    }

    return render(request, 'dashboard/clients.html', context)

