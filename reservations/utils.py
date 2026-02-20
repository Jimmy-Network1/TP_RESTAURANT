from datetime import time, datetime

from django.utils import timezone

from .models import Reservation
from tablesapp.models import Table

OPEN_TIME = time(10, 0)
CLOSE_TIME = time(23, 0)
SLOT_MINUTES = 30
RESERVATION_BLOCK_HOURS = 2


def is_in_opening_hours(dt):
    if not dt:
        return False
    t = dt.time()
    close_dt = datetime.combine(dt.date(), CLOSE_TIME)
    last_start = (close_dt - timezone.timedelta(minutes=SLOT_MINUTES)).time()
    return OPEN_TIME <= t <= last_start


def is_valid_slot(dt):
    if not dt:
        return False
    return dt.minute % SLOT_MINUTES == 0 and dt.second == 0


def conflict_window(dt):
    return (dt - timezone.timedelta(hours=RESERVATION_BLOCK_HOURS), dt + timezone.timedelta(hours=RESERVATION_BLOCK_HOURS))


def active_reservations_qs():
    return Reservation.objects.filter(status__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED])


def available_slots(date_value, party_size, zone=None):
    tz = timezone.get_current_timezone()
    start = datetime.combine(date_value, OPEN_TIME)
    end = datetime.combine(date_value, CLOSE_TIME)
    slots = []
    now = timezone.localtime()

    tables_qs = Table.objects.filter(active=True, capacity__gte=party_size)
    if zone:
        tables_qs = tables_qs.filter(zone=zone)
    available_tables = tables_qs.count()

    if available_tables == 0:
        return slots

    current = start
    while current <= end - timezone.timedelta(minutes=SLOT_MINUTES):
        dt = timezone.make_aware(current, tz)
        if dt >= now and is_valid_slot(dt) and is_in_opening_hours(dt):
            window_start, window_end = conflict_window(dt)
            existing = active_reservations_qs().filter(reservation_datetime__range=(window_start, window_end))
            if zone:
                existing = existing.filter(zone=zone)
            slots.append({
                "time": dt.strftime("%H:%M"),
                "available": max(available_tables - existing.count(), 0),
            })
        current += timezone.timedelta(minutes=SLOT_MINUTES)
    return slots
