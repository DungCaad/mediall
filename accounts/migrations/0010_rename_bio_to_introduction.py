from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_doctor_professional_fields"),
    ]

    operations = [
        migrations.RenameField(
            model_name="doctorprofile",
            old_name="bio",
            new_name="introduction",
        ),
        migrations.AlterField(
            model_name="doctorprofile",
            name="introduction",
            field=models.TextField(blank=True, verbose_name="Giới thiệu"),
        ),
    ]
