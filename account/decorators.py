from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def staff_user_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # Check if the user is active but not admin, staff, or superuser
        if user.is_active and not (user.is_admin or user.is_staff or user.is_superuser):
            messages.error(request, "Please contact the admin to get permission.")
            return redirect(reverse('account:permission-denied'))  # Replace with your custom page name
        return view_func(request, *args, **kwargs)

    return _wrapped_view
