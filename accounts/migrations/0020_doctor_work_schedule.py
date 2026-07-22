from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0019_profile_country"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorprofile",
            name="work_schedule_type",
            field=models.CharField(choices=[("office", "Giờ hành chính"), ("night", "Ca đêm"), ("custom", "Tùy chỉnh")], default="office", max_length=20),
        ),
        migrations.AddField(
            model_name="doctorprofile",
            name="custom_work_start",
            field=models.TimeField(blank=True, null=True, verbose_name="Giờ bắt đầu tùy chỉnh"),
        ),
        migrations.AddField(
            model_name="doctorprofile",
            name="custom_work_end",
            field=models.TimeField(blank=True, null=True, verbose_name="Giờ kết thúc tùy chỉnh"),
        ),
    ]
