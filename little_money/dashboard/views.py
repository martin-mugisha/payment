from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from core.models import CustomUser
from payment.models import PlatformSettings, Transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum

# Admin Dashboard - Transactions
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    transactions = Transaction.objects.all()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(created_at__date__lte=end_date)

    total_platform_earnings = transactions.filter(status='SUCCESS').aggregate(Sum('platform_fee_amount'))['platform_fee_amount__sum'] or 0.00

    return render(request, 'dashboard/admin.html', {
        'transactions': transactions,
        'total_platform_earnings': total_platform_earnings,
        'start_date': start_date,
        'end_date': end_date
    })

# Platform Fee Settings
@login_required
@user_passes_test(lambda u: u.is_superuser)
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

# Export Transactions CSV
@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_transactions_csv(request):
    transactions = Transaction.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Transaction ID', 'User', 'Base Amount', 'Platform Fee %', 'Platform Fee Amount', 'Total', 'Status', 'Created At'])

    for txn in transactions:
        writer.writerow([
            txn.transaction_id,
            txn.user.username,
            txn.base_amount,
            txn.platform_fee_percent,
            txn.platform_fee_amount,
            txn.total_amount,
            txn.status,
            txn.created_at
        ])

    return response

# Staff Dashboard
@login_required
@user_passes_test(lambda u: u.is_staff_user)
def staff_dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)

    return render(request, 'dashboard/staff.html', {
        'transactions': transactions
    })

# Manage Staff Users (Admin Only)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def staff_users(request):
    staff_users = CustomUser.objects.filter(is_staff_user=True)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            if not CustomUser.objects.filter(username=username).exists():
                new_user = CustomUser.objects.create_user(username=username, password=password)
                new_user.is_staff_user = True
                new_user.save()
                messages.success(request, f"Staff user '{username}' created.")
            else:
                messages.error(request, "Username already exists.")

    return render(request, 'dashboard/staff_user.html', {
        'staff_users': staff_users
    })

# Login View
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif user.is_staff_user:
                return redirect('staff_dashboard')
            else:
                messages.error(request, "Unauthorized user.")
                logout(request)
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'dashboard/login.html')

# Logout View
def user_logout(request):
    logout(request)
    return redirect('login')
