import json
import mimetypes
from io import BytesIO
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Conversation, ConversationMember, Message


def build_admin_message_actions(message):
    # Nhóm nút thao tác cho từng tin nhắn trong trang quản trị
    message_actions = [
        # Nút duyệt tin nhắn
        {
            "id": "approve",
            "label": "Approve",
            "url": reverse("admin:chat_message_approve", args=[message.id]),
            "kind": "submit",
            "class_name": "message-review-approve",
        },
        # Nút xem lịch sử cuộc trò chuyện
        {
            "id": "history",
            "label": "View chat history",
            "url": reverse("admin:chat_message_history", args=[message.conversation_id]),
            "kind": "link",
            "class_name": "message-review-history",
        },
    ]
    return message_actions


def _profile_data(user):
    display_name = user.get_full_name().strip() or user.username
    avatar_url = ""
    profile_url = reverse("chat_member_profile", args=[user.id])
    try:
        account = user.profile
        role_profile = (
            getattr(account, "doctor_details", None)
            or getattr(account, "patient_details", None)
        )
        if role_profile:
            display_name = role_profile.full_name.strip() or display_name
            avatar_url = role_profile.avatar_url
        doctor_profile = getattr(account, "doctor_details", None)
        if doctor_profile:
            profile_url = reverse("doctor_profile_detail", args=[doctor_profile.id])
    except (AttributeError, ObjectDoesNotExist):
        pass
    return {
        "id": user.id,
        "name": display_name,
        "initial": display_name[:1].upper(),
        "avatar_url": avatar_url,
        "profile_url": profile_url,
    }


@login_required(login_url="login_account")
def member_profile(request, user_id):
    member = get_object_or_404(User, id=user_id, is_active=True)
    if member.id == request.user.id:
        return redirect("profile")
    shared_membership = (
        ConversationMember.objects.filter(
            user=request.user,
            conversation_id__in=ConversationMember.objects.filter(user=member).values("conversation_id"),
        )
        .select_related("conversation")
        .first()
    )
    if not shared_membership:
        raise Http404

    profile = _profile_data(member)
    role = "Member"
    details = []
    try:
        account = member.profile
        role = account.get_role_display()
        doctor = getattr(account, "doctor_details", None)
        patient = getattr(account, "patient_details", None)
        role_profile = doctor or patient
        if doctor:
            return redirect("doctor_profile_detail", doctor_id=doctor.id)
        if role_profile and role_profile.country:
            details.append({"label": "Country", "value": role_profile.country})
    except (AttributeError, ObjectDoesNotExist):
        pass

    return render(request, "chat/member_profile.html", {
        "member": profile,
        "member_role": role,
        "member_details": details,
        "back_url": f"{reverse('chat')}?conversation={shared_membership.conversation_id}",
    })


def _visible_messages(conversation, user):
    return conversation.messages.filter(
        Q(moderation_status=Message.STATUS_APPROVED) | Q(sender=user)
    ).select_related("sender").defer("attachment_data")


def _serialize_message(message, user):
    mine = message.sender_id == user.id
    sender = _profile_data(message.sender)
    display_status = "failed" if mine and message.moderation_status == Message.STATUS_REJECTED else "sent"
    attachment = None
    if message.attachment_size or message.attachment:
        attachment = {
            "type": message.attachment_type,
            "name": message.attachment_name,
            "url": reverse("chat_message_attachment", args=[message.id]),
        }
    return {
        "id": message.id,
        "content": message.content,
        "attachment": attachment,
        "is_mine": mine,
        "display_status": display_status,
        "sender": sender,
        "created_at": timezone.localtime(message.created_at).isoformat(),
        "time_label": timezone.localtime(message.created_at).strftime("%H:%M"),
    }


def _get_membership(conversation_id, user):
    return get_object_or_404(
        ConversationMember.objects.select_related("conversation"),
        conversation_id=conversation_id,
        user=user,
    )


