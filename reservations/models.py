from django.conf import settings
from django.db import models
from django.utils import timezone


class Reservation(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELED = 'canceled'
    STATUS_NO_SHOW = 'no_show'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_CONFIRMED, 'Confirmée'),
        (STATUS_CANCELED, 'Annulée'),
        (STATUS_NO_SHOW, 'No-show'),
        (STATUS_COMPLETED, 'Terminée'),
    ]

    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)
    reservation_datetime = models.DateTimeField()
    party_size = models.PositiveIntegerField(default=2)
    table = models.ForeignKey('sales.Table', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations_created',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Réservation {self.customer_name} ({self.reservation_datetime:%Y-%m-%d %H:%M})"
