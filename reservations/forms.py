from django import forms
from django.utils import timezone

from tablesapp.models import Table
from .models import Reservation


class ClientReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["reservation_datetime", "party_size", "zone", "note"]
        widgets = {
            "reservation_datetime": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "party_size": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "zone": forms.Select(choices=[("", "Peu importe"), ("VIP", "VIP"), ("Terrasse", "Terrasse"), ("Interieur", "Interieur")], attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3, "maxlength": "200"}),
        }

    def clean_reservation_datetime(self):
        dt = self.cleaned_data.get("reservation_datetime")
        if dt and dt < timezone.now():
            raise forms.ValidationError("Impossible de reserver dans le passe.")
        return dt

    def clean(self):
        cleaned = super().clean()
        dt = cleaned.get("reservation_datetime")
        zone = cleaned.get("zone")
        party_size = cleaned.get("party_size")
        if not dt or not party_size:
            return cleaned

        window_start = dt - timezone.timedelta(hours=2)
        window_end = dt + timezone.timedelta(hours=2)

        tables_qs = Table.objects.filter(active=True, capacity__gte=party_size)
        if zone:
            tables_qs = tables_qs.filter(zone=zone)

        available_tables = tables_qs.count()
        existing = Reservation.objects.filter(
            status__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED],
            reservation_datetime__range=(window_start, window_end),
        )
        if zone:
            existing = existing.filter(zone=zone)

        if available_tables and existing.count() >= available_tables:
            raise forms.ValidationError("Aucune table disponible sur ce créneau.")
        if available_tables == 0:
            raise forms.ValidationError("Aucune table disponible pour ce nombre de personnes.")
        return cleaned


class StaffReservationUpdateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["status", "table"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "table": forms.Select(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        table = cleaned.get("table")
        reservation = self.instance
        if table:
            if not table.active:
                self.add_error("table", "Cette table est inactive.")
            if table.status == "occupied":
                self.add_error("table", "Cette table est déjà occupée.")
            if reservation.party_size and table.capacity < reservation.party_size:
                self.add_error("table", "Capacité insuffisante pour cette table.")
        return cleaned
