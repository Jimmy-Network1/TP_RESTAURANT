from django.contrib.auth import logout
from django.shortcuts import redirect


class RoleGuardMiddleware:
    """
    Block any staff user that doesn't belong to a valid role group.
    UI is not a security: enforce at middleware level.
    """

    VALID_GROUPS = {"gerant", "manager", "admin", "serveur", "cuisinier", "caissier", "livreur"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            if user.is_superuser:
                return self.get_response(request)
            if user.is_staff:
                groups = {g.name.strip().lower() for g in user.groups.all()}
                if not groups.intersection(self.VALID_GROUPS):
                    logout(request)
                    return redirect("accounts:login")
        return self.get_response(request)
