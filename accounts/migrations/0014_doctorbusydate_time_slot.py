from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_doctorbusydate"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="doctorbusydate",
            name="unique_doctor_busy_date",
        ),
        migrations.AddField(
            model_name="doctorbusydate",
            name="time_slot",
            field=models.CharField(default="", max_length=20, verbose_name="Busy time slot"),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="doctorbusydate",
            options={"ordering": ["date", "time_slot"]},
        ),
        migrations.AddConstraint(
            model_name="doctorbusydate",
            constraint=models.UniqueConstraint(
                fields=("doctor", "date", "time_slot"),
                name="unique_doctor_busy_time_slot",
            ),
        ),
    ]
