from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_seed_demo_accounts"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accountprofile",
            name="role",
            field=models.CharField(choices=[("patient", "Patient"), ("doctor", "Doctor")], max_length=20),
        ),
    ]
