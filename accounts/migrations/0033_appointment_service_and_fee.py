from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0032_fee_currency_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorappointment",
            name="service_type",
            field=models.CharField(blank=True, choices=[("video", "Video consultation"), ("message", "Message consultation")], default="", max_length=20, verbose_name="Consultation service"),
        ),
        migrations.AddField(
            model_name="doctorappointment",
            name="consultation_fee",
            field=models.DecimalField(blank=True, decimal_places=2, editable=False, max_digits=12, null=True, validators=[MinValueValidator(0)], verbose_name="Consultation fee ($/visit)"),
        ),
    ]
