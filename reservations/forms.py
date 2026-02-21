from django import forms
from django.utils import timezone

from tablesapp.models import Table
from .models import Reservation
from .utils import is_in_opening_hours, is_valid_slot, conflict_window, active_reservations_qs


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
        if dt and not is_valid_slot(dt):
            raise forms.ValidationError("Créneau invalide. Merci de choisir une tranche de 30 minutes.")
        if dt and not is_in_opening_hours(dt):
            raise forms.ValidationError("Créneau hors horaires d'ouverture.")
        return dt

    def clean(self):
        cleaned = super().clean()
        dt = cleaned.get("reservation_datetime")
        zone = cleaned.get("zone")
        party_size = cleaned.get("party_size")
        if not dt or not party_size:
            return cleaned

        window_start, window_end = conflict_window(dt)

        tables_qs = Table.objects.filter(active=True, capacity__gte=party_size)
        if zone:
            tables_qs = tables_qs.filter(zone=zone)

        available_tables = tables_qs.count()
        existing = active_reservations_qs().filter(reservation_datetime__range=(window_start, window_end))
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
        if reservation.status in [Reservation.STATUS_CANCELLED, Reservation.STATUS_COMPLETED, Reservation.STATUS_NO_SHOW]:
            raise forms.ValidationError("Réservation clôturée : modification interdite.")
        new_status = cleaned.get("status") or reservation.status
        if reservation.status == Reservation.STATUS_CONFIRMED and new_status == Reservation.STATUS_PENDING:
            raise forms.ValidationError("Impossible de revenir à 'En attente' après confirmation.")
        if table:
            if not table.active:
                self.add_error("table", "Cette table est inactive.")
            if table.status != Table.STATUS_FREE:
                self.add_error("table", "Cette table n'est pas libre.")
            if reservation.party_size and table.capacity < reservation.party_size:
                self.add_error("table", "Capacité insuffisante pour cette table.")
            window_start, window_end = conflict_window(reservation.reservation_datetime)
            conflicts = active_reservations_qs().filter(
                table=table,
                reservation_datetime__range=(window_start, window_end),
            ).exclude(id=reservation.id)
            if conflicts.exists():
                self.add_error("table", "Cette table est déjà réservée sur ce créneau.")
        return cleaned
