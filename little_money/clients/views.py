from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Client, Finances, RecentTransaction, UpcomingPayment, LinkedAccount, UserSetting, FAQ, ContactInfo, KnowledgeBaseEntry,DailyPayment
from django.utils.timezone import now
from core.utils import is_client
import openpyxl
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.timezone import localdate
import datetime
from collections import defaultdict
from django.db.models import Sum
from calendar import monthrange


def is_all_zero(data):
    """Check if all values in the data list are zero."""
    return all(float(x) == 0 for x in data)

@login_required
@user_passes_test(is_client)
def overview_dashboard(request):
    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    finances = Finances.objects.filter(client=client).first()

    today = localdate()
    current_weekday = (today.weekday() + 1) % 7  # Sunday = 0

    # ------------------ WEEKLY PAYMENTS -------------------
    week_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    week_start = today - datetime.timedelta(days=current_weekday)
    payments_week_data = []

    for i in range(7):
        day_date = week_start + datetime.timedelta(days=i)
        if day_date <= today:
            total = DailyPayment.objects.filter(client=client, date=day_date)\
                .aggregate(total=Sum('amount'))['total'] or 0
            payments_week_data.append(float(total))
        else:
            payments_week_data.append(0.0)

    payments_week = {
        'labels': week_labels,
        'data': payments_week_data if not is_all_zero(payments_week_data) else [],
    }

    # ------------------ MONTHLY PAYMENTS -------------------
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=monthrange(today.year, today.month)[1])

    # Find the first Sunday on or before the 1st of the month
    start_of_calendar = first_day_of_month - datetime.timedelta(days=(first_day_of_month.weekday() + 1) % 7)

    # Create a map of daily totals in the month
    all_payments = DailyPayment.objects.filter(
        client=client,
        date__range=(start_of_calendar, last_day_of_month)
    ).values('date').annotate(total=Sum('amount'))

    day_totals_map = {entry['date']: float(entry['total']) for entry in all_payments}

    # Iterate Sunday to Saturday in week blocks
    payments_month_data = []
    labels = []
    current = start_of_calendar
    week_index = 1

    while current <= today:
        week_total = 0.0
        for i in range(7):
            day = current + datetime.timedelta(days=i)
            if day > today:
                continue  # future days are 0
            week_total += day_totals_map.get(day, 0.0)
        payments_month_data.append(week_total)
        labels.append(f"Week {week_index}")
        week_index += 1
        current += datetime.timedelta(days=7)

    payments_month = {
        'labels': labels,
        'data': payments_month_data if not is_all_zero(payments_month_data) else [],
    }

    # ------------------ OTHER CONTEXT -------------------
    recent_transactions = RecentTransaction.objects.filter(client=client).order_by('-date')[:5]
    upcoming_payments = UpcomingPayment.objects.filter(client=client).order_by('date')[:5]
    linked_accounts = LinkedAccount.objects.filter(client=client)

    try:
        user_settings = client.user_settings
    except UserSetting.DoesNotExist:
        user_settings = None

    context = {
        'client': client,
        'finances': finances,
        'balance_summary': finances.balance if finances else '0.00',
        'recent_transactions': recent_transactions,
        'upcoming_payments': upcoming_payments,
        'payment_methods': ['MTN', 'Airtel'],
        'payments_week': payments_week,
        'payments_month': payments_month,
        'linked_accounts': linked_accounts,
        'user_settings': user_settings,
    }
    return render(request, 'dashboard/overview.html', context)

