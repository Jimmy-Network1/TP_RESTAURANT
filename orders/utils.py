from .models import Order, OrderStatusLog
from accounts.models import AuditLog
from accounts.notifications import notify_order_status


def _group_names(user):
    if not user.is_authenticated:
        return set()
    return {g.strip().lower() for g in user.groups.values_list("name", flat=True)}


def is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    groups = _group_names(user)
    return bool(groups.intersection({"gerant", "manager", "admin"}))


def is_server(user):
    return "serveur" in _group_names(user)


def is_cook(user):
    return "cuisinier" in _group_names(user)


def is_cashier(user):
    return "caissier" in _group_names(user)


def is_delivery(user):
    return "livreur" in _group_names(user)

def is_staff_user(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    groups = _group_names(user)
    return bool(groups.intersection({"gerant", "manager", "admin", "serveur", "cuisinier", "caissier", "livreur"}))


def can_transition(user, order, new_status):
    if new_status == order.status:
        return True

    if order.status == Order.STATUS_PAID or order.status == Order.STATUS_CANCELLED:
        return False

    if new_status == Order.STATUS_CANCELLED:
        return is_manager(user)

    if order.status == Order.STATUS_DRAFT:
        return new_status in [Order.STATUS_PENDING] or (new_status == Order.STATUS_CANCELLED and is_manager(user))

    if order.status == Order.STATUS_PENDING:
        return (new_status == Order.STATUS_PREPARING and (is_cook(user) or is_manager(user)))

    if order.status == Order.STATUS_PREPARING:
        return (new_status == Order.STATUS_READY and (is_cook(user) or is_manager(user)))

    if order.status == Order.STATUS_READY:
        return (new_status == Order.STATUS_SERVED and (is_server(user) or is_manager(user))) or (
            new_status == Order.STATUS_ON_ROUTE and (is_delivery(user) or is_manager(user))
        )

    if order.status == Order.STATUS_SERVED:
        return new_status == Order.STATUS_PAID and (is_cashier(user) or is_manager(user))

    if order.status == Order.STATUS_ON_ROUTE:
        return new_status == Order.STATUS_DONE and (is_delivery(user) or is_manager(user))

    if order.status == Order.STATUS_DONE:
        return new_status == Order.STATUS_PAID and (is_cashier(user) or is_delivery(user) or is_manager(user))

    return False


def can_edit_order(user, order):
    if order.status in [Order.STATUS_PAID, Order.STATUS_CANCELLED]:
        return False
    if is_manager(user):
        return True
    return order.status in [Order.STATUS_DRAFT, Order.STATUS_PENDING]


def log_transition(order, user, old_status, new_status, reason=""):
    if old_status == new_status:
        return
    detail = f"{old_status} -> {new_status}"
    if reason:
        detail = f"{detail} | {reason}"
    OrderStatusLog.objects.create(
        order=order,
        status=new_status,
        actor=user if user.is_authenticated else None,
        reason=detail,
    )
    AuditLog.objects.create(
        action="ORDER_STATUS",
        user=user if user.is_authenticated else None,
        object_type="Order",
        object_id=str(order.id),
        old_value=old_status,
        new_value=new_status,
        reason=reason or "",
    )
    try:
        notify_order_status(order, new_status)
    except Exception:
        # Avoid breaking flow if notification fails
        pass
