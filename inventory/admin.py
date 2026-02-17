from django.contrib import admin

from .models import Ingredient, PurchaseOrder, PurchaseOrderItem, StockMovement, Supplier


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'quantity_in_stock', 'alert_threshold', 'supplier', 'is_active')
    list_filter = ('category', 'unit', 'supplier', 'is_active')
    search_fields = ('name', 'category')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_name', 'phone', 'email')
    search_fields = ('name', 'contact_name', 'phone', 'email')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'movement_type', 'quantity', 'created_at', 'created_by')
    list_filter = ('movement_type',)
    search_fields = ('ingredient__name', 'note')


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'status', 'total_amount', 'created_at', 'received_at')
    list_filter = ('status', 'supplier')
    search_fields = ('id', 'supplier__name')
    inlines = [PurchaseOrderItemInline]
