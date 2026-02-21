from django.contrib import admin

from .models import KitchenTicket, KitchenUpdate


@admin.register(KitchenTicket)
class KitchenTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "created_at", "started_at", "ready_at")
    search_fields = ("order__id",)
    list_filter = ("status", "created_at")
    ordering = ("-created_at",)


@admin.register(KitchenUpdate)
class KitchenUpdateAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "kind", "created_by", "created_at")
    search_fields = ("order__id", "created_by__username")
    list_filter = ("kind", "created_at")
    ordering = ("-created_at",)
