from django.db import migrations


def sync_email_from_username(apps, schema_editor):
    User = apps.get_model("auth", "User")
    users = User.objects.filter(email="", username__contains="@")
    for user in users.iterator():
        user.email = user.username
        user.save(update_fields=["email"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0028_doctorappointment_moderation_status"),
    ]

    operations = [
        migrations.RunPython(sync_email_from_username, migrations.RunPython.noop),
    ]
