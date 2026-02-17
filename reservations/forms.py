from django import forms

from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            'customer_name',
            'customer_phone',
            'customer_email',
            'reservation_datetime',
            'party_size',
            'table',
            'status',
            'notes',
        ]
        widgets = {
            'reservation_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
