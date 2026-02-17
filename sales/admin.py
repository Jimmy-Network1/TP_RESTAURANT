from django.contrib import admin

from .models import Order, OrderItem, Payment, Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'capacity', 'status')
    list_filter = ('status', 'zone')
    search_fields = ('name', 'zone')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_type', 'status', 'table', 'total_amount', 'created_at')
    list_filter = ('order_type', 'status')
    search_fields = ('id', 'customer_name', 'customer_phone')
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'method', 'amount', 'created_at')
    list_filter = ('method',)
