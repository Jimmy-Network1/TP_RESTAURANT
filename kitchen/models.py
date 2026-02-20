from django.db import models
from django.utils import timezone

from orders.models import Order


class KitchenTicket(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PREPARING = "preparing"
    STATUS_READY = "ready"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_PREPARING, "En préparation"),
        (STATUS_READY, "Prêt"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="kitchen_tickets")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(blank=True, null=True)
    ready_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Ticket #{self.id} pour commande {self.order_id}"


class KitchenUpdate(models.Model):
    KIND_ADD = "add"
    KIND_MODIFY = "modify"
    KIND_CHOICES = [
        (KIND_ADD, "Ajout"),
        (KIND_MODIFY, "Modification"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="kitchen_updates")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_MODIFY)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="kitchen_updates"
    )

    def __str__(self):
        return f"{self.get_kind_display()} #{self.id}"
