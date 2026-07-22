from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_active_appointment_slot_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorprofile",
            name="recommended_doctors",
            field=models.ManyToManyField(blank=True, related_name="recommended_by_doctors", symmetrical=False, to="accounts.doctorprofile"),
        ),
    ]
