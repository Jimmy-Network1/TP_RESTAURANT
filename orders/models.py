from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import CustomerProfile, Address
from menu.models import Dish
from tablesapp.models import Table


class Order(models.Model):
    TYPE_DINE_IN = "dine_in"
    TYPE_TAKEAWAY = "takeaway"
    TYPE_DELIVERY = "delivery"
    TYPE_CHOICES = [
        (TYPE_DINE_IN, "Sur place"),
        (TYPE_TAKEAWAY, "À emporter"),
        (TYPE_DELIVERY, "Livraison"),
    ]

    STATUS_DRAFT = "DRAFT"
    STATUS_PENDING = "EN_ATTENTE"
    STATUS_PREPARING = "PREPARATION"
    STATUS_READY = "PRETE"
    STATUS_SERVED = "SERVIE"
    STATUS_ON_ROUTE = "EN_ROUTE"
    STATUS_DONE = "LIVREE"
    STATUS_PAID = "PAYEE"
    STATUS_CANCELLED = "ANNULEE"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Brouillon"),
        (STATUS_PENDING, "En attente"),
        (STATUS_PREPARING, "En préparation"),
        (STATUS_READY, "Prête"),
        (STATUS_SERVED, "Servie"),
        (STATUS_ON_ROUTE, "En route"),
        (STATUS_DONE, "Livrée"),
        (STATUS_PAID, "Payée"),
        (STATUS_CANCELLED, "Annulée"),
    ]

    order_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_DINE_IN)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    customer_profile = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    note = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    kitchen_issue = models.BooleanField(default=False)
    kitchen_issue_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    assigned_delivery = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries"
    )

    def __str__(self):
        return f"Commande #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    dish = models.ForeignKey(Dish, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dish} x{self.quantity}"


class OrderNotification(models.Model):
    TARGET_SERVER = "server"
    TARGET_DELIVERY = "delivery"
    TARGET_CHOICES = [
        (TARGET_SERVER, "Serveur"),
        (TARGET_DELIVERY, "Livraison"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notifications")
    target = models.CharField(max_length=20, choices=TARGET_CHOICES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_id} -> {self.status}"
