from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_auditlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_role", models.CharField(choices=[("server", "Serveur"), ("cook", "Cuisinier"), ("cashier", "Caissier"), ("delivery", "Livreur"), ("manager", "Gérant"), ("client", "Client")], max_length=20)),
                ("message", models.CharField(max_length=255)),
                ("url", models.CharField(blank=True, max_length=255)),
                ("level", models.CharField(choices=[("info", "Info"), ("warn", "Alerte"), ("danger", "Critique")], default="info", max_length=10)),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="notifications", to=settings.AUTH_USER_MODEL)),
                ("read_by", models.ManyToManyField(blank=True, related_name="notifications_read", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
