from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0039_blogpost_is_featured"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeaturedPostGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Group name")),
                ("position", models.PositiveIntegerField(default=0, verbose_name="Position")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["position", "created_at"],
            },
        ),
        migrations.AddField(
            model_name="blogpost",
            name="featured_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="posts",
                to="accounts.featuredpostgroup",
            ),
        ),
    ]
