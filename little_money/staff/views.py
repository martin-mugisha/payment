from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models.functions import TruncWeek, TruncMonth, TruncDate
from .models import Withdrawal
from django.db.models import Sum
import csv
from django.http import HttpResponse
from core.utils import is_staff

# Profile View
@login_required
def profile_view(request):
    return render(request, 'dashboard/admin/profile.html', {'user': request.user})

@login_required
def summary_dashboard(request):
    # Sample data for charts
    weekly_labels = ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7']
    weekly_data = [100000, 150000, 70000, 120000, 200000, 180000, 250000]

    monthly_labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    monthly_data = [5000000, 6000000, 5500000, 7000000]

    balance = 1234500
    transactions_count = 150
    active_clients = 38
    earnings = 3000000

    context = {
        'weekly_labels': weekly_labels,
        'weekly_data': weekly_data,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'current_balance': balance,
        'transactions': transactions_count,
        'active_clients': active_clients,
        'monthly_total': earnings,

    }
    return render(request, 'dashboard/summary_dashboard.html', context)

@login_required
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
def transactions(request):
    transactions_list = [
        {'name': 'John Doe', 'number': '07844567890', 'network': 'MTN', 'status': 'Completed', 'reason': 'Payment', 'amount': 1000000.00},
        {'name': 'Jane Smith', 'number': '0757654321', 'network': 'Airtel', 'status': 'Pending', 'reason': 'Refund', 'amount': 500000.00},
        {'name': 'Bob Johnson', 'number': '0772334455', 'network': 'MTN', 'status': 'Failed', 'reason': 'Chargeback', 'amount': 750000.00},
    ]
    context = {
        'transactions': transactions_list,
    }
    return render(request, 'dashboard/transaction.html', context)

@login_required
def my_earning(request):
    weekly_earnings = [
        {'day': 'Monday', 'amount': 150000.00},
        {'day': 'Tuesday', 'amount': 180000.00},
        {'day': 'Wednesday', 'amount': 200000.00},
        {'day': 'Thursday', 'amount': 170000.00},
        {'day': 'Friday', 'amount': 220000.00},
        {'day': 'Saturday', 'amount': 130000.00},
        {'day': 'Sunday', 'amount': 150000.00},
    ]
    weekly_total = sum(item['amount'] for item in weekly_earnings)

    monthly_earnings = [
        {'week': 'Week 1', 'amount': 3000000.00},
        {'week': 'Week 2', 'amount': 3500000.00},
        {'week': 'Week 3', 'amount': 2800000.00},
        {'week': 'Week 4', 'amount': 2700000.00},
    ]
    monthly_total = sum(item['amount'] for item in monthly_earnings)

    highest_earnings = [
        {'user': 'Arme Corp', 'amount': 500000.00, 'date': '2024-05-20'},
        {'user': 'Simple Loans', 'amount': 450000.00, 'date': '2024-05-18'},
    ]

    lowest_earnings = [
        {'user': 'Bob Johnson', 'amount': 20000.00, 'date': '2024-05-22'},
        {'user': 'Alice Namara', 'amount': 25000.00, 'date': '2024-05-19'},
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
def clients(request):
    total_clients = 45
    active_clients = 38
    inactive_clients = 7
    
    clients_list = [
        {'name': 'Acme Corp', 'business_type': 'Retail', 'id': '001', 'status': 'Active', 'balance': 12345000.67},
        {'name': 'Beta LLC', 'business_type': 'Wholesale', 'id': '002', 'status': 'Inactive', 'balance': 8765000.43},
    ]
    total_balance = sum(client['balance'] for client in clients_list)
    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'total_balance': total_balance,
        'clients': clients_list,
    }
    return render(request, 'dashboard/clients.html', context)
