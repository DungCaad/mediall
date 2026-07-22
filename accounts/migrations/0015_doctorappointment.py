from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0014_doctorbusydate_time_slot"),
    ]

    operations = [
        migrations.CreateModel(
            name="DoctorAppointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("appointment_date", models.DateField(verbose_name="Appointment date")),
                ("time_slot", models.CharField(max_length=20, verbose_name="Appointment time slot")),
                ("reason", models.TextField(blank=True, verbose_name="Reason for visit")),
                ("status", models.CharField(choices=[("pending", "Chờ xác nhận"), ("accepted", "Đã chấp nhận"), ("rejected", "Đã từ chối")], default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="appointments", to="accounts.doctorprofile")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="appointments", to="accounts.patientprofile")),
                ("referred_doctor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="received_referrals", to="accounts.doctorprofile")),
            ],
            options={"ordering": ["appointment_date", "time_slot"]},
        ),
        migrations.AddConstraint(
            model_name="doctorappointment",
            constraint=models.UniqueConstraint(fields=("doctor", "appointment_date", "time_slot"), name="unique_doctor_appointment_time_slot"),
        ),
    ]
