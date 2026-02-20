from django.db import models


class Table(models.Model):
    STATUS_FREE = "free"
    STATUS_OCCUPIED = "occupied"
    STATUS_RESERVED = "reserved"
    STATUS_CLEANING = "cleaning"
    STATUS_CHOICES = [
        (STATUS_FREE, "Libre"),
        (STATUS_OCCUPIED, "Occupée"),
        (STATUS_RESERVED, "Réservée"),
        (STATUS_CLEANING, "À nettoyer"),
    ]

    name = models.CharField(max_length=50, unique=True)
    zone = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_FREE)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
