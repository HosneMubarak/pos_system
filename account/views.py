from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404

from .decorators import staff_user_required
from .forms import *


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


@login_required
def custom_logout(request):
    logout(request)
    return redirect('account:login')


@login_required
@staff_user_required
def user_list_view(request):
    User = get_user_model()
    users = User.objects.all()

    # Sorting
    sort_by = request.GET.get('sort_by', 'date_joined')  # Default sorting by date_joined
    if sort_by not in ['username', 'first_name', 'last_name', 'date_joined']:
        sort_by = '-date_joined'  # Default to date_joined if invalid sort criteria
    users = users.order_by(sort_by)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(Q(username__icontains=search_query) |
                             Q(first_name__icontains=search_query) |
                             Q(last_name__icontains=search_query) |
                             Q(email__icontains=search_query))

    # Pagination
    per_page = 10
    paginator = Paginator(users, per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        'page': page,
        'sort_by': sort_by,
        'search_query': search_query,
    }
    return render(request, 'account/user_list.html', context)


@login_required
@staff_user_required
def user_add_view(request):
    if not request.user.is_admin and not request.user.is_superuser:
        messages.error(request, "You don't have the permission to add users. Only admin can add users.")
        return redirect('account:user-list')  # Redirect back to the user list view

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('password')
            user = form.save(commit=False)
            user.set_password(password)  # Set the password
            user.save()
            messages.success(request, 'User successfully added.')
            return redirect('account:user-list')  # Redirect to the user list view after adding
        else:
            messages.error(request, 'There was an error adding the user.')
    else:
        form = UserForm()

    return render(request, 'account/user_add.html', {'form': form})


@login_required
@staff_user_required
def user_edit_view(request, user_id):
    if not request.user.is_admin and not request.user.is_superuser:
        messages.error(request, "You don't have the permission to edit users. Only admin can edit users.")
        return redirect('account:user-list')  # Redirect back to the user list view

    user = get_object_or_404(get_user_model(), pk=user_id)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, 'User successfully updated.')
            return redirect('account:user-list')  # Redirect to the user list view after editing
        else:
            messages.error(request, 'There was an error updating the user.')
    else:
        form = UserEditForm(instance=user)

    return render(request, 'account/user_edit.html', {'form': form, 'user': user})


@login_required
@staff_user_required
def user_delete_view(request, user_id):
    if not request.user.is_admin and request.user.id == user_id and not request.user.is_superuser:
        messages.error(request, "You don't have the permission to delete users.")
        return redirect('account:user-list')  # Redirect back to the user list view

    user = get_object_or_404(get_user_model(), pk=user_id)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User successfully deleted.')
        return redirect('account:user-list')  # Redirect to the user list view after deletion

    # Since we removed the confirmation page, if the method is not POST, redirect to the list view.
    return redirect('account:user-list')


@login_required()
def permission_denied_view(request):
    # Your view logic here
    return render(request, 'account/permission-denied.html')


def custom_404_view(request, exception=None):
    """Renders a custom 404 page."""
    return render(request, 'account/custom_404.html', status=404)
