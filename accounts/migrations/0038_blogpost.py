from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0037_doctorappointment_payment_submitted_at"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BlogPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Title")),
                ("content_html", models.TextField(verbose_name="Content")),
                ("seo_description", models.CharField(blank=True, max_length=160, verbose_name="SEO description")),
                ("tags", models.CharField(blank=True, max_length=500, verbose_name="Tags")),
                ("is_published", models.BooleanField(default=True, verbose_name="Published")),
                ("view_count", models.PositiveIntegerField(default=0, editable=False, verbose_name="View count")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="blog_posts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
