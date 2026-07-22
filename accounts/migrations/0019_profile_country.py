from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0018_doctorprofile_recommended_doctors"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorprofile",
            name="country",
            field=models.CharField(blank=True, max_length=100, verbose_name="Quốc gia"),
        ),
        migrations.AddField(
            model_name="patientprofile",
            name="country",
            field=models.CharField(blank=True, max_length=100, verbose_name="Quốc gia"),
        ),
    ]
