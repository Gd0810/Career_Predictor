from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def candidate_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "candidate":
            raise PermissionDenied("Only candidate accounts can access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper
