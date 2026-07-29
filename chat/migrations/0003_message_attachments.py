from django.db import migrations, models

import chat.models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0002_alter_conversation_title_alter_message_content_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="content",
            field=models.TextField(blank=True, max_length=5000, verbose_name="Content"),
        ),
        migrations.AddField(
            model_name="message",
            name="attachment",
            field=models.FileField(blank=True, upload_to=chat.models.chat_attachment_upload_to, verbose_name="Attachment"),
        ),
        migrations.AddField(
            model_name="message",
            name="attachment_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Attachment name"),
        ),
        migrations.AddField(
            model_name="message",
            name="attachment_type",
            field=models.CharField(blank=True, choices=[("document", "Document"), ("image", "Image"), ("video", "Video")], max_length=20, verbose_name="Attachment type"),
        ),
    ]
