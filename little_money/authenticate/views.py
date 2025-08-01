from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def index(request):
    return render(request, 'index.html')

# Login View
from django.http import HttpResponse

def user_login(request):
    # If user is already authenticated (session active), redirect to their dashboard
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admins:admin_dashboard')
        elif request.user.role == 'staff':
            return redirect('staff:summary_dashboard')
        elif request.user.role == 'client':
            return redirect('client:overview_dashboard')
        else:
            messages.error(request, "Unauthorized user.")
            logout(request)
            return redirect('authenticate:login')

    if request.method == 'POST':
        # Check if this is the forgot password form submission by checking if 'password' is missing
        if 'password' not in request.POST:
            username = request.POST.get('username', '')
            messages.success(request, f"Hey {username}, request received but feature is still under development.")
            return redirect('authenticate:login')

        # Otherwise, handle login form submission
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'admin':
                return redirect('admins:admin_dashboard')
            elif user.role == 'staff':
                return redirect('staff:summary_dashboard')
            elif user.role == 'client':
                return redirect('client:overview_dashboard')
            else:
                messages.error(request, "Unauthorized user.")
                logout(request)
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'login.html')


# Logout View
def user_logout(request):
    logout(request)
    return redirect('authenticate:login')

