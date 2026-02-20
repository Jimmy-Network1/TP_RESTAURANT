from django.db import models
from django.utils import timezone

from orders.models import Order


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
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default=METHOD_CASH)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_method_display()} - {self.amount}"
