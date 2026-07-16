from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_english_role_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="accountprofile",
            name="photo",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="accountprofile",
            name="clinic_address",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
