from django.contrib.auth.hashers import make_password
from django.db import migrations


DEMO_ACCOUNTS = [
    {
        "username": "benhnhan01",
        "password": "Patient@123",
        "phone": "0901000001",
        "role": "patient",
    },
    {
        "username": "benhnhan02",
        "password": "Patient@123",
        "phone": "0901000002",
        "role": "patient",
    },
    {
        "username": "bacsi01",
        "password": "Doctor@123",
        "phone": "0902000001",
        "role": "doctor",
    },
    {
        "username": "bacsi02",
        "password": "Doctor@123",
        "phone": "0902000002",
        "role": "doctor",
    },
]


def seed_demo_accounts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    AccountProfile = apps.get_model("accounts", "AccountProfile")

    for account in DEMO_ACCOUNTS:
        user, created = User.objects.update_or_create(
            username=account["username"],
            defaults={
                "password": make_password(account["password"]),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        if not created and not user.password:
            user.password = make_password(account["password"])
            user.save(update_fields=["password"])

        AccountProfile.objects.update_or_create(
            user=user,
            defaults={
                "phone": account["phone"],
                "role": account["role"],
            },
        )


def remove_demo_accounts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(username__in=[account["username"] for account in DEMO_ACCOUNTS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_accounts, remove_demo_accounts),
    ]
