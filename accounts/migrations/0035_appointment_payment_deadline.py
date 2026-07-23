from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone


def set_existing_payment_deadlines(apps, schema_editor):
    DoctorAppointment = apps.get_model("accounts", "DoctorAppointment")
    DoctorAppointment.objects.filter(
        moderation_status="approved",
        payment_status="awaiting",
        payment_due_at__isnull=True,
    ).update(payment_due_at=timezone.now() + timedelta(hours=24))


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0034_remove_staff_profile_access_requests"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorappointment",
            name="payment_due_at",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="Payment deadline"),
        ),
        migrations.AlterField(
            model_name="doctorappointment",
            name="payment_status",
            field=models.CharField(choices=[("awaiting", "Chờ thanh toán"), ("paid", "Đã thanh toán"), ("expired", "Payment expired")], default="awaiting", max_length=20),
        ),
        migrations.RunPython(set_existing_payment_deadlines, migrations.RunPython.noop),
    ]
