from django.contrib import admin

from .models import Ingredient, InventoryAlert, StockMovement


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit", "quantity_in_stock", "alert_threshold", "is_active")
    search_fields = ("name",)
    list_filter = ("unit", "is_active")
    ordering = ("name",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "ingredient", "movement_type", "quantity", "created_by", "created_at")
    search_fields = ("ingredient__name", "created_by__username")
    list_filter = ("movement_type", "created_at")
    ordering = ("-created_at",)


@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = ("id", "ingredient", "message", "is_read", "created_at")
    search_fields = ("ingredient__name", "message")
    list_filter = ("is_read", "created_at")
    ordering = ("-created_at",)
