from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0038_blogpost"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="is_featured",
            field=models.BooleanField(default=False, verbose_name="Featured in footer"),
        ),
    ]
