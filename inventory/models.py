from django.conf import settings
from django.db import models
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=150, unique=True)
    contact_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    UNIT_KG = 'kg'
    UNIT_LITER = 'l'
    UNIT_UNIT = 'unit'
    UNIT_BUNCH = 'bunch'

    UNIT_CHOICES = [
        (UNIT_KG, 'kg'),
        (UNIT_LITER, 'L'),
        (UNIT_UNIT, 'unité'),
        (UNIT_BUNCH, 'botte'),
    ]

    name = models.CharField(max_length=150, unique=True)
    category = models.CharField(max_length=120, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default=UNIT_UNIT)
    quantity_in_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='ingredients')
    storage_location = models.CharField(max_length=120, blank=True)
    expiry_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    TYPE_IN = 'in'
    TYPE_OUT = 'out'
    TYPE_TRANSFER = 'transfer'
    TYPE_ADJUSTMENT = 'adjustment'

    TYPE_CHOICES = [
        (TYPE_IN, 'Entrée'),
        (TYPE_OUT, 'Sortie'),
        (TYPE_TRANSFER, 'Transfert'),
        (TYPE_ADJUSTMENT, 'Ajustement'),
    ]

    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.ingredient.name} - {self.get_movement_type_display()}"


class PurchaseOrder(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_RECEIVED = 'received'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Brouillon'),
        (STATUS_SENT, 'Envoyée'),
        (STATUS_RECEIVED, 'Reçue'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    received_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Commande fournisseur #{self.id or 'N/A'}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name='purchase_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.ingredient.name} ({self.quantity})"
