from django.conf import settings
from django.db import models
from pathlib import Path
from uuid import uuid4


def chat_attachment_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"chat/attachments/{instance.conversation_id}/{uuid4().hex}{extension}"


class Conversation(models.Model):
    title = models.CharField("Conversation name", max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or f"Conversation #{self.pk}"


class ConversationMember(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_memberships",
    )
    last_read_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="read_markers",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_member",
            ),
        ]

    def __str__(self):
        return f"{self.user} in {self.conversation}"


class Message(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]
    ATTACHMENT_DOCUMENT = "document"
    ATTACHMENT_IMAGE = "image"
    ATTACHMENT_VIDEO = "video"
    ATTACHMENT_TYPE_CHOICES = [
        (ATTACHMENT_DOCUMENT, "Document"),
        (ATTACHMENT_IMAGE, "Image"),
        (ATTACHMENT_VIDEO, "Video"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    content = models.TextField("Content", max_length=5000, blank=True)
    attachment = models.FileField(
        "Attachment",
        upload_to=chat_attachment_upload_to,
        blank=True,
    )
    attachment_data = models.BinaryField("Attachment data", null=True, blank=True, editable=False)
    attachment_content_type = models.CharField("Attachment content type", max_length=255, blank=True)
    attachment_size = models.PositiveBigIntegerField("Attachment size", default=0)
    attachment_type = models.CharField(
        "Attachment type",
        max_length=20,
        choices=ATTACHMENT_TYPE_CHOICES,
        blank=True,
    )
    attachment_name = models.CharField("Attachment name", max_length=255, blank=True)
    moderation_status = models.CharField(
        "Review status",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_chat_messages",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField("Rejection reason", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(
                fields=["conversation", "moderation_status", "-id"],
                name="chat_visible_message_idx",
            ),
        ]

    def __str__(self):
        summary = self.content[:60] or self.attachment_name or "Attachment"
        return f"{self.sender}: {summary}"
