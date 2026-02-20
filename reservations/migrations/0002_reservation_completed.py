from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reservation",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "En attente"),
                    ("CONFIRMED", "Confirmée"),
                    ("CANCELLED", "Annulée"),
                    ("COMPLETED", "Terminée"),
                    ("NO_SHOW", "No-show"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
    ]
