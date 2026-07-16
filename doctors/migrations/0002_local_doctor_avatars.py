from django.db import migrations, models


AVATAR_BY_NAME = {
    "ThS. BS. CK2 Nguyen Thi Hong Hanh": "/static/images/doctor-female.svg",
    "TS. BS Nguyen Duc Bang": "/static/images/doctor-male.svg",
    "Bac si Nguyen Thanh Thai": "/static/images/doctor-male.svg",
    "Benh vien Phoi Soc Trang": "/static/images/clinic.svg",
    "Phong kham Phoi Quoc te An Duc": "/static/images/clinic.svg",
    "BS. Tran Minh Quan": "/static/images/doctor-male.svg",
    "BS. Le Thu Ha": "/static/images/doctor-female.svg",
    "ThS. BS Pham Anh Tuan": "/static/images/doctor-male.svg",
}


def use_local_avatars(apps, schema_editor):
    Doctor = apps.get_model("doctors", "Doctor")
    for name, avatar in AVATAR_BY_NAME.items():
        Doctor.objects.filter(name=name).update(avatar=avatar)


class Migration(migrations.Migration):
    dependencies = [
        ("doctors", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="doctor",
            name="avatar",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(use_local_avatars, migrations.RunPython.noop),
    ]
