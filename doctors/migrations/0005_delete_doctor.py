from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("doctors", "0004_english_provider_copy"),
    ]

    operations = [
        migrations.DeleteModel(name="Doctor"),
    ]
