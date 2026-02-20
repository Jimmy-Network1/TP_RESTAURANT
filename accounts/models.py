from django.conf import settings
from django.db import models
from django.utils import timezone


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField(max_length=30, blank=True)
    preferences = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Address(models.Model):
    profile = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=150, default="Adresse")
    city = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    details = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-is_default", "label"]

    def __str__(self):
        return f"{self.label} ({self.profile})"
