from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Client, Finances
from django.utils.timezone import now
from core.utils import is_client
import openpyxl
from django.contrib import messages
from django.shortcuts import redirect
from core.utils import format_phone_number

@login_required
@user_passes_test(is_client)
def overview_dashboard(request):
    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    finances = Finances.objects.filter(client=client).first()
    # Mock data for overview with payment methods reflecting MTN and Airtel
    # Added weekly and monthly payment data for charts
    context = {
        'client': client,
        'finances': finances,
        'balance_summary': '5,000.00',
        'recent_transactions': [
            {'date': '2025-06-01', 'amount': '100,000.00', 'recipient': 'John Senkubuge',},
            {'date': '2025-05-30', 'amount': '50,000.00', 'recipient': 'Jane Awori'},
            {'date': '2025-05-28', 'amount': '200,000.00', 'recipient': 'Kansime Investiments'},
        ],
        'upcoming_payments': [
            {'date': '2025-08-14', 'amount': '200,000.00', 'recipient': 'Edwin Byabakama'},
        ],
        'payment_methods': ['MTN', 'Airtel'],
        'payments_week': {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'data': [150000, 200000, 100000, 250000, 300000, 180000, 220000],
        },
        'payments_month': {
            'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'data': [7000000, 8500000, 9000000, 7500000],
        },
    }
    return render(request, 'dashboard/overview.html', context)

@login_required
@user_passes_test(is_client)
def transactions(request):
    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    # Mock transaction history reflecting payments made to people with phone numbers
    transaction_history = [
        {'date': '2024-06-01', 'amount': '100000.00', 'recipient': 'John Senkubuge', 'phone': '+256709451069'},
        {'date': '2024-05-30', 'amount': '50000.00', 'recipient': 'Jane Awori', 'phone': '+256785237432'},
        {'date': '2024-05-28', 'amount': '200000.00', 'recipient': 'Kansime Investiments', 'phone': '+256757454546'},
    ]
    context = {
        'client': client,
        'transaction_history': transaction_history,
    }
    return render(request, 'dashboard/transactions.html', context)

@login_required
@user_passes_test(is_client)
def payments(request):
    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})

    if request.method == 'POST':
        if 'single_payment' in request.POST:
            # Handle single payment form submission
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            amount = request.POST.get('amount')
            payment_method = request.POST.get('payment_method')
            transaction_type = request.POST.get('transaction_type')

            if payment_method not in ['MTN', 'Airtel']:
                messages.error(request, 'Invalid payment method selected.')
            elif transaction_type not in ['collection', 'disbursement']:
                messages.error(request, 'Invalid transaction type selected.')
            else:
                # Process the single payment (mock)
                messages.success(request, f'Single payment of {amount} to {name} ({phone}) via {payment_method} as {transaction_type} processed.')

            return redirect('client:payments')

        elif 'multiple_payments' in request.POST:
            # Handle multiple payments file upload
            payment_file = request.FILES.get('payment_file')
            if not payment_file:
                messages.error(request, 'No file uploaded.')
                return redirect('client:payments')

            if not payment_file.name.endswith(('.xls', '.xlsx')):
                messages.error(request, 'Invalid file type. Please upload an Excel file.')
                return redirect('client:payments')

            try:
                wb = openpyxl.load_workbook(payment_file)
                sheet = wb.active
                payments_processed = 0
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    name, phone, amount, payment_method = row
                    if payment_method not in ['MTN', 'Airtel']:
                        continue  # skip invalid payment methods
                    # Process each payment (mock)
                    payments_processed += 1
                messages.success(request, f'{payments_processed} payments processed from the uploaded file.')
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')

            return redirect('client:payments')

    # GET request or fallback
    payment_methods = ['MTN', 'Airtel']
    scheduled_payments = [
        {'date': '2024-06-10', 'amount': '200.00', 'type': 'One-time'},
        {'date': '2024-07-01', 'amount': '100.00', 'type': 'Recurring'},
    ]
    context = {
        'client': client,
        'payment_methods': payment_methods,
        'scheduled_payments': scheduled_payments,
    }
    return render(request, 'dashboard/payments.html', context)

@login_required
@user_passes_test(is_client)
def accounts(request):
    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    # Mock linked accounts with phone numbers formatted
    linked_accounts = [
        {'type': 'MTN', 'details': format_phone_number('256751234567'), 'balance': '3,000,000.00'},
        {'type': 'Airtel', 'details': format_phone_number('256701234567'), 'balance': '1,200,000.00'},
    ]
    context = {
        'client': client,
        'linked_accounts': linked_accounts,
    }
    return render(request, 'dashboard/accounts.html', context)

@login_required
@user_passes_test(is_client)
def settings(request):
    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    # Mock user settings
    user_settings = {
        'profile_info': {'name': client.name, 'email': request.user.email},
        'security': {'password_set': True, '2fa_enabled': False},
        'notifications': {'email_notifications': True, 'sms_notifications': False},
    }
    context = {
        'client': client,
        'user_settings': user_settings,
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
@user_passes_test(is_client)
def help_support(request):
    # Mock help/support content
    faqs = [
        {'question': 'How to make a payment?', 'answer': 'Go to the Payments page and follow the instructions.'},
        {'question': 'How to add a payment method?', 'answer': 'Go to the Payments page and click Add Payment Method.'},
    ]
    contact_info = {
        'email': 'support@example.com',
        'phone': '+1-800-123-4567',
        'chat': 'Available 9am-5pm EST',
    }
    knowledge_base = [
        {'title': 'Managing Your Account', 'link': '#'},
        {'title': 'Payment Scheduling', 'link': '#'},
    ]
    context = {
        'faqs': faqs,
        'contact_info': contact_info,
        'knowledge_base': knowledge_base,
    }
    return render(request, 'dashboard/help_support.html', context)