@login_required(login_url="login_account")
def chat_page(request):
    memberships = list(
        ConversationMember.objects.filter(user=request.user)
        .select_related("conversation")
        .prefetch_related("conversation__members__user")
        .order_by("-conversation__updated_at")
    )
    selected_id = request.GET.get("conversation")
    selected = next(
        (item for item in memberships if str(item.conversation_id) == selected_id),
        memberships[0] if memberships else None,
    )

    conversations = []
    for membership in memberships:
        conversation = membership.conversation
        others = [member.user for member in conversation.members.all() if member.user_id != request.user.id]
        peer = _profile_data(others[0]) if others else _profile_data(request.user)
        visible = _visible_messages(conversation, request.user)
        last_message = visible.order_by("-id").first()
        unread = visible.filter(
            moderation_status=Message.STATUS_APPROVED,
        ).exclude(sender=request.user)
        if membership.last_read_message_id:
            unread = unread.filter(id__gt=membership.last_read_message_id)
        conversations.append({
            "id": conversation.id,
            "title": conversation.title or peer["name"],
            "avatar_url": peer["avatar_url"],
            "initial": peer["initial"],
            "profile_url": peer["profile_url"],
            "preview": (last_message.content or last_message.attachment_name) if last_message else "No messages yet",
            "time": timezone.localtime(last_message.created_at).strftime("%H:%M") if last_message else "",
            "unread": unread.count(),
            "is_group": conversation.members.count() > 2,
            "active": selected is not None and selected.conversation_id == conversation.id,
        })

    selected_data = None
    if selected:
        others = [member.user for member in selected.conversation.members.all() if member.user_id != request.user.id]
        peer = _profile_data(others[0]) if others else _profile_data(request.user)
        selected_data = {
            "id": selected.conversation_id,
            "title": selected.conversation.title or peer["name"],
            "avatar_url": peer["avatar_url"],
            "initial": peer["initial"],
            "profile_url": peer["profile_url"],
        }

    users = [_profile_data(user) for user in User.objects.filter(is_active=True).exclude(id=request.user.id).order_by("username")[:100]]

    # Nhóm bộ lọc danh sách cuộc trò chuyện
    chat_filters = [
        # Nút hiển thị tất cả cuộc trò chuyện
        {"id": "all", "label": "All", "active": True},
        # Nút hiển thị cuộc trò chuyện chưa đọc
        {"id": "unread", "label": "Unread", "active": False},
        # Nút hiển thị các cuộc trò chuyện nhóm
        {"id": "group", "label": "Groups", "active": False},
    ]

    # Nhóm lựa chọn tệp đính kèm trong khung soạn tin nhắn
    composer_attachment_options = [
        # Nút chọn tài liệu
        {"id": "document", "label": "Document", "icon": "document", "accept": "*/*"},
        # Nút chọn ảnh hoặc video
        {"id": "media", "label": "Photos & videos", "icon": "media", "accept": "image/*,video/*"},
    ]
    return render(request, "chat/chat.html", {
        "conversations": conversations,
        "selected_conversation": selected_data,
        "available_users": users,
        "chat_filters": chat_filters,
        "composer_attachment_options": composer_attachment_options,
    })


@require_GET
@login_required(login_url="login_account")
def message_list(request, conversation_id):
    membership = _get_membership(conversation_id, request.user)
    try:
        limit = min(40, max(10, int(request.GET.get("limit", 20))))
    except ValueError:
        limit = 20
    queryset = _visible_messages(membership.conversation, request.user)
    before_id = request.GET.get("before_id")
    after_id = request.GET.get("after_id")
    if before_id and before_id.isdigit():
        queryset = queryset.filter(id__lt=int(before_id))
    if after_id and after_id.isdigit():
        queryset = queryset.filter(id__gt=int(after_id))
        rows = list(queryset.order_by("id")[:limit])
    else:
        rows = list(queryset.order_by("-id")[:limit])
        rows.reverse()
    if rows:
        membership.last_read_message = rows[-1]
        membership.save(update_fields=["last_read_message"])
    return JsonResponse({
        "messages": [_serialize_message(message, request.user) for message in rows],
        "status_updates": [
            {
                "id": message.id,
                "display_status": "failed" if message.moderation_status == Message.STATUS_REJECTED else "sent",
            }
            for message in membership.conversation.messages.filter(sender=request.user).order_by("-id")[:50]
        ],
        "has_more": len(rows) == limit,
    })


