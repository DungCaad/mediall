from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_remove_doctorprofile_photo"),
    ]

    operations = [
        migrations.AddField(
            model_name="patientprofile",
            name="avatar",
            field=models.ImageField(blank=True, upload_to="profiles/avatars/", verbose_name="Avatar"),
        ),
        migrations.AddField(
            model_name="doctorprofile",
            name="avatar",
            field=models.ImageField(blank=True, upload_to="profiles/avatars/", verbose_name="Avatar"),
        ),
        migrations.RemoveField(
            model_name="patientprofile",
            name="emergency_contact",
        ),
    ]
