from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models.functions import TruncWeek, TruncMonth, TruncDate
from .models import Withdrawal
from django.db.models import Sum
import csv
from django.http import HttpResponse
from core.utils import is_staff

@login_required
@user_passes_test(is_staff)
def earnings(request):
    # Dummy earnings data for testing
    earnings_data = [
        {'date': '2025-07-01', 'amount': 500000, 'type': 'Commission'},
        {'date': '2025-07-02', 'amount': 250000, 'type': 'Bonus'},
        {'date': '2025-07-03', 'amount': 100000, 'type': 'Commission'},
    ]
    total_earnings = sum(item['amount'] for item in earnings_data)
    chart_labels = [item['date'] for item in earnings_data]
    chart_data = [item['amount'] for item in earnings_data]

    return render(request, 'dashboard/earnings.html', {
        'earnings': earnings_data,
        'total_earnings': total_earnings,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })

# Export Transactions CSV
@login_required
@user_passes_test(is_staff)
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    return response
# Profile View
@login_required
def profile_view(request):
    return render(request, 'dashboard/admin/profile.html', {'user': request.user})

# Placeholder views for missing staff templates
@login_required
@user_passes_test(is_staff)
def merchant_list(request):
    merchants = [
        {'id': 1, 'name': 'Merchant A', 'joined': '2025-05-10', 'status': 'Active'},
        {'id': 2, 'name': 'Merchant B', 'joined': '2025-06-01', 'status': 'Inactive'},
    ]
    return render(request, 'dashboard/merchant_list.html', {'merchants': merchants})


@login_required
@user_passes_test(is_staff)
def profile_staff(request):
    return render(request, 'dashboard/profile_staff.html')

@login_required
@user_passes_test(is_staff)
def earnings(request):
    return render(request, 'dashboard/earnings.html')

@login_required
@user_passes_test(is_staff)
def dispute_management(request):
    disputes = [
        {'id': 1, 'transaction_id': 'TXN10001', 'reason': 'Product not delivered', 'status': 'Open', 'created_at': '2025-06-20'},
        {'id': 2, 'transaction_id': 'TXN10002', 'reason': 'Duplicate charge', 'status': 'Closed', 'created_at': '2025-06-19'},
    ]
    return render(request, 'dashboard/dispute_management.html', {'disputes': disputes})


@login_required
@user_passes_test(is_staff)
def refund_processing(request):
    return render(request, 'dashboard/refund_processing.html')

@login_required
@user_passes_test(is_staff)
def failed_transactions(request):
    failed_transactions = Transaction.objects.filter(user=request.user, status='FAILED')
    return render(request, 'dashboard/failed_transactions.html', {
        'failed_transactions': failed_transactions
    })

@login_required
@user_passes_test(is_staff)
def support_tickets(request):
    tickets = [
        {'id': 501, 'subject': 'Refund request', 'status': 'Pending', 'created_at': '2025-06-22'},
        {'id': 502, 'subject': 'Account issue', 'status': 'Resolved', 'created_at': '2025-06-21'},
    ]
    return render(request, 'dashboard/support_tickets.html', {'tickets': tickets})


@login_required
@user_passes_test(is_staff)
def suspicious_activity(request):
    activities = [
        {'id': 1, 'activity': 'Multiple failed login attempts', 'user': 'staff1', 'timestamp': '2025-06-23 10:30'},
        {'id': 2, 'activity': 'Unusual withdrawal pattern', 'user': 'staff2', 'timestamp': '2025-06-22 14:15'},
    ]
    return render(request, 'dashboard/suspicious_activity.html', {'activities': activities})

@login_required
@user_passes_test(is_staff)
def audit_logs(request):
    logs = [
        {'id': 1, 'action': 'Updated profile', 'user': 'staff1', 'timestamp': '2025-06-23 09:45'},
        {'id': 2, 'action': 'Approved transaction', 'user': 'staff2', 'timestamp': '2025-06-22 16:10'},
    ]
    return render(request, 'dashboard/audit_logs.html', {'logs': logs})


@login_required
@user_passes_test(is_staff)
def base_staff(request):
    return render(request, 'dashboard/base_staff.html')

@login_required
@user_passes_test(is_staff)
def staff(request):
    return render(request, 'dashboard/staff.html')

@login_required
@user_passes_test(is_staff)
def payout_management(request):
    payouts = [
        {'id': 1, 'merchant': 'Employee 1', 'amount': 1200000, 'status': 'Processing', 'requested_on': '2025-06-20'},
        {'id': 2, 'merchant': 'Emploee 2', 'amount': 800000, 'status': 'Completed', 'requested_on': '2025-06-19'},
    ]
    return render(request, 'dashboard/payout_management.html', {'payouts': payouts})

# Staff Dashboard with Chart Data
@login_required
@user_passes_test(is_staff)
def staff_dashboard(request):
    # Dummy transactions data for testing
    transactions = [
        {'id': 101, 'date': '2025-07-01', 'amount': 150000, 'status': 'SUCCESS', 'type': 'Withdrawal'},
        {'id': 102, 'date': '2025-07-02', 'amount': 50000, 'status': 'FAILED', 'type': 'Deposit'},
        {'id': 103, 'date': '2025-07-03', 'amount': 200000, 'status': 'SUCCESS', 'type': 'Withdrawal'},
    ]
    total_transactions = len(transactions)
    total_success = sum(1 for t in transactions if t['status'] == 'SUCCESS')
    total_failed = sum(1 for t in transactions if t['status'] == 'FAILED')
    total_amount = sum(t['amount'] for t in transactions)

    # Example chart data
    chart_labels = [t['date'] for t in transactions]
    chart_data = [t['amount'] for t in transactions]

    return render(request, 'dashboard/staff.html', {
        'transactions': transactions,
        'total_transactions': total_transactions,
        'total_success': total_success,
        'total_failed': total_failed,
        'total_amount': total_amount,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })
