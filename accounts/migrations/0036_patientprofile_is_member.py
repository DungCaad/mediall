from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0035_appointment_payment_deadline"),
    ]

    operations = [
        migrations.AddField(
            model_name="patientprofile",
            name="is_member",
            field=models.BooleanField(default=False, editable=False, verbose_name="Member"),
        ),
    ]
