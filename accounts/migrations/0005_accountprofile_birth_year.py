from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_doctor_profile_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="accountprofile",
            name="birth_year",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Birth year"),
        ),
        migrations.AlterField(
            model_name="accountprofile",
            name="phone",
            field=models.CharField(max_length=20, unique=True, verbose_name="Phone number"),
        ),
        migrations.AlterField(
            model_name="accountprofile",
            name="role",
            field=models.CharField(choices=[("patient", "Patient"), ("doctor", "Doctor")], max_length=20, verbose_name="Account role"),
        ),
        migrations.AlterField(
            model_name="accountprofile",
            name="photo",
            field=models.URLField(blank=True, verbose_name="Profile photo URL"),
        ),
        migrations.AlterField(
            model_name="accountprofile",
            name="clinic_address",
            field=models.CharField(blank=True, max_length=255, verbose_name="Clinic address"),
        ),
    ]
