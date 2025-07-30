import datetime
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Client, Finances, RecentTransaction, UpcomingPayment, LinkedAccount, UserSetting, FAQ, ContactInfo, KnowledgeBaseEntry, DailyPayment
from django.utils.timezone import now, localdate
from core.utils import is_client
import openpyxl
from django.contrib import messages
from django.db.models import Sum
from calendar import monthrange
from config.help import process_transaction
from decimal import Decimal, InvalidOperation
from django.contrib.auth import update_session_auth_hash
from .forms import ClientProfileForm, ClientPasswordChangeForm, NotificationPreferencesForm


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
    finances, created = Finances.objects.get_or_create(client=client, defaults={'balance': Decimal('0.00')})
    # Validation for disbursement amount <= balance
    
    if request.method == 'POST':
        if 'single_payment' in request.POST:
            print(request.POST)  
            try:
                name = request.POST.get('name')
                phone = request.POST.get('phone')
                amount = request.POST.get('amount')
                payment_method = request.POST.get('payment_method')

                if payment_method not in ['MTN', 'Airtel']:
                    return JsonResponse({'status': 'error', 'message': 'Invalid payment method selected.'}, status=400)
                
                # Mapping to expected integer values
                map_channel = {'MTN': 1, 'Airtel': 2}

                channel = map_channel[payment_method]

                amount_decimal = Decimal(amount)
                base_amount = int(amount_decimal)

                trader_id = str(phone)
                message = f"Disbursment for {name} ({phone})"

                if amount_decimal > finances.balance:
                    messages.error(request, f'Disbursement amount {amount} exceeds available balance {finances.balance}. Transaction cancelled.')
                    return redirect('client:payments')
                return process_transaction(
                    channel=channel,
                    t_type=2,
                    client_id=client.id,
                    base_amount=base_amount,
                    trader_id=trader_id,
                    message=message,
                    name=name
                )

            except Exception as e:
                message = f"failed due to{str(e)}"
                return render(request, 'dashboard/payments.html')

        elif 'multiple_payments' in request.POST:
            try:
                payment_file = request.FILES.get('payment_file')
                if not payment_file:
                    return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)

                if not payment_file.name.endswith(('.xls', '.xlsx')):
                    return JsonResponse({'status': 'error', 'message': 'Invalid file type. Please upload an Excel file.'}, status=400)

                wb = openpyxl.load_workbook(payment_file)
                sheet = wb.active

                total_requested = Decimal('0.00')
                errors = []
                valid_rows = []

                for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    if len(row) < 4:
                        errors.append({'row': idx, 'message': 'Incomplete row data.'})
                        continue

                    name, phone, amount, payment_method = row[:4]

                    if payment_method not in ['MTN', 'Airtel']:
                        errors.append({'row': idx, 'message': f'Invalid payment method: {payment_method}'})
                        continue

                    try:
                        amount_decimal = Decimal(str(amount))
                        if amount_decimal <= 0:
                            raise ValueError("Amount must be greater than zero.")
                        total_requested += amount_decimal
                        valid_rows.append((name, phone, amount_decimal, payment_method))
                    except (InvalidOperation, ValueError) as e:
                        errors.append({'row': idx, 'message': f'Invalid amount: {amount}. {str(e)}'})

                if total_requested > finances.balance:
                    required_top_up = total_requested - finances.balance
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Insufficient balance. Total disbursement amount is {total_requested}, '
                                f'but your balance is {finances.balance}. You need to top up {required_top_up}.',
                        'total_requested': str(total_requested),
                        'current_balance': str(finances.balance),
                        'required_top_up': str(required_top_up),
                        'errors': errors,
                    }, status=400)

                # Process all valid transactions
                payments_processed = 0
                for name, phone, amount_decimal, payment_method in valid_rows:
                    try:
                        map_channel = {'MTN': 1, 'Airtel': 2}
                        channel = map_channel[payment_method]
                        base_amount = int(amount_decimal)
                        trader_id = client.trader_id if hasattr(client, 'trader_id') else str(client.id)
                        message = f"Disbursement for {name} ({phone})"

                        result = process_transaction(
                            channel=channel,
                            t_type=2,
                            client_id=client.id,
                            base_amount=base_amount,
                            trader_id=trader_id,
                            message=message,
                            name=name
                        )

                        if result.status_code == 200:
                            payments_processed += 1
                        else:
                            errors.append({
                                'row': name,
                                'message': result.json().get('message', 'Unknown error')
                            })

                    except Exception as e:
                        errors.append({'row': name, 'message': str(e)})

                return JsonResponse({
                    'status': 'success',
                    'processed': payments_processed,
                    'total_requested': str(total_requested),
                    'errors': errors
                })

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # For GET request
    scheduled_payments = UpcomingPayment.objects.filter(client=client).order_by('date')
    context = {
        'client': client,
        'payment_methods': ['MTN', 'Airtel'],
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
        if payment_method not in ['MTN', 'Airtel']:
            messages.error(request, 'Invalid payment method selected.')
        else:
            from decimal import Decimal
            amount_decimal = Decimal(amount)
            message = f"Collecttion for {name}"
            result = process_transaction(
                            channel=payment_method,
                            t_type=1,
                            client_id=client.id,
                            base_amount=amount,
                            trader_id=phone,
                            message=message,
                            name=name
                        )
            if result.status_code == 200:
                # Record the fund addition as a RecentTransaction with transaction_type 'collection'
                RecentTransaction.objects.create(
                    client=client,
                    date=now().date(),
                    amount=amount_decimal,
                    recipient=name,
                    phone=phone,
                )
                # Update or create Finances balance
                finances.balance += amount_decimal
                finances.save()
                messages.success(request, f'Funds of {amount} added for {name} ({phone}) via {payment_method}.')

        return redirect('client:accounts')

    context = {
        'client': client,
        'linked_accounts': linked_accounts,
        'finances': finances,
    }
    return render(request, 'dashboard/accounts.html', context)

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import ClientProfileForm, ClientPasswordChangeForm, NotificationPreferencesForm
from django.shortcuts import redirect, render

@login_required
@user_passes_test(is_client)
def settings(request):
    client, _ = Client.objects.get_or_create(user=request.user, defaults={'name': request.user.username})

    user_settings_data = {
        "profile_info": {
            "name": client.name,
            "email": request.user.email,
            "business_type": client.business_type,
            "status": client.status,
        },
        "security": {
            "password_set": request.user.has_usable_password(),
            "2fa_enabled": False,
        },
        "notifications": {},
    }

    try:
        user_settings = client.user_settings
        user_settings_data["notifications"] = user_settings.notifications
    except AttributeError:
        user_settings_data["notifications"] = {
            "email_notifications": False,
            "sms_notifications": False,
        }

    if request.method == 'POST':
        if 'profile_form' in request.POST:
            profile_form = ClientProfileForm(request.POST, request.FILES, instance=request.user)
            business_type = request.POST.get('business_type')  # grab from request

            if profile_form.is_valid():
                profile_form.save()
                client.business_type = business_type
                client.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('clients:settings')
            else:
                messages.error(request, 'Please correct the errors below.')
        elif 'password_form' in request.POST:
            password_form = ClientPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
                return redirect('clients:settings')
            else:
                messages.error(request, 'Please correct the errors below.')
        elif 'notification_form' in request.POST:
            notification_form = NotificationPreferencesForm(request.POST)
            if notification_form.is_valid():
                # Save notification prefs here
                messages.success(request, 'Notification preferences updated successfully.')
                return redirect('clients:settings')
            else:
                messages.error(request, 'Please correct the errors below.')

    profile_form = ClientProfileForm(instance=client)
    password_form = ClientPasswordChangeForm(request.user)
    notification_form = NotificationPreferencesForm(initial=user_settings_data["notifications"])

    return render(request, 'dashboard/settings.html', {
        'client': client,
        'user': request.user,
        'user_settings': user_settings_data,
        'profile_form': profile_form,
        'password_form': password_form,
        'notification_form': notification_form,
    })

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


def force_password_change_view(request):
    user = request.user
    if request.method == 'POST':
        password_form = ClientPasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            user.is_first_login = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('client:overview_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        password_form = ClientPasswordChangeForm(user)

    return render(request, 'dashboard/force_password_change.html', {
        'password_form': password_form,
        'user': user,
    })
