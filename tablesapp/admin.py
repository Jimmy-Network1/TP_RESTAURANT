from django.contrib import admin

from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "zone", "capacity", "status", "active")
    search_fields = ("name", "zone")
    list_filter = ("status", "active", "zone")
    ordering = ("name",)
