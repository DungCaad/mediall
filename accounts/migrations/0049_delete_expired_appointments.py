from django.db import migrations


def delete_expired_appointments(apps, schema_editor):
    DoctorAppointment = apps.get_model("accounts", "DoctorAppointment")
    DoctorAppointment.objects.filter(payment_status="expired").delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0048_profile_form_translations")]

    operations = [
        migrations.RunPython(
            delete_expired_appointments,
            migrations.RunPython.noop,
        ),
    ]
