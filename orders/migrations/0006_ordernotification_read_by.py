from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_alter_order_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="ordernotification",
            name="read_by",
            field=models.ManyToManyField(
                blank=True,
                related_name="order_notifications_read",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
