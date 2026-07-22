from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_doctorappointment"),
    ]

    operations = [
        migrations.CreateModel(
            name="DoctorReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(verbose_name="Rating")),
                ("comment", models.TextField(blank=True, verbose_name="Comment")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="accounts.doctorprofile")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="doctor_reviews", to="accounts.patientprofile")),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.AddConstraint(
            model_name="doctorreview",
            constraint=models.UniqueConstraint(fields=("patient", "doctor"), name="unique_patient_doctor_review"),
        ),
        migrations.AddConstraint(
            model_name="doctorreview",
            constraint=models.CheckConstraint(condition=models.Q(("rating__gte", 1), ("rating__lte", 5)), name="doctor_review_rating_1_to_5"),
        ),
    ]