@require_POST
@login_required(login_url="login_account")
def send_message(request, conversation_id):
    membership = _get_membership(conversation_id, request.user)
    attachment = request.FILES.get("attachment")
    if attachment:
        if attachment.size > 50 * 1024 * 1024:
            return JsonResponse({"error": "Attachments cannot exceed 50 MB."}, status=400)
        content_type = (attachment.content_type or "application/octet-stream").lower()
        if content_type.startswith("image/"):
            attachment_type = Message.ATTACHMENT_IMAGE
        elif content_type.startswith("video/"):
            attachment_type = Message.ATTACHMENT_VIDEO
        else:
            attachment_type = Message.ATTACHMENT_DOCUMENT
        message = Message.objects.create(
            conversation=membership.conversation,
            sender=request.user,
            content="",
            attachment_data=attachment.read(),
            attachment_content_type=content_type,
            attachment_size=attachment.size,
            attachment_type=attachment_type,
            attachment_name=Path(attachment.name).name[:255],
        )
        membership.conversation.save(update_fields=["updated_at"])
        return JsonResponse({"message": _serialize_message(message, request.user)}, status=201)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request data."}, status=400)
    content = str(data.get("content", "")).strip()
    if not content:
        return JsonResponse({"error": "Enter a message."}, status=400)
    if len(content) > 5000:
        return JsonResponse({"error": "Messages cannot exceed 5,000 characters."}, status=400)
    message = Message.objects.create(
        conversation=membership.conversation,
        sender=request.user,
        content=content,
    )
    membership.conversation.save(update_fields=["updated_at"])
    return JsonResponse({"message": _serialize_message(message, request.user)}, status=201)


@require_GET
@login_required(login_url="login_account")
def message_attachment(request, message_id):
    message = get_object_or_404(
        Message.objects.select_related("sender", "conversation"),
        id=message_id,
    )
    can_review = request.user.is_staff
    is_sender = message.sender_id == request.user.id
    is_approved_recipient = (
        message.moderation_status == Message.STATUS_APPROVED
        and message.conversation.members.filter(user=request.user).exists()
    )
    if not (can_review or is_sender or is_approved_recipient):
        raise Http404
    as_attachment = message.attachment_type == Message.ATTACHMENT_DOCUMENT
    content_type = (
        message.attachment_content_type
        or mimetypes.guess_type(message.attachment_name)[0]
        or "application/octet-stream"
    )
    if message.attachment_data is not None:
        source = BytesIO(bytes(message.attachment_data))
    elif message.attachment:
        source = message.attachment.open("rb")
    else:
        raise Http404
    response = FileResponse(
        source,
        as_attachment=as_attachment,
        filename=message.attachment_name,
        content_type=content_type,
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_POST
@login_required(login_url="login_account")
@transaction.atomic
def create_conversation(request):
    try:
        data = json.loads(request.body or "{}")
        user_id = int(data.get("user_id"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Invalid member."}, status=400)
    other = get_object_or_404(User, id=user_id, is_active=True)
    if other.id == request.user.id:
        return JsonResponse({"error": "You cannot start a conversation with yourself."}, status=400)
    existing = Conversation.objects.filter(
        members__user=request.user,
    ).filter(
        members__user=other,
    ).annotate().distinct()
    for conversation in existing:
        if conversation.members.count() == 2:
            return JsonResponse({"conversation_id": conversation.id})
    conversation = Conversation.objects.create()
    ConversationMember.objects.bulk_create([
        ConversationMember(conversation=conversation, user=request.user),
        ConversationMember(conversation=conversation, user=other),
    ])
    return JsonResponse({"conversation_id": conversation.id}, status=201)
