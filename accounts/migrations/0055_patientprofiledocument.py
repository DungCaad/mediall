import accounts.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0054_immediate_payment_translations"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatientProfileDocument",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to=accounts.models.patient_profile_document_upload_to,
                        verbose_name="File",
                    ),
                ),
                ("original_name", models.CharField(max_length=255)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documents",
                        to="accounts.patientprofile",
                    ),
                ),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
    ]
