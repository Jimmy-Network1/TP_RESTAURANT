from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "reservation_datetime", "party_size", "status", "table")
    search_fields = ("customer_name", "customer_phone")
    list_filter = ("status", "reservation_datetime")
    ordering = ("-reservation_datetime",)
