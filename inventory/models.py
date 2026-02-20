from django.db import models
from django.utils import timezone


class Ingredient(models.Model):
    UNIT_KG = "kg"
    UNIT_L = "l"
    UNIT_UNIT = "unit"
    UNIT_CHOICES = [
        (UNIT_KG, "kg"),
        (UNIT_L, "L"),
        (UNIT_UNIT, "unité"),
    ]

    name = models.CharField(max_length=150, unique=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default=UNIT_UNIT)
    quantity_in_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    TYPE_IN = "in"
    TYPE_OUT = "out"
    TYPE_ADJUST = "adjust"
    TYPE_CHOICES = [
        (TYPE_IN, "Entrée"),
        (TYPE_OUT, "Sortie"),
        (TYPE_ADJUST, "Ajustement"),
    ]

    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} {self.ingredient}"


class InventoryAlert(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="alerts")
    message = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_alerts"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
