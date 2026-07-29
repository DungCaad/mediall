import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Conversation, ConversationMember, Message


class ChatFlowTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username="sender", password="test-pass-123")
        self.receiver = User.objects.create_user(username="receiver", password="test-pass-123")
        self.outsider = User.objects.create_user(username="outsider", password="test-pass-123")
        self.conversation = Conversation.objects.create()
        ConversationMember.objects.create(conversation=self.conversation, user=self.sender)
        ConversationMember.objects.create(conversation=self.conversation, user=self.receiver)

    def test_pending_message_is_sent_for_sender_and_hidden_from_receiver(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            content="Tin đang chờ duyệt",
        )

        self.client.force_login(self.sender)
        sender_response = self.client.get(reverse("chat_messages", args=[self.conversation.id]))
        self.assertEqual(sender_response.status_code, 200)
        self.assertEqual(sender_response.json()["messages"][0]["display_status"], "sent")

        self.client.force_login(self.receiver)
        receiver_response = self.client.get(reverse("chat_messages", args=[self.conversation.id]))
        self.assertEqual(receiver_response.json()["messages"], [])

        message.moderation_status = Message.STATUS_APPROVED
        message.save(update_fields=["moderation_status"])
        approved_response = self.client.get(reverse("chat_messages", args=[self.conversation.id]))
        self.assertEqual(approved_response.json()["messages"][0]["content"], "Tin đang chờ duyệt")

    def test_rejected_message_becomes_failed_only_for_sender(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            content="Tin bị từ chối",
            moderation_status=Message.STATUS_REJECTED,
        )
        self.client.force_login(self.sender)
        response = self.client.get(reverse("chat_messages", args=[self.conversation.id]))
        self.assertEqual(response.json()["messages"][0]["display_status"], "failed")
        self.assertEqual(response.json()["status_updates"][0]["id"], message.id)

        self.client.force_login(self.receiver)
        response = self.client.get(reverse("chat_messages", args=[self.conversation.id]))
        self.assertEqual(response.json()["messages"], [])

    def test_non_member_cannot_read_conversation(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("chat_messages", args=[self.conversation.id]))
        self.assertEqual(response.status_code, 404)

    def test_avatar_profile_is_visible_only_to_shared_conversation_members(self):
        self.client.force_login(self.sender)
        response = self.client.get(reverse("chat_member_profile", args=[self.receiver.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.receiver.username)

        self.client.force_login(self.outsider)
        response = self.client.get(reverse("chat_member_profile", args=[self.receiver.id]))
        self.assertEqual(response.status_code, 404)

    def test_send_endpoint_creates_pending_message(self):
        self.client.force_login(self.sender)
        response = self.client.post(
            reverse("chat_send_message", args=[self.conversation.id]),
            data=json.dumps({"content": "Xin chào"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        message = Message.objects.get()
        self.assertEqual(message.moderation_status, Message.STATUS_PENDING)
        self.assertEqual(response.json()["message"]["display_status"], "sent")

    def test_attachment_is_sent_immediately_but_hidden_until_approved(self):
        image_bytes = b"test-image-content"
        self.client.force_login(self.sender)
        response = self.client.post(
            reverse("chat_send_message", args=[self.conversation.id]),
            data={
                "attachment": SimpleUploadedFile(
                    "photo.png",
                    image_bytes,
                    content_type="image/png",
                ),
            },
        )
        self.assertEqual(response.status_code, 201)
        message = Message.objects.get()
        self.assertEqual(message.moderation_status, Message.STATUS_PENDING)
        self.assertEqual(message.attachment_type, Message.ATTACHMENT_IMAGE)
        self.assertEqual(message.attachment_content_type, "image/png")
        self.assertEqual(message.attachment_size, len(image_bytes))
        self.assertEqual(bytes(message.attachment_data), image_bytes)
        self.assertFalse(message.attachment)
        self.assertEqual(response.json()["message"]["attachment"]["name"], "photo.png")

        attachment_url = reverse("chat_message_attachment", args=[message.id])
        attachment_response = self.client.get(attachment_url)
        self.assertEqual(attachment_response.status_code, 200)
        self.assertEqual(attachment_response["Content-Type"], "image/png")
        self.assertEqual(b"".join(attachment_response.streaming_content), image_bytes)

        self.client.force_login(self.receiver)
        self.assertEqual(self.client.get(attachment_url).status_code, 404)
        self.assertEqual(
            self.client.get(reverse("chat_messages", args=[self.conversation.id])).json()["messages"],
            [],
        )

        message.moderation_status = Message.STATUS_APPROVED
        message.save(update_fields=["moderation_status"])
        self.assertEqual(self.client.get(attachment_url).status_code, 200)
        messages = self.client.get(reverse("chat_messages", args=[self.conversation.id])).json()["messages"]
        self.assertEqual(messages[0]["attachment"]["type"], "image")


class ChatAdminReviewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="review-admin",
            email="admin@example.test",
            password="test-pass-123",
        )
        self.sender = User.objects.create_user(username="sender-admin-test")
        self.receiver = User.objects.create_user(username="receiver-admin-test")
        self.conversation = Conversation.objects.create()
        ConversationMember.objects.create(conversation=self.conversation, user=self.sender)
        ConversationMember.objects.create(conversation=self.conversation, user=self.receiver)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            content="Tin cần admin duyệt",
        )
        self.client.force_login(self.admin)

    def test_review_list_only_shows_pending_messages(self):
        response = self.client.get(reverse("admin:chat_message_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tin cần admin duyệt")
        self.assertContains(response, "View chat history")

    def test_individual_approval_updates_message(self):
        response = self.client.post(reverse("admin:chat_message_approve", args=[self.message.id]))
        self.assertRedirects(response, reverse("admin:chat_message_changelist"))
        self.message.refresh_from_db()
        self.assertEqual(self.message.moderation_status, Message.STATUS_APPROVED)
        self.assertEqual(self.message.reviewed_by, self.admin)

    def test_history_page_shows_conversation_messages(self):
        response = self.client.get(reverse("admin:chat_message_history", args=[self.conversation.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tin cần admin duyệt")
        self.assertContains(response, self.sender.username)
