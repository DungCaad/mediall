from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_remove_doctorprofile_clinic_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorprofile",
            name="is_verified",
            field=models.BooleanField(default=False, editable=False, verbose_name="Verified doctor"),
        ),
    ]