@login_required
@user_passes_test(is_client)
def transactions(request):
    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    transaction_history = RecentTransaction.objects.filter(client=client).order_by('-date')
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
            from decimal import Decimal
            from django.utils.timezone import now

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
                from decimal import Decimal
                client_obj, _ = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
                finances, created = Finances.objects.get_or_create(client=client_obj, defaults={'balance': Decimal('0.00')})
                amount_decimal = Decimal(amount)

                # Validation for disbursement amount <= balance
                if transaction_type == 'disbursement' and amount_decimal > finances.balance:
                    messages.error(request, f'Disbursement amount {amount} exceeds available balance {finances.balance}. Transaction cancelled.')
                    return redirect('client:payments')

                # Record the payment in DailyPayment and RecentTransaction
                DailyPayment.objects.create(
                    client=client_obj,
                    date=now().date(),
                    amount=amount_decimal if transaction_type == 'collection' else -amount_decimal,
                )
                RecentTransaction.objects.create(
                    client=client_obj,
                    date=now().date(),
                    amount=amount_decimal,
                    recipient=name,
                    phone=phone,
                )
                # Update or create Finances balance accordingly
                if transaction_type == 'collection':
                    finances.balance += amount_decimal
                else:
                    finances.balance -= amount_decimal

                # Ensure balance never goes below 0
                if finances.balance < 0:
                    messages.error(request, 'Balance cannot go below zero. Transaction cancelled.')
                    return redirect('client:payments')

                finances.save()

                messages.success(request, f'Single payment of {amount} to {name} ({phone}) via {payment_method} as {transaction_type} processed.')

            return redirect('client:payments')

        elif 'multiple_payments' in request.POST:
            from decimal import Decimal
            from django.utils.timezone import now

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
                client_obj, _ = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    # Expecting row to have name, phone, amount, payment_method, optionally transaction_type
                    if len(row) == 4:
                        name, phone, amount, payment_method = row
                        transaction_type = 'collection'  # default if not provided
                    elif len(row) >= 5:
                        name, phone, amount, payment_method, transaction_type = row
                        if transaction_type not in ['collection', 'disbursement']:
                            transaction_type = 'collection'  # fallback default
                    else:
                        continue  # skip rows that don't have enough columns

                    if payment_method not in ['MTN', 'Airtel']:
                        continue  # skip invalid payment methods

                    from decimal import Decimal
                    amount_decimal = Decimal(amount)
                    finances, created = Finances.objects.get_or_create(client=client_obj, defaults={'balance': Decimal('0.00')})

                    # Validation for disbursement amount <= balance
                    if transaction_type == 'disbursement' and amount_decimal > finances.balance:
                        continue  # skip this payment

                    # Record each payment in DailyPayment and RecentTransaction
                    DailyPayment.objects.create(
                        client=client_obj,
                        date=now().date(),
                        amount=amount_decimal if transaction_type == 'collection' else -amount_decimal,
                    )
                    RecentTransaction.objects.create(
                        client=client_obj,
                        date=now().date(),
                        amount=amount_decimal,
                        recipient=name,
                        phone=phone,
                    )
                    # Update or create Finances balance
                    if transaction_type == 'collection':
                        finances.balance += amount_decimal
                    else:
                        finances.balance -= amount_decimal

                    # Ensure balance never goes below 0
                    if finances.balance < 0:
                        # Rollback this payment by skipping save and continue
                        continue

                    finances.save()

                    payments_processed += 1
                messages.success(request, f'{payments_processed} payments processed from the uploaded file.')
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')

            return redirect('client:payments')

    scheduled_payments = UpcomingPayment.objects.filter(client=client).order_by('date')
    payment_methods = ['MTN', 'Airtel']
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
    linked_accounts = LinkedAccount.objects.filter(client=client)
    finances = Finances.objects.filter(client=client).first()

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        transaction_type = request.POST.get('transaction_type', 'collection')

        if payment_method not in ['MTN', 'Airtel']:
            messages.error(request, 'Invalid payment method selected.')
        elif transaction_type not in ['collection', 'disbursement']:
            messages.error(request, 'Invalid transaction type selected.')
        else:
            from decimal import Decimal
            amount_decimal = Decimal(amount)
            finances, created = Finances.objects.get_or_create(client=client, defaults={'balance': Decimal('0.00')})

            # Validation for disbursement amount <= balance
            if transaction_type == 'disbursement' and amount_decimal > finances.balance:
                messages.error(request, f'Disbursement amount {amount} exceeds available balance {finances.balance}. Transaction cancelled.')
                return redirect('client:accounts')

            # Record the fund addition as a RecentTransaction with transaction_type 'collection'
            RecentTransaction.objects.create(
                client=client,
                date=now().date(),
                amount=amount_decimal,
                recipient=name,
                phone=phone,
            )
            # Update or create Finances balance
            if transaction_type == 'collection':
                finances.balance += amount_decimal
            else:
                finances.balance -= amount_decimal

            # Ensure balance never goes below 0
            if finances.balance < 0:
                messages.error(request, 'Balance cannot go below zero. Transaction cancelled.')
                return redirect('client:accounts')

            finances.save()

            messages.success(request, f'Funds of {amount} added for {name} ({phone}) via {payment_method}.')

        return redirect('client:accounts')

    context = {
        'client': client,
        'linked_accounts': linked_accounts,
        'finances': finances,
    }
    return render(request, 'dashboard/accounts.html', context)

@login_required
@user_passes_test(is_client)
def settings(request):
    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    user_settings = None
    try:
        user_settings = client.user_settings
    except UserSetting.DoesNotExist:
        user_settings = None
    context = {
        'client': client,
        'user_settings': user_settings,
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
@user_passes_test(is_client)
def help_support(request):
    faqs = FAQ.objects.all()
    contact_info = ContactInfo.objects.first()
    knowledge_base = KnowledgeBaseEntry.objects.all()
    context = {
        'faqs': faqs,
        'contact_info': contact_info,
        'knowledge_base': knowledge_base,
    }
    return render(request, 'dashboard/help_support.html', context)
