from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0043_review_per_paid_appointment"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorappointment",
            name="completion_status",
            field=models.CharField(
                choices=[("pending", "Completion pending"), ("completed", "Completed")],
                db_index=True,
                default="pending",
                max_length=20,
                verbose_name="Completion status",
            ),
        ),
        migrations.AddField(
            model_name="doctorappointment",
            name="completed_at",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="Completed at"),
        ),
        migrations.AddField(
            model_name="doctorappointment",
            name="completed_by",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="completed_consultation_orders",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
