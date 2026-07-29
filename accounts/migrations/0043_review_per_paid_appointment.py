from django.db import migrations, models
import django.db.models.deletion


def link_existing_reviews_to_paid_appointments(apps, schema_editor):
    DoctorReview = apps.get_model("accounts", "DoctorReview")
    DoctorAppointment = apps.get_model("accounts", "DoctorAppointment")
    for review in DoctorReview.objects.all().iterator():
        appointment = (
            DoctorAppointment.objects.filter(
                patient_id=review.patient_id,
                doctor_id=review.doctor_id,
                payment_status="paid",
            )
            .order_by("-payment_submitted_at", "-id")
            .first()
        )
        if appointment:
            review.appointment_id = appointment.id
            review.save(update_fields=["appointment"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0042_alter_doctorappointment_payment_status_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="doctorreview",
            name="unique_patient_doctor_review",
        ),
        migrations.AddField(
            model_name="doctorreview",
            name="appointment",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="review",
                to="accounts.doctorappointment",
            ),
        ),
        migrations.RunPython(link_existing_reviews_to_paid_appointments, migrations.RunPython.noop),
    ]
