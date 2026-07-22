from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0020_doctor_work_schedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorprofile",
            name="weekend_off",
            field=models.BooleanField(default=False, verbose_name="Nghỉ Thứ 7 và Chủ nhật"),
        ),
    ]
