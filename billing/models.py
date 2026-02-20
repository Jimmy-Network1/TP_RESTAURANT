from django.db import models
from django.conf import settings
from django.utils import timezone

from orders.models import Order


class CashSession(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Ouverte"),
        (STATUS_CLOSED, "Fermée"),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    opening_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="cash_sessions_opened")
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="cash_sessions_closed")

    def __str__(self):
        return f"Caisse {self.get_status_display()} - {self.opened_at:%d/%m %H:%M}"


class Payment(models.Model):
    METHOD_CASH = "cash"
    METHOD_CARD = "card"
    METHOD_MOMO = "momo"
    METHOD_CHOICES = [
        (METHOD_CASH, "Espèces"),
        (METHOD_CARD, "Carte"),
        (METHOD_MOMO, "Mobile Money"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    session = models.ForeignKey(CashSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments_created"
    )
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default=METHOD_CASH)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_method_display()} - {self.amount}"
