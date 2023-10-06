from django.contrib.auth import authenticate, login
from django.contrib.auth import logout


def custom_login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, 'Login successful')
                return redirect('pos:dashboard')
            else:
                messages.error(request, 'Your account is not active. Please contact support.')
        else:
            messages.error(request, 'Invalid credentials or Your account is not active. Please contact admin.')

    return render(request, 'account/login.html')


from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect


def signup(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        # Check if a user with the same email already exists
        if get_user_model().objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'account/signup.html')

        # Check if a user with the same username already exists
        if get_user_model().objects.filter(username=username).exists():
            messages.error(request, "An account with this username already exists.")
            return render(request, 'account/signup.html')

        if password1 == password2:
            user = get_user_model().objects.create_user(username=username, email=email, password=password1)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            messages.success(request, f'Account created for {email}!')
            return redirect('account:login')
        else:
            messages.error(request, "Passwords do not match. Please try again.")

    return render(request, 'account/signup.html')


def custom_logout(request):
    logout(request)
    return redirect('account:login')
