from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("kitchen", "0001_initial"),
        ("orders", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="KitchenUpdate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("add", "Ajout"), ("modify", "Modification")], default="modify", max_length=20)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="kitchen_updates", to="auth.user")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="kitchen_updates", to="orders.order")),
            ],
        ),
    ]
