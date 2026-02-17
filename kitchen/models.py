from django.db import models
from django.utils import timezone


class KitchenStation(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class KitchenTicket(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PREPARING = 'preparing'
    STATUS_READY = 'ready'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_PREPARING, 'En préparation'),
        (STATUS_READY, 'Prêt'),
    ]

    order = models.ForeignKey('sales.Order', on_delete=models.CASCADE, related_name='kitchen_tickets')
    station = models.ForeignKey(KitchenStation, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(blank=True, null=True)
    ready_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Ticket {self.order_id}"


class KitchenTicketItem(models.Model):
    ticket = models.ForeignKey(KitchenTicket, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey('menu.Dish', on_delete=models.PROTECT, related_name='kitchen_ticket_items')
    quantity = models.PositiveIntegerField(default=1)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.dish.name} x{self.quantity}"


class Recipe(models.Model):
    dish = models.OneToOneField('menu.Dish', on_delete=models.CASCADE, related_name='recipe')
    description = models.TextField(blank=True)
    servings = models.PositiveIntegerField(default=1)
    total_time_minutes = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Recette - {self.dish.name}"


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveIntegerField(default=1)
    instruction = models.TextField()
    time_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"{self.recipe.dish.name} - Étape {self.step_number}"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey('inventory.Ingredient', on_delete=models.PROTECT, related_name='recipe_ingredients')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.ingredient.name} ({self.quantity})"
