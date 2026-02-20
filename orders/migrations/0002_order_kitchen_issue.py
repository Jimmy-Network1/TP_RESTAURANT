from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="kitchen_issue",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="order",
            name="kitchen_issue_note",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
