from django.urls import reverse

from accounts.models import Notification
from .utils import is_manager, is_server, is_delivery, is_cashier, is_cook, is_staff_user


def notification_context(request):
    user = request.user
    if not user.is_authenticated:
        return {
            "notification_count": 0,
            "notification_url": reverse("accounts:login"),
        }

    qs = Notification.objects.exclude(read_by=user)
    if is_delivery(user):
        qs = qs.filter(target_role=Notification.ROLE_DELIVERY)
    elif is_server(user):
        qs = qs.filter(target_role=Notification.ROLE_SERVER)
    elif is_cashier(user):
        qs = qs.filter(target_role=Notification.ROLE_CASHIER)
    elif is_cook(user):
        qs = qs.filter(target_role=Notification.ROLE_COOK)
    elif is_manager(user):
        qs = qs.filter(target_role=Notification.ROLE_MANAGER)
    else:
        qs = qs.filter(target_role=Notification.ROLE_CLIENT, user=user)

    url = reverse("orders:notifications")

    return {
        "notification_count": qs.count(),
        "notification_url": url,
    }
