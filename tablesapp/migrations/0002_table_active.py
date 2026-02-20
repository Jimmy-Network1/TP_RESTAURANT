from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tablesapp", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="table",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]
