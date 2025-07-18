from decimal import Decimal
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render
from django.db.models.functions import TruncWeek, TruncMonth, TruncDate
from django.shortcuts import render
from django.db.models import Sum, Exists, OuterRef
from clients.models import Client, RecentTransaction
from .models import Earnings, Staff, Transaction, Balance
from django.db.models import Sum
import csv
from django.http import HttpResponse
from core.utils import is_staff

# Profile View
@login_required
@user_passes_test(is_staff)
def profile_view(request):
    return render(request, 'dashboard/admin/profile.html', {'user': request.user})

@login_required
@user_passes_test(is_staff)
def summary_dashboard(request):
    staff_user, created = Staff.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    assigned_clients = Client.objects.filter(assigned_staff__staff=staff_user).distinct()
    transactions = Transaction.objects.all()
    balance = Balance.objects.filter(staff=staff_user).first()

    # Weekly earnings
    weekly_qs = Earnings.objects.filter(staff=staff_user, type='weekly').order_by('day_or_week')
    weekly_labels = [e.day_or_week for e in weekly_qs]
    weekly_data = [float(e.amount) for e in weekly_qs]

    # Monthly earnings
    monthly_qs = Earnings.objects.filter(staff=staff_user, type='monthly').order_by('day_or_week')
    monthly_labels = [e.day_or_week for e in monthly_qs]
    monthly_data = [float(e.amount) for e in monthly_qs]

    # Highest earnings (top 10)
    highest_qs = Earnings.objects.filter(staff=staff_user, type='highest').order_by('-amount')[:10]
    highest_labels = [e.day_or_week for e in highest_qs]
    highest_data = [float(e.amount) for e in highest_qs]

    # Lowest earnings (bottom 10)
    lowest_qs = Earnings.objects.filter(staff=staff_user, type='lowest').order_by('amount')[:10]
    lowest_labels = [e.day_or_week for e in lowest_qs]
    lowest_data = [float(e.amount) for e in lowest_qs]

    # Additional KPIs
    current_balance = balance.balance if balance else 0.00
    transactions_count = transactions.count()
    active_clients = assigned_clients.filter(recent_transactions__isnull=False).distinct().count()
    monthly_total = sum(monthly_data) if monthly_data else 0

    context = {
        'weekly_labels': weekly_labels,
        'weekly_data': weekly_data,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'highest_earning_labels': highest_labels,
        'highest_earning_data': highest_data,
        'lowest_earning_labels': lowest_labels,
        'lowest_earning_data': lowest_data,
        'current_balance': current_balance,
        'transactions': transactions_count,
        'active_clients': active_clients,
        'monthly_total': monthly_total,
    }
    return render(request, 'dashboard/summary_dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def balance(request):
    current_balance = 1234500
    account_number = '078456789'
    account_type = 'MTN Mobile Money'
    last_updated = '2024-06-01'
    withdraw_history = [
        {'name': 'John Doe', 'number': '0784567890', 'network': 'MTN', 'amount': 100000.00, 'date': '2024-05-25'},
        {'name': 'Jane Smith', 'number': '0757654321', 'network': 'Airtel', 'amount': 50000.00, 'date': '2024-05-28'},
    ]
    context = {
        'current_balance': current_balance,
        'account_number': account_number,
        'account_type': account_type,
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
def my_earning(request):
    # Filter earnings by type
    weekly_earnings_qs = Earnings.objects.filter(type='weekly')
    monthly_earnings_qs = Earnings.objects.filter(type='monthly')
    highest_earnings_qs = Earnings.objects.filter(type='highest')
    lowest_earnings_qs = Earnings.objects.filter(type='lowest')

    # Prepare data for the template
    weekly_earnings = [
        {'day': e.day_or_week, 'amount': e.amount} for e in weekly_earnings_qs
    ]
    weekly_total = sum(e.amount for e in weekly_earnings_qs)

    monthly_earnings = [
        {'week': e.day_or_week, 'amount': e.amount} for e in monthly_earnings_qs
    ]
    monthly_total = sum(e.amount for e in monthly_earnings_qs)

    highest_earnings = [
        {
            'user': e.staff.__str__() if e.staff else 'Unknown', 
            'amount': e.amount, 
            'date': e.date.strftime('%Y-%m-%d') if e.date else ''
        } 
        for e in highest_earnings_qs
    ]

    lowest_earnings = [
        {
            'user': e.staff.__str__() if e.staff else 'Unknown', 
            'amount': e.amount, 
            'date': e.date.strftime('%Y-%m-%d') if e.date else ''
        } 
        for e in lowest_earnings_qs
    ]

    context = {
        'weekly_earnings': weekly_earnings,
        'weekly_total': weekly_total,
        'monthly_earnings': monthly_earnings,
        'monthly_total': monthly_total,
        'highest_earnings': highest_earnings,
        'lowest_earnings': lowest_earnings,
    }
    return render(request, 'dashboard/my_earning.html', context)

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

