from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def index(request):
    return render(request, 'index.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if user.role == 'admin':
                return redirect('https://admin.mangupay.tech/overview/')
            elif user.role == 'staff':
                return redirect('https://staff.mangupay.tech/overview/')
            elif user.role == 'client':
                return redirect('https://client.mangupay.tech/overview/')
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

