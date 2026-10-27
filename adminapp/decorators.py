from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def superadmin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Only the super admin can access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper
