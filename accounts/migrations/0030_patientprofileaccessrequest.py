from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0029_sync_email_from_username"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PatientProfileAccessRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="profile_access_requests", to="accounts.patientprofile")),
                ("requester", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="patient_profile_access_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.AddConstraint(
            model_name="patientprofileaccessrequest",
            constraint=models.UniqueConstraint(fields=("patient", "requester"), name="unique_patient_profile_access_request"),
        ),
    ]
