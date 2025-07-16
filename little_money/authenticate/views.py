from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def index(request):
    return render(request, 'index.html')

# Login View
def user_login(request):
    if request.method == 'POST':
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

