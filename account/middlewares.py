# middlewares.py

from django.http import HttpResponseForbidden


class AdminSiteAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is trying to access the admin site
        if 'super-a-d-m-i-n/' in request.path:
            # If the user is not authenticated, deny access
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Forbidden")

            # If the user does not have 'is_si_admin' or 'is_superuser', deny access
            if not request.user.is_superuser:
                return HttpResponseForbidden("Forbidden")

        return self.get_response(request)
