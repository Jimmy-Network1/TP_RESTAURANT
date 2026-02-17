from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'reservation_datetime', 'party_size', 'table', 'status')
    list_filter = ('status',)
    search_fields = ('customer_name', 'customer_phone', 'customer_email')
