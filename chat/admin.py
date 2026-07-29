from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from .models import Conversation, ConversationMember, Message
from .views import build_admin_message_actions


class ConversationMemberInline(admin.TabularInline):
    model = ConversationMember
    extra = 1
    autocomplete_fields = ("user",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "updated_at")
    search_fields = ("title", "members__user__username", "members__user__email")
    inlines = (ConversationMemberInline,)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    change_list_template = "admin/chat/message/review_list.html"
    search_fields = ("content", "sender__username", "sender__email")

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        custom_urls = [
            path(
                "<int:message_id>/approve/",
                self.admin_site.admin_view(self.approve_message_view),
                name="chat_message_approve",
            ),
            path(
                "conversation/<int:conversation_id>/history/",
                self.admin_site.admin_view(self.conversation_history_view),
                name="chat_message_history",
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        if not self.has_view_or_change_permission(request):
            return self.admin_site.login(request)
        pending_messages = (
            Message.objects.filter(moderation_status=Message.STATUS_PENDING)
            .select_related("sender", "conversation")
            .prefetch_related("conversation__members__user")
            .order_by("created_at")
        )
        rows = []
        for message in pending_messages:
            recipients = [
                member.user.get_full_name().strip() or member.user.username
                for member in message.conversation.members.all()
                if member.user_id != message.sender_id
            ]
            rows.append({
                "message": message,
                "sender_name": message.sender.get_full_name().strip() or message.sender.username,
                "recipient_names": ", ".join(recipients) or "—",
                "actions": build_admin_message_actions(message),
            })
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Review messages",
            "rows": rows,
            "pending_count": len(rows),
            "has_view_permission": self.has_view_permission(request),
        }
        return TemplateResponse(request, self.change_list_template, context)

    def approve_message_view(self, request, message_id):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        if not self.has_change_permission(request):
            return self.admin_site.login(request)
        message = get_object_or_404(Message, id=message_id)
        if message.moderation_status == Message.STATUS_PENDING:
            message.moderation_status = Message.STATUS_APPROVED
            message.reviewed_by = request.user
            message.reviewed_at = timezone.now()
            message.rejection_reason = ""
            message.save(update_fields=[
                "moderation_status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
                "updated_at",
            ])
            messages.success(request, "The message was approved and delivered to the recipient.")
        return redirect(reverse("admin:chat_message_changelist"))

    def conversation_history_view(self, request, conversation_id):
        if not self.has_view_or_change_permission(request):
            return self.admin_site.login(request)
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related("members__user"),
            id=conversation_id,
        )
        history = conversation.messages.select_related("sender", "reviewed_by").order_by("created_at")
        member_names = [
            member.user.get_full_name().strip() or member.user.username
            for member in conversation.members.all()
        ]
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Chat history",
            "conversation": conversation,
            "member_names": member_names,
            "history": history,
            "review_list_url": reverse("admin:chat_message_changelist"),
        }
        return TemplateResponse(request, "admin/chat/message/history.html", context)


@admin.register(ConversationMember)
class ConversationMemberAdmin(admin.ModelAdmin):
    list_display = ("conversation", "user", "joined_at")
    search_fields = ("conversation__title", "user__username", "user__email")
    autocomplete_fields = ("conversation", "user", "last_read_message")
