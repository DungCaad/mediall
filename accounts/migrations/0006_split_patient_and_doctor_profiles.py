from django.db import migrations, models
import django.db.models.deletion


def split_existing_profiles(apps, schema_editor):
    AccountProfile = apps.get_model("accounts", "AccountProfile")
    PatientProfile = apps.get_model("accounts", "PatientProfile")
    DoctorProfile = apps.get_model("accounts", "DoctorProfile")

    for account in AccountProfile.objects.all():
        if account.role == "doctor":
            DoctorProfile.objects.get_or_create(
                account_id=account.pk,
                defaults={
                    "birth_year": account.birth_year,
                    "photo": account.photo,
                    "clinic_address": account.clinic_address,
                },
            )
        else:
            PatientProfile.objects.get_or_create(
                account_id=account.pk,
                defaults={"birth_year": account.birth_year},
            )


def merge_existing_profiles(apps, schema_editor):
    AccountProfile = apps.get_model("accounts", "AccountProfile")
    PatientProfile = apps.get_model("accounts", "PatientProfile")
    DoctorProfile = apps.get_model("accounts", "DoctorProfile")

    for profile in PatientProfile.objects.all():
        AccountProfile.objects.filter(pk=profile.account_id).update(birth_year=profile.birth_year)
    for profile in DoctorProfile.objects.all():
        AccountProfile.objects.filter(pk=profile.account_id).update(
            birth_year=profile.birth_year,
            photo=profile.photo,
            clinic_address=profile.clinic_address,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_accountprofile_birth_year"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatientProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(blank=True, max_length=150, verbose_name="Full name")),
                ("birth_year", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Birth year")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("address", models.CharField(blank=True, max_length=255, verbose_name="Home address")),
                ("emergency_contact", models.CharField(blank=True, max_length=100, verbose_name="Emergency contact")),
                ("account", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="patient_details", to="accounts.accountprofile")),
            ],
        ),
        migrations.CreateModel(
            name="DoctorProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(blank=True, max_length=150, verbose_name="Full name")),
                ("birth_year", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Birth year")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("photo", models.URLField(verbose_name="Profile photo URL")),
                ("clinic_address", models.CharField(max_length=255, verbose_name="Clinic address")),
                ("specialties", models.CharField(blank=True, max_length=255, verbose_name="Specialties")),
                ("bio", models.TextField(blank=True, verbose_name="Professional biography")),
                ("account", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="doctor_details", to="accounts.accountprofile")),
            ],
        ),
        migrations.RunPython(split_existing_profiles, merge_existing_profiles),
        migrations.RemoveField(model_name="accountprofile", name="birth_year"),
        migrations.RemoveField(model_name="accountprofile", name="photo"),
        migrations.RemoveField(model_name="accountprofile", name="clinic_address"),
    ]
