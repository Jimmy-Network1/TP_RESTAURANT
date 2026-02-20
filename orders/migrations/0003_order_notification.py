from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_order_kitchen_issue"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target", models.CharField(choices=[("server", "Serveur"), ("delivery", "Livraison")], max_length=20)),
                ("message", models.CharField(max_length=255)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="orders.order")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
