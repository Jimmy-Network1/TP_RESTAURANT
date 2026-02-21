from django.contrib import admin

from .models import CashSession, Payment


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "opening_amount", "closing_amount", "opened_by", "opened_at", "closed_at")
    search_fields = ("opened_by__username", "closed_by__username")
    list_filter = ("status", "opened_at")
    ordering = ("-opened_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "method", "amount", "created_by", "created_at")
    search_fields = ("order__id", "created_by__username")
    list_filter = ("method", "created_at")
    ordering = ("-created_at",)
