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


class AuditLog(models.Model):
    action = models.CharField(max_length=80)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=64, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.object_type}#{self.object_id}"


class Notification(models.Model):
    ROLE_SERVER = "server"
    ROLE_COOK = "cook"
    ROLE_CASHIER = "cashier"
    ROLE_DELIVERY = "delivery"
    ROLE_MANAGER = "manager"
    ROLE_CLIENT = "client"
    ROLE_CHOICES = [
        (ROLE_SERVER, "Serveur"),
        (ROLE_COOK, "Cuisinier"),
        (ROLE_CASHIER, "Caissier"),
        (ROLE_DELIVERY, "Livreur"),
        (ROLE_MANAGER, "Gérant"),
        (ROLE_CLIENT, "Client"),
    ]

    LEVEL_INFO = "info"
    LEVEL_WARN = "warn"
    LEVEL_DANGER = "danger"
    LEVEL_CHOICES = [
        (LEVEL_INFO, "Info"),
        (LEVEL_WARN, "Alerte"),
        (LEVEL_DANGER, "Critique"),
    ]

    target_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default=LEVEL_INFO)
    created_at = models.DateTimeField(default=timezone.now)
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="notifications_read",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_target_role_display()} • {self.message}"
