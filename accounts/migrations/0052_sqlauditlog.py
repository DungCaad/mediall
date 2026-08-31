from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0051_english_homepage_translations")]

    operations = [
        migrations.CreateModel(
            name="SqlAuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("INSERT", "Insert"), ("UPDATE", "Update"), ("DELETE", "Delete")], max_length=6)),
                ("table_name", models.CharField(blank=True, max_length=255)),
                ("sql", models.TextField()),
                ("affected_rows", models.IntegerField(blank=True, null=True)),
                ("request_method", models.CharField(blank=True, max_length=10)),
                ("request_path", models.CharField(blank=True, max_length=500)),
                ("client_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="sql_audit_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "verbose_name": "SQL audit log", "verbose_name_plural": "SQL audit logs"},
        ),
    ]
