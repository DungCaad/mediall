from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0052_sqlauditlog")]

    operations = [
        migrations.AddField(
            model_name="doctorappointment",
            name="paddle_transaction_id",
            field=models.CharField(blank=True, db_index=True, default="", editable=False, max_length=40),
        ),
    ]
