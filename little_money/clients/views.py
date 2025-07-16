from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Client, Finances, RecentTransaction, UpcomingPayment, LinkedAccount, UserSetting, FAQ, ContactInfo, KnowledgeBaseEntry,DailyPayment
from django.utils.timezone import now
from core.utils import is_client
import openpyxl
from django.contrib import messages
from django.shortcuts import redirect
from core.utils import format_phone_number

@login_required
@user_passes_test(is_client)
def overview_dashboard(request):
    import datetime
    from django.utils.timezone import localdate
    from django.db.models import Sum

    client, created = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
    finances = Finances.objects.filter(client=client).first()

    # Get current day of week (0=Monday, 6=Sunday)
    today = localdate()
    # Adjust so Sunday=0, Monday=1,... Saturday=6
    current_weekday = (today.weekday() + 1) % 7

    # Prepare payments_week data
    week_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    payments_week_data = []
    for i in range(7):
        # Calculate day_date with Sunday as first day
        day_date = today - datetime.timedelta(days=(current_weekday - i) % 7)
        if i <= current_weekday:
            total = DailyPayment.objects.filter(client=client, date=day_date).aggregate(total=Sum('amount'))['total'] or 0
            payments_week_data.append(total)
        else:
            payments_week_data.append(0)  # Future days show 0

    payments_week = {
        'labels': week_labels,
        'data': payments_week_data,
    }

    # Prepare payments_month data (4 weeks)
    # Determine current week of the month (1-4)
    first_day_of_month = today.replace(day=1)
    current_week_of_month = (today.day - 1) // 7 + 1
    payments_month_data = []
    for week_num in range(1, 5):
        if week_num <= current_week_of_month:
            start_day = first_day_of_month + datetime.timedelta(days=(week_num - 1) * 7)
            end_day = start_day + datetime.timedelta(days=6)
            total = DailyPayment.objects.filter(client=client, date__range=(start_day, end_day)).aggregate(total=Sum('amount'))['total'] or 0
            payments_month_data.append(total)
        else:
            payments_month_data.append(0)  # Future weeks show 0

    payments_month = {
        'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        'data': payments_month_data,
    }

    recent_transactions = RecentTransaction.objects.filter(client=client).order_by('-date')[:5]
    upcoming_payments = UpcomingPayment.objects.filter(client=client).order_by('date')[:5]
    linked_accounts = LinkedAccount.objects.filter(client=client)
    user_settings = None
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
                # Record the payment in DailyPayment and RecentTransaction
                client_obj, _ = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
                DailyPayment.objects.create(
                    client=client_obj,
                    date=now().date(),
                    amount=Decimal(amount),
                )
                RecentTransaction.objects.create(
                    client=client_obj,
                    date=now().date(),
                    amount=Decimal(amount),
                    recipient=name,
                    phone=phone,
                )
                # Update or create Finances balance accordingly
                finances, created = Finances.objects.get_or_create(client=client_obj, defaults={'balance': Decimal('0.00')})
                if transaction_type == 'collection':
                    finances.balance += Decimal(amount)
                else:
                    finances.balance -= Decimal(amount)
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
                    name, phone, amount, payment_method = row
                    if payment_method not in ['MTN', 'Airtel']:
                        continue  # skip invalid payment methods
                    # Record each payment in DailyPayment and RecentTransaction
                    DailyPayment.objects.create(
                        client=client_obj,
                        date=now().date(),
                        amount=Decimal(amount),
                    )
                    RecentTransaction.objects.create(
                        client=client_obj,
                        date=now().date(),
                        amount=Decimal(amount),
                        recipient=name,
                        phone=phone,
                    )
                    # Update or create Finances balance
                    finances, created = Finances.objects.get_or_create(client=client_obj, defaults={'balance': Decimal('0.00')})
                    finances.balance += Decimal(amount)
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
            # Record the fund addition as a RecentTransaction with transaction_type 'collection'
            RecentTransaction.objects.create(
                client=client,
                date=now().date(),
                amount=Decimal(amount),
                recipient=name,
                phone=phone,
            )
            # Update or create Finances balance
            finances, created = Finances.objects.get_or_create(client=client, defaults={'balance': Decimal('0.00')})
            finances.balance += Decimal(amount)
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
