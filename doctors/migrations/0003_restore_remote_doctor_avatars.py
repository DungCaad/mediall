from django.db import migrations, models


AVATAR_BY_NAME = {
    "ThS. BS. CK2 Nguyen Thi Hong Hanh": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=240&q=80",
    "TS. BS Nguyen Duc Bang": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=240&q=80",
    "Bac si Nguyen Thanh Thai": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=240&q=80",
    "Benh vien Phoi Soc Trang": "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?auto=format&fit=crop&w=240&q=80",
    "Phong kham Phoi Quoc te An Duc": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=240&q=80",
    "BS. Tran Minh Quan": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=240&q=80",
    "BS. Le Thu Ha": "https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&w=240&q=80",
    "ThS. BS Pham Anh Tuan": "https://images.unsplash.com/photo-1605684954998-685c79d6a018?auto=format&fit=crop&w=240&q=80",
}


def restore_remote_avatars(apps, schema_editor):
    Doctor = apps.get_model("doctors", "Doctor")
    for name, avatar in AVATAR_BY_NAME.items():
        Doctor.objects.filter(name=name).update(avatar=avatar)


class Migration(migrations.Migration):
    dependencies = [
        ("doctors", "0002_local_doctor_avatars"),
    ]

    operations = [
        migrations.AlterField(
            model_name="doctor",
            name="avatar",
            field=models.URLField(blank=True),
        ),
        migrations.RunPython(restore_remote_avatars, migrations.RunPython.noop),
    ]
