from django.conf import settings
from django.db import models
from django.utils import timezone


class Table(models.Model):
    STATUS_FREE = 'free'
    STATUS_OCCUPIED = 'occupied'
    STATUS_RESERVED = 'reserved'
    STATUS_CLEANING = 'cleaning'

    STATUS_CHOICES = [
        (STATUS_FREE, 'Libre'),
        (STATUS_OCCUPIED, 'Occupée'),
        (STATUS_RESERVED, 'Réservée'),
        (STATUS_CLEANING, 'À nettoyer'),
    ]

    name = models.CharField(max_length=50, unique=True)
    zone = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_FREE)

    def __str__(self):
        return self.name


class Order(models.Model):
    TYPE_DINE_IN = 'dine_in'
    TYPE_TAKEAWAY = 'takeaway'
    TYPE_DELIVERY = 'delivery'

    TYPE_CHOICES = [
        (TYPE_DINE_IN, 'Sur place'),
        (TYPE_TAKEAWAY, 'À emporter'),
        (TYPE_DELIVERY, 'Livraison'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_PREPARING = 'preparing'
    STATUS_READY = 'ready'
    STATUS_SERVED = 'served'
    STATUS_CLOSED = 'closed'
    STATUS_CANCELED = 'canceled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Brouillon'),
        (STATUS_SENT, 'Envoyée'),
        (STATUS_PREPARING, 'En préparation'),
        (STATUS_READY, 'Prête'),
        (STATUS_SERVED, 'Servie'),
        (STATUS_CLOSED, 'Clôturée'),
        (STATUS_CANCELED, 'Annulée'),
    ]

    order_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_DINE_IN)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=150, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    delivery_address = models.TextField(blank=True)
    assigned_delivery = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries',
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tip_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_created',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commande #{self.id or 'N/A'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey('menu.Dish', on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.dish.name} x{self.quantity}"


class Payment(models.Model):
    METHOD_CASH = 'cash'
    METHOD_CARD = 'card'
    METHOD_MOMO = 'momo'
    METHOD_CHEQUE = 'cheque'

    METHOD_CHOICES = [
        (METHOD_CASH, 'Espèces'),
        (METHOD_CARD, 'Carte'),
        (METHOD_MOMO, 'Mobile Money'),
        (METHOD_CHEQUE, 'Chèque'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_method_display()} - {self.amount}"
