from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_split_patient_and_doctor_profiles"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="doctorprofile",
            name="photo",
        ),
    ]
