from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_add_avatar_remove_emergency_contact"),
    ]

    operations = [
        migrations.AlterField(
            model_name="doctorprofile",
            name="specialties",
            field=models.CharField(blank=True, max_length=255, verbose_name="Chuyên khoa"),
        ),
        migrations.AddField(
            model_name="doctorprofile",
            name="position",
            field=models.CharField(blank=True, max_length=150, verbose_name="Chức vụ"),
        ),
        migrations.AddField(
            model_name="doctorprofile",
            name="workplace",
            field=models.CharField(blank=True, max_length=255, verbose_name="Nơi công tác"),
        ),
    ]
