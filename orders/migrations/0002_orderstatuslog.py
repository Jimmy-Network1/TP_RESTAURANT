from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderStatusLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[
                    ("DRAFT", "Brouillon"),
                    ("EN_ATTENTE", "En attente"),
                    ("PREPARATION", "En préparation"),
                    ("PRETE", "Prête"),
                    ("SERVIE", "Servie"),
                    ("EN_ROUTE", "En route"),
                    ("LIVREE", "Livrée"),
                    ("PAYEE", "Payée"),
                    ("ANNULEE", "Annulée"),
                ], max_length=20)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_logs", to="orders.order")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
