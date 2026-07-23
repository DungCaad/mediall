from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0036_patientprofile_is_member"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorappointment",
            name="payment_submitted_at",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="Payment submitted at"),
        ),
    ]
