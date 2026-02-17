from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_CHEF = 'chef'
    ROLE_SERVER = 'server'
    ROLE_CASHIER = 'cashier'
    ROLE_DELIVERY = 'delivery'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrateur'),
        (ROLE_CHEF, 'Chef de cuisine'),
        (ROLE_SERVER, 'Serveur'),
        (ROLE_CASHIER, 'Caissier'),
        (ROLE_DELIVERY, 'Livreur'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_SERVER)
    phone = models.CharField(max_length=30, blank=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class ActivityLog(models.Model):
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Création'),
        (ACTION_UPDATE, 'Modification'),
        (ACTION_DELETE, 'Suppression'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_action_display()} - {self.model_name} - {self.created_at:%Y-%m-%d %H:%M}"
