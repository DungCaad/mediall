from django.db import migrations


def remove_staff_profile_access_requests(apps, schema_editor):
    PatientProfileAccessRequest = apps.get_model("accounts", "PatientProfileAccessRequest")
    PatientProfileAccessRequest.objects.filter(requester__is_staff=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0033_appointment_service_and_fee"),
    ]

    operations = [
        migrations.RunPython(remove_staff_profile_access_requests, migrations.RunPython.noop),
    ]
