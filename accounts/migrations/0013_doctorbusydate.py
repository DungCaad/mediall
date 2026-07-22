from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_doctorprofile_is_verified"),
    ]

    operations = [
        migrations.CreateModel(
            name="DoctorBusyDate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Busy date")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="busy_dates", to="accounts.doctorprofile")),
            ],
            options={"ordering": ["date"]},
        ),
        migrations.AddConstraint(
            model_name="doctorbusydate",
            constraint=models.UniqueConstraint(fields=("doctor", "date"), name="unique_doctor_busy_date"),
        ),
    ]
