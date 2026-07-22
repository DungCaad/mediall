from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_rename_bio_to_introduction"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="doctorprofile",
            name="clinic_address",
        ),
    ]
