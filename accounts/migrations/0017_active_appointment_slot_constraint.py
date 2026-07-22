from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_doctorreview"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="doctorappointment",
            name="unique_doctor_appointment_time_slot",
        ),
        migrations.AddConstraint(
            model_name="doctorappointment",
            constraint=models.UniqueConstraint(
                condition=~models.Q(status="rejected"),
                fields=("doctor", "appointment_date", "time_slot"),
                name="unique_doctor_appointment_time_slot",
            ),
        ),
    ]
