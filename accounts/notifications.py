from django.urls import reverse

from accounts.models import Notification
from orders.models import Order
from reservations.models import Reservation


def create_notification(target_role, message, user=None, url="", level=Notification.LEVEL_INFO):
    return Notification.objects.create(
        target_role=target_role,
        user=user,
        message=message,
        url=url,
        level=level,
    )


def notify_order_status(order, new_status):
    staff_url = reverse("orders:detail", args=[order.id])
    client_url = reverse("public:order_detail", args=[order.id])
    client_user = order.customer if order.customer_id else None

    if new_status == Order.STATUS_PENDING:
        create_notification(Notification.ROLE_COOK, f"Nouvelle commande #{order.id} en attente", url=staff_url)
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Commande #{order.id} confirmée", user=client_user, url=client_url)
    elif new_status == Order.STATUS_PREPARING:
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Commande #{order.id} en préparation", user=client_user, url=client_url)
    elif new_status == Order.STATUS_READY:
        if order.order_type == Order.TYPE_DELIVERY:
            create_notification(Notification.ROLE_DELIVERY, f"Commande #{order.id} prête à livrer", url=staff_url)
        else:
            create_notification(Notification.ROLE_SERVER, f"Commande #{order.id} prête à servir", url=staff_url)
        if client_user and order.order_type == Order.TYPE_TAKEAWAY:
            create_notification(Notification.ROLE_CLIENT, f"Commande #{order.id} prête à retirer", user=client_user, url=client_url)
    elif new_status == Order.STATUS_SERVED:
        create_notification(Notification.ROLE_CASHIER, f"Commande #{order.id} servie, à encaisser", url=staff_url)
    elif new_status == Order.STATUS_ON_ROUTE:
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Commande #{order.id} en livraison", user=client_user, url=client_url)
    elif new_status == Order.STATUS_DONE:
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Commande #{order.id} livrée", user=client_user, url=client_url)
    elif new_status == Order.STATUS_PAID:
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Paiement confirmé pour la commande #{order.id}", user=client_user, url=client_url)
    elif new_status == Order.STATUS_CANCELLED:
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Commande #{order.id} annulée", user=client_user, url=client_url, level=Notification.LEVEL_WARN)
        create_notification(Notification.ROLE_MANAGER, f"Commande #{order.id} annulée", url=staff_url, level=Notification.LEVEL_WARN)


def notify_reservation_status(reservation, new_status):
    client_user = reservation.customer_profile.user if reservation.customer_profile_id else None
    client_url = reverse("reservations:client_detail", args=[reservation.id])
    staff_url = reverse("reservations:staff_detail", args=[reservation.id])

    if new_status == Reservation.STATUS_PENDING:
        create_notification(Notification.ROLE_MANAGER, f"Nouvelle réservation #{reservation.id} à valider", url=staff_url)
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Réservation #{reservation.id} en attente", user=client_user, url=client_url)
    elif new_status == Reservation.STATUS_CONFIRMED:
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Réservation #{reservation.id} confirmée", user=client_user, url=client_url)
    elif new_status == Reservation.STATUS_CANCELLED:
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Réservation #{reservation.id} annulée", user=client_user, url=client_url, level=Notification.LEVEL_WARN)
    elif new_status == Reservation.STATUS_COMPLETED:
        if client_user:
            create_notification(Notification.ROLE_CLIENT, f"Réservation #{reservation.id} terminée", user=client_user, url=client_url)
