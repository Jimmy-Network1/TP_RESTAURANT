from django.contrib import admin

from .models import Order, OrderItem, OrderNotification, OrderStatusLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "order_type", "status", "total_amount", "table", "customer", "assigned_delivery", "created_at")
    search_fields = ("id", "customer__username", "table__name")
    list_filter = ("status", "order_type", "created_at")
    inlines = [OrderItemInline]
    ordering = ("-created_at",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "dish", "quantity", "unit_price", "line_total")
    search_fields = ("order__id", "dish__name")
    list_filter = ("dish",)


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "actor", "created_at")
    search_fields = ("order__id", "actor__username", "status")
    list_filter = ("status", "created_at")
    readonly_fields = ("order", "status", "reason", "actor", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False


@admin.register(OrderNotification)
class OrderNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "target", "message", "created_at")
    search_fields = ("order__id", "message")
    list_filter = ("target", "created_at")
    readonly_fields = ("created_at",)
