from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0031_doctor_consultation_fees"),
    ]

    operations = [
        migrations.AlterField(
            model_name="doctorprofile",
            name="video_consultation_fee",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, validators=[MinValueValidator(0)], verbose_name="Video consultation fee ($/visit)"),
        ),
        migrations.AlterField(
            model_name="doctorprofile",
            name="message_consultation_fee",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, validators=[MinValueValidator(0)], verbose_name="Message consultation fee ($/visit)"),
        ),
    ]
