from django.contrib import admin

from .models import Address, AuditLog, CustomerProfile, Notification


admin.site.site_header = "Saveur 237 — Administration"
admin.site.site_title = "Saveur 237 Admin"
admin.site.index_title = "Gestion du restaurant"


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")
    list_filter = ("created_at",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "label", "city", "district", "is_default")
    search_fields = ("profile__user__username", "label", "city", "district")
    list_filter = ("is_default", "city")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "object_type", "object_id", "user", "created_at")
    search_fields = ("action", "object_type", "object_id", "user__username")
    list_filter = ("action", "object_type", "created_at")
    readonly_fields = (
        "action",
        "user",
        "object_type",
        "object_id",
        "old_value",
        "new_value",
        "reason",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "target_role", "user", "level", "message", "created_at")
    search_fields = ("message", "user__username")
    list_filter = ("target_role", "level", "created_at")
    readonly_fields = ("created_at",)
