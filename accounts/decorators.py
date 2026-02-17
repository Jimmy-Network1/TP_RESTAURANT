from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import UserProfile


def role_required(roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            profile = getattr(request.user, 'userprofile', None)
            if not profile:
                profile = UserProfile.objects.create(
                    user=request.user,
                    role=UserProfile.ROLE_ADMIN if request.user.is_staff else UserProfile.ROLE_SERVER,
                )

            if profile.role not in roles:
                return render(request, 'accounts/forbidden.html', status=403)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
