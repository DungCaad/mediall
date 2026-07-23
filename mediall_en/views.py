import calendar
import json
import mimetypes
import struct
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from datetime import date, datetime, timedelta
from urllib import error, parse, request as urllib_request

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Avg, F, Min, Q
from django.forms import modelform_factory
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST

from accounts.models import AccountProfile, AppointmentAttachment, BlogPost, DoctorAppointment, DoctorBusyDate, DoctorProfile, DoctorReview, FeaturedPostGroup, MedicalRecord, PatientProfile, PatientProfileAccessRequest


STANDARD_PATIENT_PRICE_MULTIPLIER = Decimal("2.05")
MEMBER_PATIENT_PRICE_MULTIPLIER = Decimal("1.50")


class SafePostHTMLParser(HTMLParser):
    allowed_tags = {
        "a", "blockquote", "br", "div", "em", "h2", "h3", "hr", "li",
        "ol", "p", "strong", "u", "ul",
    }
    void_tags = {"br", "hr"}
    blocked_tags = {"script", "style"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.blocked_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.blocked_tags:
            self.blocked_depth += 1
            return
        if self.blocked_depth:
            return
        if tag not in self.allowed_tags:
            return
        safe_attrs = []
        if tag == "a":
            href = dict(attrs).get("href", "").strip()
            if href.startswith(("https://", "http://", "mailto:", "/")):
                safe_attrs = [
                    ("href", href),
                    ("target", "_blank"),
                    ("rel", "noopener noreferrer"),
                ]
        attributes = "".join(
            f' {name}="{escape(value, quote=True)}"'
            for name, value in safe_attrs
        )
        self.parts.append(f"<{tag}{attributes}>")

    def handle_endtag(self, tag):
        if tag in self.blocked_tags and self.blocked_depth:
            self.blocked_depth -= 1
            return
        if self.blocked_depth:
            return
        if tag in self.allowed_tags and tag not in self.void_tags:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.blocked_depth:
            self.parts.append(escape(data))

    def get_html(self):
        return "".join(self.parts).strip()


def sanitize_post_html(value):
    parser = SafePostHTMLParser()
    parser.feed(value or "")
    parser.close()
    return parser.get_html()


def calculate_patient_consultation_fee(base_fee, is_member=False):
    if base_fee is None:
        return None
    multiplier = MEMBER_PATIENT_PRICE_MULTIPLIER if is_member else STANDARD_PATIENT_PRICE_MULTIPLIER
    return (base_fee * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_account_email(user):
    if user.email:
        return user.email
    if "@" in user.username:
        return user.username
    return "Not provided"


def get_account_display_name(user):
    return user.email or user.username or "Not provided"


def _read_ebml_vint(data, offset):
    if offset >= len(data):
        return None, 0
    first_byte = data[offset]
    mask = 0x80
    length = 1
    while length <= 8 and not first_byte & mask:
        mask >>= 1
        length += 1
    if length > 8 or offset + length > len(data):
        return None, 0
    value = first_byte & (mask - 1)
    for byte in data[offset + 1:offset + length]:
        value = (value << 8) | byte
    return value, length


def get_uploaded_video_duration(uploaded_file):
    original_position = uploaded_file.tell()
    try:
        uploaded_file.seek(0)
        data = uploaded_file.read()
    finally:
        uploaded_file.seek(original_position)

    extension = Path(uploaded_file.name).suffix.lower()
    if extension in {".mp4", ".mov"}:
        marker_position = data.find(b"mvhd")
        if marker_position < 0 or marker_position + 32 > len(data):
            return None
        version = data[marker_position + 4]
        if version == 0:
            timescale = int.from_bytes(data[marker_position + 16:marker_position + 20], "big")
            duration = int.from_bytes(data[marker_position + 20:marker_position + 24], "big")
        elif version == 1:
            timescale = int.from_bytes(data[marker_position + 24:marker_position + 28], "big")
            duration = int.from_bytes(data[marker_position + 28:marker_position + 36], "big")
        else:
            return None
        return duration / timescale if timescale else None

    if extension == ".webm":
        timecode_scale = 1_000_000
        scale_position = data.find(b"\x2a\xd7\xb1")
        if scale_position >= 0:
            scale_size, scale_size_length = _read_ebml_vint(data, scale_position + 3)
            scale_start = scale_position + 3 + scale_size_length
            if scale_size and scale_start + scale_size <= len(data):
                timecode_scale = int.from_bytes(data[scale_start:scale_start + scale_size], "big")

        duration_position = data.find(b"\x44\x89")
        if duration_position < 0:
            return None
        duration_size, duration_size_length = _read_ebml_vint(data, duration_position + 2)
        duration_start = duration_position + 2 + duration_size_length
        if duration_size == 4 and duration_start + 4 <= len(data):
            duration_value = struct.unpack(">f", data[duration_start:duration_start + 4])[0]
        elif duration_size == 8 and duration_start + 8 <= len(data):
            duration_value = struct.unpack(">d", data[duration_start:duration_start + 8])[0]
        else:
            return None
        return duration_value * timecode_scale / 1_000_000_000

    return None


def expire_overdue_appointment_payments():
    now = timezone.now()
    return DoctorAppointment.objects.filter(
        moderation_status=DoctorAppointment.MODERATION_APPROVED,
        payment_status=DoctorAppointment.PAYMENT_AWAITING,
        payment_due_at__isnull=False,
        payment_due_at__lte=now,
    ).exclude(status=DoctorAppointment.STATUS_REJECTED).update(
        payment_status=DoctorAppointment.PAYMENT_EXPIRED,
        status=DoctorAppointment.STATUS_REJECTED,
        updated_at=now,
    )


def verify_recaptcha(token, remote_ip=""):
    if not token or not settings.RECAPTCHA_SECRET_KEY:
        return False

    payload = {
        "secret": settings.RECAPTCHA_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    verification_request = urllib_request.Request(
        "https://www.google.com/recaptcha/api/siteverify",
        data=parse.urlencode(payload).encode("utf-8"),
        method="POST",
    )

    try:
        with urllib_request.urlopen(verification_request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return False

    return result.get("success") is True


@require_POST
def translate_to_english(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid translation request."}, status=400)

    source_text = str(payload.get("text", "")).strip()
    if not source_text:
        return JsonResponse({"error": "There is no text to translate."}, status=400)
    if len(source_text) > 10000:
        return JsonResponse({"error": "The text is too long to translate."}, status=400)

    query = parse.urlencode({
        "client": "gtx",
        "sl": "auto",
        "tl": "en",
        "dt": "t",
        "q": source_text,
    })
    try:
        with urllib_request.urlopen(
            f"https://translate.googleapis.com/translate_a/single?{query}",
            timeout=8,
        ) as response:
            translation_data = json.loads(response.read().decode("utf-8"))
        translated_text = "".join(
            segment[0] for segment in translation_data[0] if segment and segment[0]
        ).strip()
    except (error.URLError, TimeoutError, json.JSONDecodeError, IndexError, TypeError):
        return JsonResponse({"error": "Translation is temporarily unavailable."}, status=502)

    return JsonResponse({"translation": translated_text})


@login_required
def appointment_attachment_file(request, attachment_id):
    attachment = get_object_or_404(
        AppointmentAttachment.objects.select_related(
            "appointment__patient__account__user",
            "appointment__doctor__account__user",
        ),
        pk=attachment_id,
    )
    appointment = attachment.appointment
    patient_can_view = request.user == appointment.patient.account.user
    doctor_can_view = (
        request.user == appointment.doctor.account.user
        and appointment.moderation_status == DoctorAppointment.MODERATION_APPROVED
    )
    if not request.user.is_staff and not patient_can_view and not doctor_can_view:
        return HttpResponseForbidden("You do not have permission to view this attachment.")

    content_type = mimetypes.guess_type(attachment.original_name)[0] or "application/octet-stream"
    return FileResponse(
        attachment.file.open("rb"),
        as_attachment=False,
        filename=attachment.original_name,
        content_type=content_type,
    )


def build_admin_order_actions():
    # Action buttons shown on every consultation request in /admin/orders
    return [
        # Button that approves the request and sends it to the doctor
        {
            "id": "verify",
            "label": "Verify",
            "type": "submit",
            "class_name": "admin-order-action verify",
        },
        # Button that confirms the patient's consultation payment
        {
            "id": "confirm-payment",
            "label": "Confirm payment",
            "confirmed_label": "Payment confirmed",
            "type": "submit",
            "class_name": "admin-order-action confirm-payment",
        },
        # Button that opens all order information, images, and videos
        {
            "id": "details",
            "label": "View order details",
            "type": "link",
            "class_name": "admin-order-action details",
        },
        # Button that permanently removes a rejected, expired, or failed request
        {
            "id": "cleanup",
            "label": "Clean up",
            "type": "submit",
            "class_name": "admin-order-action cleanup",
        },
    ]


def can_cleanup_admin_order(appointment):
    return (
        appointment.moderation_status == DoctorAppointment.MODERATION_REJECTED
        or appointment.status == DoctorAppointment.STATUS_REJECTED
        or appointment.payment_status == DoctorAppointment.PAYMENT_EXPIRED
    )


def can_confirm_admin_order_payment(appointment):
    return (
        appointment.moderation_status == DoctorAppointment.MODERATION_APPROVED
        and appointment.payment_status == DoctorAppointment.PAYMENT_AWAITING
        and appointment.payment_submitted_at is not None
    )


@staff_member_required
def admin_orders(request):
    expire_overdue_appointment_payments()
    if request.method == "POST":
        order_action = request.POST.get("order_action")
        appointment = get_object_or_404(DoctorAppointment, pk=request.POST.get("appointment_id"))
        if order_action == "verify":
            if appointment.moderation_status == DoctorAppointment.MODERATION_PENDING:
                appointment.moderation_status = DoctorAppointment.MODERATION_APPROVED
                appointment.payment_due_at = timezone.now() + timedelta(hours=24)
                appointment.save(update_fields=["moderation_status", "payment_due_at", "updated_at"])
                messages.success(request, "The consultation request was verified and sent to the doctor.")
            else:
                messages.info(request, "This consultation request has already been reviewed.")
        elif order_action == "cleanup":
            if not can_cleanup_admin_order(appointment):
                messages.error(request, "Only rejected, expired, or failed consultation requests can be cleaned up.")
            else:
                appointment_id = appointment.pk
                with transaction.atomic():
                    for attachment in appointment.attachments.all():
                        attachment.file.delete(save=False)
                    appointment.delete()
                messages.success(request, f"Consultation request #{appointment_id} was permanently cleaned up.")
        elif order_action == "confirm-payment":
            if not can_confirm_admin_order_payment(appointment):
                messages.error(request, "Only approved consultation requests awaiting payment can be confirmed.")
            else:
                appointment.payment_status = DoctorAppointment.PAYMENT_PAID
                appointment.save(update_fields=["payment_status", "updated_at"])
                messages.success(request, f"Payment for consultation request #{appointment.pk} was confirmed.")
        else:
            messages.error(request, "Invalid order action.")
        return redirect("admin_orders")

    orders = list(
        DoctorAppointment.objects.select_related(
            "patient__account__user",
            "doctor__account__user",
        ).prefetch_related("attachments").order_by("-created_at")
    )
    for order in orders:
        order.can_cleanup = can_cleanup_admin_order(order)
        order.can_confirm_payment = can_confirm_admin_order_payment(order)
    orders.sort(key=lambda order: order.moderation_status != DoctorAppointment.MODERATION_PENDING)

    unpaid_orders = [
        order for order in orders
        if order.payment_status != DoctorAppointment.PAYMENT_PAID
    ]
    paid_orders = [
        order for order in orders
        if order.payment_status == DoctorAppointment.PAYMENT_PAID
    ]

    # Dãy nút phân nhóm đơn hàng theo trạng thái thanh toán
    order_payment_groups = [
        # Nút hiển thị các đơn chưa thanh toán
        {
            "id": "unpaid",
            "label": "Chưa thanh toán",
            "active": True,
            "orders": unpaid_orders,
            "count": len(unpaid_orders),
            "empty_title": "Không có đơn chưa thanh toán",
            "empty_description": "Tất cả đơn hiện tại đã được thanh toán.",
        },
        # Nút hiển thị các đơn đã thanh toán
        {
            "id": "paid",
            "label": "Đã thanh toán",
            "active": False,
            "orders": paid_orders,
            "count": len(paid_orders),
            "empty_title": "Chưa có đơn đã thanh toán",
            "empty_description": "Các đơn được xác nhận thanh toán sẽ xuất hiện tại đây.",
        },
    ]

    return render(request, "admin/orders.html", {
        "title": "Consultation orders",
        "order_payment_groups": order_payment_groups,
        "order_actions": build_admin_order_actions(),
        "pending_count": sum(
            order.moderation_status == DoctorAppointment.MODERATION_PENDING for order in orders
        ),
    })


@staff_member_required
def admin_order_detail(request, appointment_id):
    order = get_object_or_404(
        DoctorAppointment.objects.select_related(
            "patient__account__user",
            "doctor__account__user",
        ).prefetch_related("attachments"),
        pk=appointment_id,
    )
    return render(request, "admin/order_detail.html", {
        "title": f"Consultation request #{order.pk}",
        "order": order,
    })


@login_required
@require_POST
def submit_appointment_payment(request, appointment_id):
    expire_overdue_appointment_payments()
    appointment = get_object_or_404(
        DoctorAppointment,
        pk=appointment_id,
        patient__account__user=request.user,
    )
    if (
        appointment.moderation_status != DoctorAppointment.MODERATION_APPROVED
        or appointment.payment_status != DoctorAppointment.PAYMENT_AWAITING
        or not appointment.payment_due_at
    ):
        messages.error(request, "This consultation request is not available for payment.")
    elif appointment.payment_submitted_at:
        messages.info(request, "Your payment is already awaiting admin confirmation.")
    else:
        appointment.payment_submitted_at = timezone.now()
        appointment.save(update_fields=["payment_submitted_at", "updated_at"])
        messages.success(request, "Payment submitted. Please wait for admin confirmation.")
    return redirect("/profile?tab=consultation-requests#consultation-request-{}".format(appointment.pk))


def build_post_editor_toolbar():
    # Dãy nút định dạng nội dung trong trình soạn thảo bài viết
    return [
        # Nút in đậm
        {"id": "bold", "label": "B", "title": "In đậm", "command": "bold", "class_name": "bold"},
        # Nút in nghiêng
        {"id": "italic", "label": "I", "title": "In nghiêng", "command": "italic", "class_name": "italic"},
        # Nút gạch chân
        {"id": "underline", "label": "U", "title": "Gạch chân", "command": "underline", "class_name": "underline"},
        # Nút tiêu đề cấp hai
        {"id": "heading", "label": "H2", "title": "Tiêu đề", "command": "formatBlock", "value": "h2"},
        # Nút đoạn văn
        {"id": "paragraph", "label": "¶", "title": "Đoạn văn", "command": "formatBlock", "value": "p"},
        # Nút danh sách dấu chấm
        {"id": "unordered-list", "label": "• List", "title": "Danh sách dấu chấm", "command": "insertUnorderedList"},
        # Nút danh sách đánh số
        {"id": "ordered-list", "label": "1. List", "title": "Danh sách đánh số", "command": "insertOrderedList"},
        # Nút trích dẫn
        {"id": "quote", "label": "❝", "title": "Trích dẫn", "command": "formatBlock", "value": "blockquote"},
        # Nút chèn liên kết
        {"id": "link", "label": "🔗", "title": "Chèn liên kết", "command": "createLink", "prompt": True},
        # Nút xóa định dạng
        {"id": "clear", "label": "Tx", "title": "Xóa định dạng", "command": "removeFormat"},
    ]


def build_admin_post_actions(post):
    # Dãy nút thao tác của từng bài viết trong trang quản lý
    return [
        # Nút thay đổi trạng thái bài viết nổi bật
        {
            "type": "submit",
            "name": "toggle_featured",
            "value": post.pk,
            "label": "Bỏ nổi bật" if post.is_featured else "Đặt nổi bật",
            "class_name": "featured" if post.is_featured else "",
        },
        # Nút lưu nhóm bài viết
        {
            "type": "submit",
            "name": "assign_group",
            "value": post.pk,
            "label": "Lưu nhóm",
            "class_name": "group",
        },
        # Nút xem bài viết
        {
            "type": "link",
            "label": "Xem bài",
            "url": reverse("post_detail", args=[post.pk]),
            "class_name": "secondary",
        },
    ]


def get_featured_footer_groups():
    groups = list(FeaturedPostGroup.objects.all())
    footer_groups = []

    for group in groups:
        posts = list(BlogPost.objects.filter(
            is_published=True,
            is_featured=True,
            featured_group=group,
        ).only("id", "title").order_by("-created_at"))
        if posts:
            footer_groups.append({"name": group.name, "posts": posts})

    ungrouped_posts = list(BlogPost.objects.filter(
        is_published=True,
        is_featured=True,
        featured_group__isnull=True,
    ).only("id", "title").order_by("-created_at"))
    if ungrouped_posts:
        footer_groups.append({"name": "Bài viết nổi bật", "posts": ungrouped_posts})

    return footer_groups


@staff_member_required
def admin_create_post(request):
    errors = []
    form_values = {
        "title": "",
        "content_html": "",
        "seo_description": "",
        "tags": "",
        "is_published": True,
    }

    if request.method == "POST":
        form_values = {
            "title": request.POST.get("title", "").strip(),
            "content_html": request.POST.get("content_html", "").strip(),
            "seo_description": request.POST.get("seo_description", "").strip(),
            "tags": request.POST.get("tags", "").strip(),
            "is_published": request.POST.get("is_published") == "on",
        }
        sanitized_content = sanitize_post_html(form_values["content_html"])
        form_values["content_html"] = sanitized_content
        plain_content = strip_tags(sanitized_content).strip()

        if not form_values["title"]:
            errors.append("Vui lòng nhập tiêu đề bài viết.")
        if not plain_content:
            errors.append("Vui lòng nhập nội dung bài viết.")
        if len(form_values["seo_description"]) > 160:
            errors.append("Mô tả SEO không được vượt quá 160 ký tự.")

        normalized_tags = []
        normalized_tag_keys = set()
        for tag in form_values["tags"].replace("\n", ",").split(","):
            tag = tag.strip()
            if tag and tag.casefold() not in normalized_tag_keys:
                normalized_tags.append(tag)
                normalized_tag_keys.add(tag.casefold())

        if not errors:
            post = BlogPost.objects.create(
                title=form_values["title"],
                content_html=sanitized_content,
                seo_description=form_values["seo_description"],
                tags=", ".join(normalized_tags),
                author=request.user,
                is_published=form_values["is_published"],
            )
            messages.success(request, f'Đã tạo bài viết “{post.title}”.')
            return redirect("admin_posts")

    return render(request, "admin/post.html", {
        "title": "Tạo bài viết",
        "editor_toolbar": build_post_editor_toolbar(),
        "form_values": form_values,
        "form_errors": errors,
        "recent_posts": BlogPost.objects.select_related("author")[:10],
    })


@staff_member_required
def admin_posts(request):
    if request.method == "POST":
        if "create_group" in request.POST:
            group_name = request.POST.get("group_name", "").strip()
            if not group_name:
                messages.error(request, "Vui lòng nhập tên nhóm.")
            elif FeaturedPostGroup.objects.filter(name__iexact=group_name).exists():
                messages.error(request, "Tên nhóm này đã tồn tại.")
            else:
                FeaturedPostGroup.objects.create(
                    name=group_name,
                    position=FeaturedPostGroup.objects.count(),
                )
                messages.success(request, f'Đã tạo nhóm “{group_name}”.')
        elif "assign_group" in request.POST:
            post_id = request.POST.get("assign_group", "").strip()
            post = get_object_or_404(BlogPost, pk=post_id)
            group_id = request.POST.get(f"group_{post.pk}", "").strip()
            post.featured_group = (
                get_object_or_404(FeaturedPostGroup, pk=group_id)
                if group_id else None
            )
            post.is_featured = True
            post.save(update_fields=["featured_group", "is_featured", "updated_at"])
            group_label = post.featured_group.name if post.featured_group else "Bài viết nổi bật"
            messages.success(request, f'Đã đưa “{post.title}” vào nhóm “{group_label}”.')
        else:
            post_id = request.POST.get("toggle_featured", "").strip()
            post = get_object_or_404(BlogPost, pk=post_id)
            post.is_featured = not post.is_featured
            post.save(update_fields=["is_featured", "updated_at"])
            state = "bài viết nổi bật" if post.is_featured else "bài viết thường"
            messages.success(request, f'Đã chuyển “{post.title}” thành {state}.')
        return redirect("admin_posts")

    posts = list(BlogPost.objects.select_related("author"))
    for post in posts:
        post.admin_actions = build_admin_post_actions(post)

    return render(request, "admin/posts.html", {
        "title": "Quản lý bài viết",
        "posts": posts,
        "featured_count": sum(post.is_featured for post in posts),
        "featured_groups": FeaturedPostGroup.objects.all(),
    })


def post_detail(request, post_id):
    posts = BlogPost.objects.select_related("author")
    if not request.user.is_staff:
        posts = posts.filter(is_published=True)
    post = get_object_or_404(posts, pk=post_id)

    BlogPost.objects.filter(pk=post.pk).update(view_count=F("view_count") + 1)
    post.view_count += 1

    search_query = request.GET.get("q", "").strip()
    sidebar_posts = BlogPost.objects.filter(is_published=True).exclude(pk=post.pk)
    if search_query:
        sidebar_posts = sidebar_posts.filter(
            Q(title__icontains=search_query)
            | Q(tags__icontains=search_query)
            | Q(seo_description__icontains=search_query)
        )

    context = {
        "post": post,
        "search_query": search_query,
        "sidebar_posts": sidebar_posts[:6],
        "featured_footer_groups": get_featured_footer_groups(),
    }
    context.update(build_header_context(request=request))
    return render(request, "post_detail.html", context)


@staff_member_required
def admin_profiles(request, profile_type):
    # Profile type navigation buttons in the admin profile directory
    profile_type_buttons = [
        # Doctor profiles button
        {
            "id": "doctor",
            "label": "Doctors",
            "url_name": "admin_doctor_profiles",
            "active": profile_type == "doctor",
        },
        # User profiles button
        {
            "id": "users",
            "label": "Users",
            "url_name": "admin_user_profiles",
            "active": profile_type == "users",
        },
    ]

    if profile_type == "doctor":
        profiles = DoctorProfile.objects.select_related("account__user").order_by("full_name", "account_id")
        profile_rows = [
            {
                "profile_id": profile.pk,
                "name": profile.display_name,
                "email": get_account_email(profile.account.user),
                "phone": profile.account.phone or "Not provided",
                "detail": profile.specialties or "Specialties not provided",
                "avatar": profile.avatar,
                "is_verified": profile.is_verified,
            }
            for profile in profiles
        ]
        page_title = "Doctor profiles"
        page_description = "View doctor information and manage green verification ticks."
        detail_url_name = "admin_doctor_profile_detail"
    else:
        profiles = PatientProfile.objects.select_related("account__user").order_by("full_name", "account_id")
        profile_rows = [
            {
                "profile_id": profile.pk,
                "name": profile.full_name or get_account_display_name(profile.account.user),
                "email": get_account_email(profile.account.user),
                "phone": profile.account.phone or "Not provided",
                "detail": profile.country or "Country not provided",
                "avatar": profile.avatar,
                "is_verified": False,
                "is_member": profile.is_member,
            }
            for profile in profiles
        ]
        page_title = "User profiles"
        page_description = "View registered patient account information."
        detail_url_name = "admin_user_profile_detail"

    return render(request, "admin/profiles.html", {
        "title": page_title,
        "page_title": page_title,
        "page_description": page_description,
        "profile_rows": profile_rows,
        "profile_type": profile_type,
        "profile_type_buttons": profile_type_buttons,
        "detail_url_name": detail_url_name,
    })


def render_admin_no_profile(request, profile_type):
    is_doctor = profile_type == "doctor"
    return render(request, "admin/no_profile.html", {
        "title": "No profile",
        "profile_label": "doctor" if is_doctor else "user",
        "profile_list_url_name": (
            "admin_doctor_profiles" if is_doctor else "admin_user_profiles"
        ),
    }, status=404)


@staff_member_required
def admin_profile_detail(request, account_id=None, profile_type=None, profile_id=None):
    if profile_type == "doctor":
        role_profile = DoctorProfile.objects.select_related("account__user").filter(pk=profile_id).first()
        if role_profile is None:
            return render_admin_no_profile(request, profile_type)
        account = role_profile.account
    elif profile_type == "users":
        role_profile = PatientProfile.objects.select_related("account__user").filter(pk=profile_id).first()
        if role_profile is None:
            return render_admin_no_profile(request, profile_type)
        account = role_profile.account
    else:
        account = AccountProfile.objects.select_related("user").filter(pk=account_id).first()
        if account is None:
            return render_admin_no_profile(request, "users")
        role_profile = None

    if (
        account.role == AccountProfile.ROLE_PATIENT
        and request.user != account.user
        and not request.user.is_staff
    ):
        if role_profile is None:
            role_profile = PatientProfile.objects.filter(account=account).first()
            if role_profile is None:
                return render_admin_no_profile(request, "users")
        access_request = PatientProfileAccessRequest.objects.filter(
            patient=role_profile,
            requester=request.user,
        ).first()
        has_profile_access = (
            access_request is not None
            and access_request.status == PatientProfileAccessRequest.STATUS_APPROVED
        )
        if not has_profile_access:
            if request.method == "POST" and request.POST.get("profile_access_action") == "request":
                access_request, _ = PatientProfileAccessRequest.objects.update_or_create(
                    patient=role_profile,
                    requester=request.user,
                    defaults={"status": PatientProfileAccessRequest.STATUS_PENDING},
                )
                messages.success(request, "The patient has been asked to approve access to their profile.")
                redirect_kwarg = "profile_id" if profile_type else "account_id"
                redirect_id = role_profile.pk if profile_type else account.pk
                return redirect(request.resolver_match.url_name, **{redirect_kwarg: redirect_id})
            return render(request, "admin/profile_consent_required.html", {
                "title": "Patient consent required",
                "patient": role_profile,
                "access_request": access_request,
                "profile_list_url_name": "admin_user_profiles",
            }, status=403)

    if account.role == AccountProfile.ROLE_DOCTOR:
        if role_profile is None:
            role_profile = DoctorProfile.objects.filter(account=account).first()
            if role_profile is None:
                return render_admin_no_profile(request, "doctor")
        if request.method == "POST":
            verification_action = request.POST.get("verification_action")
            if verification_action not in {"grant", "revoke"}:
                messages.error(request, "Invalid doctor verification action.")
                redirect_id = role_profile.pk if profile_type else account.pk
                redirect_kwarg = "profile_id" if profile_type else "account_id"
                return redirect(request.resolver_match.url_name, **{redirect_kwarg: redirect_id})

            role_profile.is_verified = verification_action == "grant"
            role_profile.save(update_fields=["is_verified", "updated_at"])
            if role_profile.is_verified:
                messages.success(request, "The green verification tick has been granted to this doctor.")
            else:
                messages.success(request, "The green verification tick has been removed from this doctor.")
            redirect_id = role_profile.pk if profile_type else account.pk
            redirect_kwarg = "profile_id" if profile_type else "account_id"
            return redirect(request.resolver_match.url_name, **{redirect_kwarg: redirect_id})

        profile_title = "Doctor profile"
        profile_details = [
            {"label": "Full name", "value": role_profile.full_name or "Not provided"},
            {"label": "Email", "value": get_account_email(account.user)},
            {"label": "Phone number", "value": account.phone or "Not provided"},
            {"label": "Birth year", "value": role_profile.birth_year or "Not provided"},
            {"label": "Country", "value": role_profile.country or "Not provided"},
            {"label": "Specialties", "value": role_profile.specialties or "Not provided"},
            {"label": "Position", "value": role_profile.position or "Not provided"},
            {"label": "Workplace", "value": role_profile.workplace or "Not provided"},
            {"label": "Years of experience", "value": role_profile.years_experience if role_profile.years_experience is not None else "Not provided"},
            {"label": "Video consultation fee", "value": f"${role_profile.video_consultation_fee} /visit" if role_profile.video_consultation_fee is not None else "Not provided"},
            {"label": "Message consultation fee", "value": f"${role_profile.message_consultation_fee} /visit" if role_profile.message_consultation_fee is not None else "Not provided"},
            {"label": "Verified doctor", "value": "Yes" if role_profile.is_verified else "No"},
            {"label": "Introduction", "value": role_profile.introduction or "Not provided", "multiline": True},
            {"label": "Training history", "value": role_profile.training_history or "Not provided", "multiline": True},
        ]
    else:
        if role_profile is None:
            role_profile = PatientProfile.objects.filter(account=account).first()
            if role_profile is None:
                return render_admin_no_profile(request, "users")
        if request.method == "POST":
            membership_action = request.POST.get("membership_action")
            if membership_action not in {"grant", "revoke"}:
                messages.error(request, "Invalid patient membership action.")
                redirect_id = role_profile.pk if profile_type else account.pk
                redirect_kwarg = "profile_id" if profile_type else "account_id"
                return redirect(request.resolver_match.url_name, **{redirect_kwarg: redirect_id})

            role_profile.is_member = membership_action == "grant"
            role_profile.save(update_fields=["is_member", "updated_at"])
            if role_profile.is_member:
                messages.success(request, "The yellow member star has been granted to this patient.")
            else:
                messages.success(request, "The yellow member star has been removed from this patient.")
            redirect_id = role_profile.pk if profile_type else account.pk
            redirect_kwarg = "profile_id" if profile_type else "account_id"
            return redirect(request.resolver_match.url_name, **{redirect_kwarg: redirect_id})

        profile_title = "Patient profile"
        profile_details = [
            {"label": "Full name", "value": role_profile.full_name or "Not provided"},
            {"label": "Email", "value": get_account_email(account.user)},
            {"label": "Phone number", "value": account.phone or "Not provided"},
            {"label": "Birth year", "value": role_profile.birth_year or "Not provided"},
            {"label": "Country", "value": role_profile.country or "Not provided"},
            {"label": "Home address", "value": role_profile.address or "Not provided", "multiline": True},
            {"label": "Membership", "value": "Member" if role_profile.is_member else "Not a member"},
        ]

    return render(request, "admin/profile_detail.html", {
        "title": f"{profile_title} #{account.pk}",
        "account": account,
        "role_profile": role_profile,
        "profile_title": profile_title,
        "profile_details": profile_details,
        "profile_display_name": role_profile.full_name or get_account_display_name(account.user),
        "can_manage_verification": account.role == AccountProfile.ROLE_DOCTOR,
        "can_manage_membership": account.role == AccountProfile.ROLE_PATIENT,
        "profile_list_url_name": (
            "admin_doctor_profiles"
            if account.role == AccountProfile.ROLE_DOCTOR
            else "admin_user_profiles"
        ),
    })


def is_vietnamese_host(request):
    host = request.get_host().split(":", 1)[0].lower()
    return host.startswith("vi.")


def build_header_context(language="en", guest_modal=False, request=None):
    expire_overdue_appointment_payments()
    # Dãy mục điều hướng dùng chung trên header
    if language == "vi":
        # Dãy mục điều hướng tiếng Việt
        header_nav_items = [
            # # Mục Danh mục sức khỏe
            # {"label": "Danh mục sức khỏe ▾"},
        ]
        home_aria_label = "Trang chủ Mediall"
        account_menu_aria_label = "Mở menu tài khoản"
        profile_label = "Hồ sơ"
        profile_note = "Phát triển sau"
        sign_out_label = "Đăng xuất"
        sign_in_label = "Đăng nhập"
        sign_up_label = "Đăng ký"
    else:
        # Dãy mục điều hướng tiếng Anh
        header_nav_items = [
            # # Mục Danh mục sức khỏe
            # {"label": "Danh mục sức khỏe ▾"},
        ]
        home_aria_label = "Mediall home"
        account_menu_aria_label = "Open account menu"
        profile_label = "Profile"
        profile_note = "Coming soon"
        sign_out_label = "Sign out"
        sign_in_label = "Sign in"
        sign_up_label = "Sign up"

    # Dãy liên kết tài khoản khi người dùng đã đăng nhập
    authenticated_account_actions = [
        # Liên kết hồ sơ
        {
            "label": profile_label,
            "url_name": "profile",
            "class_name": "",
            "note": "",
        },
        # Link to the patient's previous medical records
        # Liên kết đăng xuất
        {
            "label": sign_out_label,
            "url_name": "logout_account",
            "class_name": "",
            "note": "",
        },
    ]

    # Dãy nút hoặc liên kết tài khoản khi người dùng chưa đăng nhập
    guest_account_actions = [
        # Nút hoặc liên kết đăng nhập
        {
            "label": sign_in_label,
            "modal_target": "login" if guest_modal else "",
            "url_name": "home",
        },
        # Nút hoặc liên kết đăng ký
        {
            "label": sign_up_label,
            "modal_target": "register" if guest_modal else "",
            "url_name": "home",
        },
    ]

    header_avatar_url = ""
    header_display_name = ""
    header_is_verified = False
    header_is_member = False
    header_is_patient = False
    header_notifications = []
    consultation_request_count = 0
    if request is not None and request.user.is_authenticated:
        header_display_name = request.user.email or request.user.username
        try:
            account_profile = request.user.profile
            if account_profile.role == AccountProfile.ROLE_DOCTOR:
                role_profile = account_profile.doctor_details
            else:
                role_profile = account_profile.patient_details
            if role_profile.avatar:
                header_avatar_url = role_profile.avatar.url
            if role_profile.full_name:
                header_display_name = role_profile.full_name
            if account_profile.role == AccountProfile.ROLE_DOCTOR:
                header_is_verified = role_profile.is_verified
            else:
                header_is_patient = True
                header_is_member = role_profile.is_member

            if account_profile.role == AccountProfile.ROLE_PATIENT:
                consultation_request_count = role_profile.appointments.count()
                appointments = role_profile.appointments.select_related(
                    "doctor__account__user"
                ).order_by("-updated_at")[:8]
                for appointment in appointments:
                    doctor_name = appointment.doctor.full_name or appointment.doctor.account.user.email
                    appointment_time = f"{appointment.time_slot}, {appointment.appointment_date.strftime('%d/%m/%Y')}"

                    if appointment.moderation_status == DoctorAppointment.MODERATION_PENDING:
                        title = "Appointment request awaiting review"
                        message = f"Your request for {appointment_time} is being reviewed by the admin team."
                        notification_type = "pending"
                    elif appointment.moderation_status == DoctorAppointment.MODERATION_REJECTED:
                        title = "Appointment request was not approved"
                        message = f"Your request for {appointment_time} was declined during review."
                        notification_type = "rejected"
                    elif appointment.payment_status == DoctorAppointment.PAYMENT_EXPIRED:
                        title = "Payment deadline expired"
                        message = f"The 24-hour payment deadline for {appointment_time} has passed. This appointment is no longer being held."
                        notification_type = "rejected"
                    elif appointment.status == DoctorAppointment.STATUS_REJECTED:
                        title = "Yêu cầu đặt khám đã bị từ chối"
                        message = f"Bác sĩ {doctor_name} không thể nhận lịch {appointment_time}."
                        notification_type = "rejected"
                    elif appointment.payment_status == DoctorAppointment.PAYMENT_PAID:
                        title = "Thanh toán thành công"
                        message = f"Giờ khám của bạn với bác sĩ {doctor_name} là {appointment_time}."
                        notification_type = "paid"
                    elif appointment.moderation_status == DoctorAppointment.MODERATION_APPROVED:
                        service_label = appointment.get_service_type_display() if appointment.service_type else "consultation"
                        fee_label = f"${appointment.consultation_fee:.2f} /visit" if appointment.consultation_fee is not None else "the listed consultation fee"
                        title = "Payment required"
                        if appointment.status == DoctorAppointment.STATUS_ACCEPTED:
                            message = f"Doctor {doctor_name} accepted your {service_label.lower()} request. Please pay {fee_label}."
                        else:
                            message = f"Your {service_label.lower()} request was verified by the admin. Please pay {fee_label}."
                        notification_type = "payment"
                    else:
                        title = "Đã gửi yêu cầu lịch khám"
                        message = f"Bạn đã gửi yêu cầu lịch khám {appointment_time} cho bác sĩ {doctor_name}."
                        notification_type = "pending"

                    header_notifications.append({
                        "id": appointment.pk,
                        "title": title,
                        "message": message,
                        "type": notification_type,
                        "created_at": appointment.updated_at,
                        "href": f"/profile?tab=consultation-requests#consultation-request-{appointment.pk}",
                    })

                access_requests = role_profile.profile_access_requests.filter(
                    status=PatientProfileAccessRequest.STATUS_PENDING,
                ).select_related("requester").order_by("-updated_at")[:8]
                for access_request in access_requests:
                    requester_name = (
                        access_request.requester.get_full_name()
                        or get_account_email(access_request.requester)
                    )
                    header_notifications.append({
                        "id": f"profile-access-{access_request.pk}",
                        "title": "Yêu cầu xem hồ sơ mới",
                        "message": f"{requester_name} muốn xem hồ sơ của bạn. Hãy đồng ý hoặc từ chối yêu cầu.",
                        "type": "pending",
                        "created_at": access_request.updated_at,
                        "href": "/profile?tab=access-requests",
                    })
            else:
                appointments = role_profile.appointments.filter(
                    moderation_status=DoctorAppointment.MODERATION_APPROVED,
                ).select_related(
                    "patient__account__user"
                ).order_by("-updated_at")[:8]
                for appointment in appointments:
                    patient_name = appointment.patient.full_name or appointment.patient.account.user.email
                    appointment_time = f"{appointment.time_slot}, {appointment.appointment_date.strftime('%d/%m/%Y')}"
                    if appointment.status == DoctorAppointment.STATUS_PENDING:
                        title = "Yêu cầu đặt khám mới"
                        message = f"{patient_name} muốn đặt lịch vào {appointment_time}."
                        notification_type = "pending"
                    elif appointment.status == DoctorAppointment.STATUS_ACCEPTED:
                        title = "Đã chấp nhận lịch khám"
                        message = f"Lịch của {patient_name} vào {appointment_time} đang chờ hoàn tất."
                        notification_type = "accepted"
                    else:
                        title = "Đã từ chối lịch khám"
                        message = f"Yêu cầu của {patient_name} vào {appointment_time} đã bị từ chối."
                        notification_type = "rejected"
                    header_notifications.append({
                        "id": appointment.pk,
                        "title": title,
                        "message": message,
                        "type": notification_type,
                        "created_at": appointment.updated_at,
                        "href": f"/profile?tab=schedule&month={appointment.appointment_date.strftime('%Y-%m')}",
                    })
        except ObjectDoesNotExist:
            pass

    header_notifications.sort(key=lambda item: item["created_at"], reverse=True)
    header_notifications = header_notifications[:8]

    # Dãy nút thao tác nhanh cạnh avatar trên header
    header_quick_actions = [
        # Nút chuông mở danh sách thông báo
        {
            "id": "notifications",
            "label": "Mở thông báo",
            "kind": "notification-menu",
            "count": len(header_notifications),
            "patient_only": False,
        },
        # Nút giỏ hàng mở danh sách yêu cầu tư vấn
        {
            "id": "consultation-requests",
            "label": "Consultation requests",
            "kind": "link",
            "href": "/profile?tab=consultation-requests",
            "count": consultation_request_count,
            "patient_only": True,
        },
    ]

    return {
        "header_nav_items": header_nav_items,
        "authenticated_account_actions": authenticated_account_actions,
        "guest_account_actions": guest_account_actions,
        "header_home_aria_label": home_aria_label,
        "header_account_menu_aria_label": account_menu_aria_label,
        "header_avatar_url": header_avatar_url,
        "header_display_name": header_display_name,
        "header_is_verified": header_is_verified,
        "header_is_member": header_is_member,
        "header_is_patient": header_is_patient,
        "header_notifications": header_notifications,
        "header_notification_count": len(header_notifications),
        "header_quick_actions": header_quick_actions,
    }


@login_required
def medical_records_page(request):
    try:
        request.user.profile.patient_details
    except ObjectDoesNotExist:
        messages.error(request, "Medical records are available to patient accounts only.")
        return redirect("profile")
    return redirect("/profile?tab=medical-history")


def parse_schedule_month(month_value):
    try:
        return datetime.strptime(month_value or "", "%Y-%m").date().replace(day=1)
    except ValueError:
        return date.today().replace(day=1)


def build_schedule_time_groups(doctor_profile=None):
    schedule_type = getattr(doctor_profile, "work_schedule_type", DoctorProfile.WORK_SCHEDULE_OFFICE)
    if schedule_type == DoctorProfile.WORK_SCHEDULE_NIGHT:
        # Dãy nhóm ca làm việc ban đêm
        time_group_settings = [
            # Nhóm nút khung giờ ca đêm
            {"id": "night", "label": "Night shift", "icon": "☾", "start": "18:00", "end": "23:00", "step": 5},
        ]
    elif (
        schedule_type == DoctorProfile.WORK_SCHEDULE_CUSTOM
        and getattr(doctor_profile, "custom_work_start", None)
        and getattr(doctor_profile, "custom_work_end", None)
        and doctor_profile.custom_work_start < doctor_profile.custom_work_end
    ):
        # Dãy nhóm ca làm việc tùy chỉnh
        time_group_settings = [
            # Nhóm nút khung giờ do bác sĩ tự thiết lập
            {
                "id": "custom",
                "label": "Custom shift",
                "icon": "◷",
                "start": doctor_profile.custom_work_start.strftime("%H:%M"),
                "end": doctor_profile.custom_work_end.strftime("%H:%M"),
                "step": 5,
            },
        ]
    else:
        # Dãy nhóm ca làm việc trong giờ hành chính
        time_group_settings = [
            # Nhóm nút khung giờ buổi sáng
            {"id": "morning", "label": "Morning", "icon": "☀", "start": "08:00", "end": "12:00", "step": 5},
            # Nhóm nút khung giờ buổi chiều
            {"id": "afternoon", "label": "Afternoon", "icon": "☼", "start": "13:00", "end": "17:00", "step": 5},
        ]

    time_groups = []
    for group in time_group_settings:
        current = datetime.strptime(group["start"], "%H:%M")
        end = datetime.strptime(group["end"], "%H:%M")
        slots = []
        while current < end:
            slot_end = current + timedelta(minutes=group["step"])
            if slot_end > end:
                break
            slot_id = f"{current.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}"
            slots.append({"id": slot_id, "label": slot_id})
            current = slot_end
        time_groups.append({**group, "slots": slots})
    return time_groups


def build_doctor_schedule(doctor_profile, month_value=""):
    month_start = parse_schedule_month(month_value)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    previous_month = (month_start - timedelta(days=1)).replace(day=1)
    busy_slots_by_date = {}
    for busy_date, time_slot in doctor_profile.busy_dates.filter(
            date__gte=month_start,
            date__lt=next_month,
        ).exclude(time_slot="").values_list("date", "time_slot"):
        busy_slots_by_date.setdefault(busy_date.isoformat(), []).append(time_slot)

    appointments = list(
        doctor_profile.appointments.filter(
            appointment_date__gte=month_start,
            appointment_date__lt=next_month,
            moderation_status=DoctorAppointment.MODERATION_APPROVED,
        ).select_related("patient__account__user", "referred_doctor__account__user").prefetch_related("attachments")
    )
    appointment_counts_by_date = {}
    for appointment in appointments:
        if appointment.status != DoctorAppointment.STATUS_REJECTED:
            date_value = appointment.appointment_date.isoformat()
            appointment_counts_by_date[date_value] = appointment_counts_by_date.get(date_value, 0) + 1

    # Dãy nút chuyển tháng của lịch bác sĩ
    month_actions = [
        # Nút chuyển đến tháng trước
        {"id": "previous", "label": "‹", "direction": -1, "month": previous_month.strftime("%Y-%m"), "aria_label": "View previous dates"},
        # Nút chuyển đến tháng sau
        {"id": "next", "label": "›", "direction": 1, "month": next_month.strftime("%Y-%m"), "aria_label": "View next dates"},
    ]

    # Dãy nhãn thứ trong tuần
    weekdays = [
        {"label": "Mon"},
        {"label": "Tue"},
        {"label": "Wed"},
        {"label": "Thu"},
        {"label": "Fri"},
        {"label": "Sat"},
        {"label": "Sun"},
    ]

    weeks = []
    for week in calendar.monthcalendar(month_start.year, month_start.month):
        days = []
        for day_number in week:
            if not day_number:
                days.append({"empty": True})
                continue
            calendar_date = month_start.replace(day=day_number)
            date_value = calendar_date.isoformat()
            is_weekend_off = doctor_profile.weekend_off and calendar_date.weekday() >= 5
            days.append({
                "empty": False,
                "day": day_number,
                "date": date_value,
                "busy": date_value in busy_slots_by_date,
                "busy_slots": "|".join(busy_slots_by_date.get(date_value, [])),
                "busy_count": len(busy_slots_by_date.get(date_value, [])),
                "appointment_count": appointment_counts_by_date.get(date_value, 0),
                "weekend_off": is_weekend_off,
                "today": calendar_date == date.today(),
            })
        weeks.append(days)

    return {
        "month_value": month_start.strftime("%Y-%m"),
        "month_label": f"Tháng {month_start.month}, {month_start.year}",
        "month_actions": month_actions,
        "weekdays": weekdays,
        "weeks": weeks,
        "time_groups": build_schedule_time_groups(doctor_profile),
        # Dãy nút chọn kiểu lịch làm việc của bác sĩ
        "work_schedule_options": [
            # Nút chọn lịch giờ hành chính
            {"id": DoctorProfile.WORK_SCHEDULE_OFFICE, "label": "Giờ hành chính", "description": "08:00–12:00 và 13:00–17:00", "active": doctor_profile.work_schedule_type == DoctorProfile.WORK_SCHEDULE_OFFICE},
            # Nút chọn lịch làm ca đêm
            {"id": DoctorProfile.WORK_SCHEDULE_NIGHT, "label": "Làm ca đêm", "description": "18:00–23:00", "active": doctor_profile.work_schedule_type == DoctorProfile.WORK_SCHEDULE_NIGHT},
            # Nút chọn lịch tùy chỉnh
            {"id": DoctorProfile.WORK_SCHEDULE_CUSTOM, "label": "Tùy chỉnh", "description": "Tự chọn giờ bắt đầu và kết thúc", "active": doctor_profile.work_schedule_type == DoctorProfile.WORK_SCHEDULE_CUSTOM},
        ],
        "custom_work_start": doctor_profile.custom_work_start.strftime("%H:%M") if doctor_profile.custom_work_start else "",
        "custom_work_end": doctor_profile.custom_work_end.strftime("%H:%M") if doctor_profile.custom_work_end else "",
        "custom_schedule_active": doctor_profile.work_schedule_type == DoctorProfile.WORK_SCHEDULE_CUSTOM,
        "weekend_off": doctor_profile.weekend_off,
        # Dãy nút thao tác trong cửa sổ ca bận
        "busy_shift_actions": [
            # Nút quay lại lịch để chọn ngày khác
            {"id": "back", "label": "Quay lại lịch", "icon_path": "images/back.ico", "type": "button", "class_name": "calendar-back-circle"},
            # Nút lưu các ca bận của ngày đang chọn
            {"id": "save", "label": "Lưu lịch bận", "type": "submit", "class_name": "btn"},
        ],
        "appointments": appointments,
        # Dãy nút xử lý yêu cầu đặt khám
        "appointment_actions": [
            # Nút chấp nhận yêu cầu
            {"id": "accept", "label": "Chấp nhận", "class_name": "appointment-action accept", "opens_modal": False},
            # Nút từ chối và mở modal giới thiệu bác sĩ khác
            {"id": "reject", "label": "Từ chối", "class_name": "appointment-action reject", "opens_modal": True},
        ],
        # Dãy nút xác nhận trong modal từ chối
        "referral_actions": [
            # Nút từ chối và gửi giới thiệu đã chọn
            {"id": "reject-with-referral", "label": "Từ chối và giới thiệu", "class_name": "btn referral-confirm", "use_referral": True},
            # Nút từ chối nhưng bỏ qua giới thiệu
            {"id": "reject-without-referral", "label": "Bỏ qua giới thiệu", "class_name": "referral-skip", "use_referral": False},
        ],
        "referral_doctors": [
            {
                "id": candidate.pk,
                "name": candidate.full_name or candidate.account.user.email,
                "specialties": candidate.specialties or "Chưa cập nhật chuyên khoa",
                "workplace": candidate.workplace or "Chưa cập nhật nơi công tác",
                "avatar_url": candidate.avatar.url if candidate.avatar else "",
            }
            for candidate in DoctorProfile.objects.exclude(pk=doctor_profile.pk)
            .select_related("account__user")[:8]
        ],
    }


def build_profile_context(request, profile_form, profile_type, active_tab="personal", security_errors=None):
    # Dãy tab điều hướng trên trang hồ sơ
    profile_tabs = [
        # Tab Thông tin cá nhân
        {"id": "personal", "label": "Thông tin cá nhân"},
        # Tab Bảo mật
        {"id": "security", "label": "Bảo mật"},
        # Tab Thông tin
        {"id": "information", "label": "Thông tin"},
    ]
    doctor_schedule = None
    recommended_doctors = []
    medical_history = []
    consultation_requests = []
    profile_access_requests = []
    if isinstance(profile_form.instance, DoctorProfile):
        # Tab Lịch đặt khám chỉ dành cho bác sĩ
        profile_tabs.append({"id": "schedule", "label": "Lịch đặt khám"})
        selected_month = request.POST.get("schedule_month") or request.GET.get("month", "")
        doctor_schedule = build_doctor_schedule(profile_form.instance, selected_month)
        recommended_doctors = profile_form.instance.recommended_doctors.select_related("account__user").order_by("full_name")
    else:
        # Tab lịch sử khám dành cho tài khoản bệnh nhân
        profile_tabs.append({"id": "medical-history", "label": "Lịch sử khám"})
        # Tab danh sách yêu cầu tư vấn dành cho tài khoản bệnh nhân
        profile_tabs.append({"id": "consultation-requests", "label": "Consultation requests"})
        # Tab yêu cầu xem hồ sơ dành cho tài khoản bệnh nhân
        profile_tabs.append({"id": "access-requests", "label": "Yêu cầu xem hồ sơ"})
        consultation_requests = profile_form.instance.appointments.select_related(
            "doctor__account__user",
        ).prefetch_related("attachments").order_by("-created_at")
        medical_history = profile_form.instance.appointments.filter(
            status=DoctorAppointment.STATUS_ACCEPTED,
            appointment_date__lte=date.today(),
        ).select_related(
            "doctor__account__user",
            "medical_record",
        ).order_by("-appointment_date", "-time_slot")
        profile_access_requests = profile_form.instance.profile_access_requests.select_related(
            "requester",
        ).all()

    # Dãy nút phản hồi yêu cầu xem hồ sơ bệnh nhân
    profile_access_actions = [
        # Nút đồng ý cho xem hồ sơ
        {"id": "approve", "label": "Đồng ý", "class_name": "btn profile-access-approve"},
        # Nút từ chối cho xem hồ sơ
        {"id": "reject", "label": "Từ chối", "approved_label": "Thu hồi quyền", "class_name": "profile-access-reject"},
    ]

    # Dãy nút thao tác của biểu mẫu hồ sơ
    profile_actions = [
        # Nút Save changes
        {"label": "Save changes", "type": "submit", "class_name": "btn"},
        # Nút Cancel
        {"label": "Cancel", "type": "link", "class_name": "profile-cancel", "url_name": "home"},
    ]

    # Dãy nút thao tác trong giao diện thanh toán của bệnh nhân
    payment_modal_actions = [
        # Nút đóng giao diện thanh toán mà không gửi dữ liệu
        {
            "id": "cancel",
            "label": "Hủy",
            "type": "button",
            "class_name": "payment-modal-action cancel",
        },
        # Nút xác nhận đã thực hiện thanh toán
        {
            "id": "submit",
            "label": "Xác nhận thanh toán",
            "type": "submit",
            "class_name": "payment-modal-action submit",
        },
    ]

    # Dãy thuộc tính được tự động lấy từ model hồ sơ theo vai trò
    profile_avatar_field = profile_form["avatar"] if "avatar" in profile_form.fields else None
    profile_fields = [
        {
            "label": field.label,
            "input": (
                getattr(field.field.widget, "input_type", None)
                or ("textarea" if field.field.widget.__class__.__name__ == "Textarea" else "select")
            ),
            "field": field,
        }
        for field in profile_form.visible_fields()
        if field.name != "avatar"
    ]

    profile_avatar_url = ""
    if profile_form.instance.avatar:
        profile_avatar_url = profile_form.instance.avatar.url

    # Dãy trường nhập trong mục Bảo mật
    security_fields = [
        # Ô nhập mật khẩu hiện tại
        {"name": "current_password", "label": "Mật khẩu hiện tại", "input": "password", "autocomplete": "current-password"},
        # Ô nhập mật khẩu mới
        {"name": "new_password", "label": "Mật khẩu mới", "input": "password", "autocomplete": "new-password"},
        # Ô xác nhận mật khẩu mới
        {"name": "confirm_password", "label": "Xác nhận mật khẩu mới", "input": "password", "autocomplete": "new-password"},
    ]

    # Dãy thông tin tài khoản chỉ đọc
    account_information = [
        # Thông tin Email
        {"label": "Email", "value": request.user.email or "Chưa cập nhật"},
        # Thông tin Phone number
        {"label": "Số điện thoại", "value": request.user.profile.phone},
        # Thông tin Account type
        {"label": "Loại tài khoản", "value": profile_type},
    ]

    context = {
        "profile_fields": profile_fields,
        "profile_actions": profile_actions,
        "profile_form": profile_form,
        "profile_type": profile_type,
        "profile_avatar_field": profile_avatar_field,
        "profile_avatar_url": profile_avatar_url,
        "profile_display_name": (
            profile_form.instance.full_name
            or request.user.email
            or request.user.username
        ),
        "profile_is_verified": (
            isinstance(profile_form.instance, DoctorProfile)
            and profile_form.instance.is_verified
        ),
        "profile_is_member": (
            isinstance(profile_form.instance, PatientProfile)
            and profile_form.instance.is_member
        ),
        "profile_tabs": profile_tabs,
        "active_profile_tab": active_tab,
        "security_fields": security_fields,
        "security_errors": security_errors or [],
        "account_information": account_information,
        "doctor_schedule": doctor_schedule,
        "recommended_doctors": recommended_doctors,
        "medical_history": medical_history,
        "consultation_requests": consultation_requests,
        "profile_access_requests": profile_access_requests,
        "profile_access_actions": profile_access_actions,
        "payment_modal_actions": payment_modal_actions,
    }
    context.update(build_header_context(request=request))
    return context


def build_home_context(request):
    minimum_doctor_fees = DoctorProfile.objects.aggregate(
        message=Min("message_consultation_fee"),
        video=Min("video_consultation_fee"),
    )
    minimum_member_message_fee = calculate_patient_consultation_fee(
        minimum_doctor_fees["message"],
        is_member=True,
    )
    minimum_member_video_fee = calculate_patient_consultation_fee(
        minimum_doctor_fees["video"],
        is_member=True,
    )
    available_member_fees = [
        fee for fee in (minimum_member_message_fee, minimum_member_video_fee)
        if fee is not None
    ]
    minimum_member_fee = min(available_member_fees) if available_member_fees else None

    def display_home_fee(fee):
        if fee is None:
            return "Not available"
        return f"${fee:.2f}".rstrip("0").rstrip(".")

    home_message_price = display_home_fee(minimum_member_message_fee)
    home_video_price = display_home_fee(minimum_member_video_fee)
    home_lowest_member_price = display_home_fee(minimum_member_fee)

    # Dãy câu hỏi và nút accordion trong phần FAQ
    faq_items = [
        # Nút câu hỏi Mediall One Medical là gì
        {
            "id": "what-is-mediall",
            "question": "What is Mediall One Medical?",
            "open": False,
            "open_icon": "images/open.ico",
            "close_icon": "images/close.ico",
            "paragraphs": [
                "Mediall One Medical is a modern approach to medical care, allowing people to get care on their terms and on their schedule.",
                "Members and patients can receive ongoing support for their healthcare needs, use the Mediall app to book in-office appointments at convenient times, and request 24/7 on-demand virtual care for common health concerns.",
            ],
        },
        # Nút câu hỏi so sánh Membership và On-Demand Care
        {
            "id": "membership-vs-on-demand",
            "question": "How is One Medical Membership different from Mediall One Medical On-Demand Care? Which should I choose?",
            "open": False,
            "open_icon": "images/open.ico",
            "close_icon": "images/close.ico",
            "paragraphs": [
                "Mediall One Medical gives people two ways to get medical care: Membership and On-Demand Care.",
                "Membership provides a differentiated primary care experience with support for ongoing healthcare needs. Members can schedule appointments, connect with care teams, and receive help coordinating their care.",
                "On-Demand Care provides pay-per-visit support for common health conditions through secure messaging or video visits. It can be a good option for people who need help with a specific concern without an ongoing membership.",
            ],
            "note": "Direct Message Care availability and prices may vary.",
        },
        # Nút câu hỏi về bảo hiểm
        {
            "id": "insurance",
            "question": "Does Mediall One Medical take insurance?",
            "open": False,
            "open_icon": "images/open.ico",
            "close_icon": "images/close.ico",
            "paragraphs": [
                "Mediall One Medical accepts eligible health insurance for scheduled visits where available. On-Demand Care services may be charged separately depending on the consultation type.",
                "If you use insurance to pay for medications, you can continue to do so for medications prescribed through Mediall One Medical services.",
            ],
        },
        # Nút câu hỏi về bảo vệ thông tin sức khỏe
        {
            "id": "health-information",
            "question": "How does Mediall One Medical protect my health information?",
            "open": False,
            "open_icon": "images/open.ico",
            "close_icon": "images/close.ico",
            "paragraphs": [
                "Mediall One Medical protects customers' health information with appropriate privacy and security practices designed to keep personal data secure.",
                "We work to safeguard health information through administrative, physical, and technical controls, including encryption and access restrictions where appropriate.",
                "Mediall One Medical does not sell customers' personal information, including protected health information.",
            ],
        },
    ]

    # Dãy nút chuyển đến danh sách chủ đề sức khỏe
    answer_ctas = [
        # Nút Find your answers trong hero
        {
            "location": "hero",
            "label": "Find your answers",
            "target_id": "health-topics",
        },
        # Nút Find your answers trong banner cuối trang
        {
            "location": "bottom_banner",
            "label": "Find your answers",
            "target_id": "health-topics",
        },
    ]

    # Dãy nút lựa chọn hình thức chăm sóc
    care_options = [
        # Nút Membership
        {
            "id": "membership",
            "active": True,
            "title": "Membership",
            "description": "24/7 Health Information & Educational Guidance",
            "price": "$39",
            "price_details": ["1/yr with Prime", "Cancel at any time"],
            "panel_title": "Membership is best for",
            "features": [
                "Self-pay treatment – insurance not accepted or needed",
                "Quick treatment of common conditions",
                "Fast care by direct message or video",
                "FSA/HSA eligible",
            ],
            "care_prices": [
                {"price": home_message_price, "label": "/Direct Message Care"},
                {"price": home_video_price, "label": "/Video Care"},
            ],
            "disclaimer": "Prices vary by condition. Prices subject to change. Direct Message Care availability varies by state.",
            "button_text": "Request a treatment",
            "button_url": "#",
            "link_text": "Learn more about Membership",
            "link_url": "#",
        },
        # Nút One-time guidance
        {
            "id": "one-time",
            "title": "One-time guidance",
            "description": "Single-session information for common health queries.",
            "price": "from $11.6",
            "price_details": [
                " /consult",
                "Fees vary by consultation type and health topic",
            ],
            "panel_title": "One-time guidance",
            "features": [],
            "care_prices": [],
            "disclaimer": "",
            "button_text": "",
            "button_url": "#",
            "link_text": "",
            "link_url": "#",
        },
    ]

    # Dãy thẻ bệnh trong carousel, sử dụng ảnh nội bộ trong static/images
    carousel_conditions = [
        # Thẻ Pain & Fever Relief
        {"img": static("images/K_Conditions_Urinary-Tract-Infection_Carousel_1x_220x220.png"), "title_lines": ["Pain & Fever Relief"], "specialty": "Pain & Fever Relief"},
        # Thẻ Erectile dysfunction
        {"img": static("images/K_Conditions_Erectile-Dysfunction_Carousel_1x_220x220.png"), "title_lines": ["Erectile", "dysfunction"], "specialty": "Erectile dysfunction"},
        # Thẻ Menopause
        {"img": static("images/K_Conditions_Menopause_Carousel_1x_220x220.png"), "title_lines": ["Menopause"], "specialty": "Menopause"},
        # Thẻ Vaginal yeast infection
        {"img": static("images/K_Conditions_Vaginal-Yeast-Infection_Carousel_1x_220x220.png"), "title_lines": ["Vaginal yeast", "infection"], "specialty": "Vaginal yeast infection"},
        # Thẻ Cold and flu
        {"img": static("images/K_Conditions_Cough-Cold-Flu-Strep_Carousel_1x_220x220.png"), "title_lines": ["Cold and flu"], "specialty": "Cold and flu"},
        # Thẻ Hair & Scalp Care
        {"img": static("images/K_Conditions_DiabetesType2_Carousel_1x_220x220.png"), "title_lines": ["Hair & Scalp Care"], "specialty": "Hair & Scalp Care"},
        # Thẻ Anti-aging skin care
        {"img": static("images/K_Conditions_Anti-Aging_Carousel_1x_220x220.png"), "title_lines": ["Anti-aging skin", "care"], "specialty": "Anti-aging skin care"},
        # Thẻ Pink eye
        {"img": static("images/K_Conditions_Pink-Eye_Carousel_1x_220x220.png"), "title_lines": ["Pink eye"], "specialty": "Pink eye"},
        # Thẻ Male-pattern hair loss
        {"img": static("images/K_Conditions_Male-Hair-Loss_Carousel_1x_220x220.png"), "title_lines": ["Male-pattern", "hair loss"], "specialty": "Male-pattern hair loss"},
        # Thẻ Anxiety, stress, and depression
        {"img": static("images/K_Conditions_Bacterial-Vaginosis_Carousel_1x_220x220.png"), "title_lines": ["Anxiety, stress,", "and depression"], "specialty": "Anxiety, stress, and depression"},
        # Thẻ Birth control
        {"img": static("images/K_Conditions_Birth-Control_Carousel_1x_220x220.png"), "title_lines": ["Birth control"], "specialty": "Birth control"},
    ]

    # Dữ liệu cho danh sách bệnh lưới (Grid)
    condition_tabs = [
        {
            "name": "Most popular",
            "active": True,
            "conditions": [
                "Anti-aging skin care", "Anxiety, stress, and depression", "Birth control",
                "Cold and flu", "COVID-19", "Erectile dysfunction",
                "Male-pattern hair loss", "Pink eye", "Sinus infection",
                "Urgent virtual care", "Pain & Fever Relief", "Weight loss",
                "Vaginal yeast infection",
            ],
        },
        {
            "name": "Men's health",
            "conditions": [
                "Erectile dysfunction", "Male-pattern hair loss", "Premature ejaculation",
            ],
        },
        {
            "name": "Women's health",
            "conditions": [
                "Anxiety, stress, and depression", "Birth control", "Emergency contraception",
                "Menopause", "Period cramps", "Positive pregnancy test",
                "Pain & Fever Relief", "Vaginal dryness", "Vaginal yeast infection",
            ],
        },
        {
            "name": "General health",
            "conditions": [
                "Acid reflux", "Anxiety", "Asthma",
                "Blood pressure", "Cholesterol", "Cold and flu",
                "Cold sores", "COVID-19", "Depression",
                "Hair & Scalp Care", "Gout attack", "Hypothyroidism",
                "Mental health", "Motion sickness", "Pink eye",
                "Quit smoking", "Seasonal allergies", "Sinus infection",
                "Skin issue", "Urgent virtual care", "Weight loss",
            ],
        },
        {
            "name": "Sexual health",
            "conditions": [
                "Anxiety, stress, and depression", "Birth control", "Emergency contraception",
                "Erectile dysfunction", "Genital herpes", "Genital warts",
                "Premature ejaculation", "PrEP", "STI testing",
                "Vaginal dryness",
            ],
        },
        {
            "name": "Skin and hair",
            "conditions": [
                "Acne", "Anti-aging skin care", "Athlete's foot",
                "Dandruff", "Dark spots & melasma", "Diaper rash",
                "Eczema", "Eyelash growth", "Head lice",
                "Male-pattern hair loss", "Rosacea", "Skin issue",
                "Toenail fungus",
            ],
        },
        {
            "name": "Prescription renewal",
            "conditions": [
                "Anxiety", "Asthma", "Blood pressure",
                "Cholesterol", "Depression", "Epinephrine & EpiPens",
                "Hypothyroidism", "Other medications",
            ],
        },
    ]

    all_conditions = sorted({
        condition
        for tab in condition_tabs
        for condition in tab["conditions"]
    }, key=str.lower)
    condition_tabs.append({
        "name": "All conditions",
        "conditions": all_conditions,
    })

    # Dữ liệu cho mục "How it works"
    how_it_works = [
        {
            "step": 1,
            "img": "https://m.media-amazon.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_ciq._CB1715995169_.png",
            "title": "Answer some questions",
            "desc": "Choose a condition you need help with, answer some questions, and connect with a provider through direct message or video."
        },
        {
            "step": 2,
            "img": "https://m.media-amazon.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_treatmentplan._CB1715995169_.png",
            "title": "Get a care summary",
            "desc": "Your provider will determine what's medically appropriate for you and send any prescriptions to a pharmacy of your choice."
        },
        {
            "step": 3,
            "img": "https://m.media-amazon.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_followup._CB1715995169_.png",
            "title": "14 days to follow up",
            "desc": "You'll have unlimited follow-up messaging with your provider for 14 days after you receive your care summary."
        }
    ]

    context = {
        'faq_items': faq_items,
        'answer_ctas': answer_ctas,
        'care_options': care_options,
        'carousel_conditions': carousel_conditions,
        'condition_tabs': condition_tabs,
        'how_it_works': how_it_works,
        'home_message_price': home_message_price,
        'home_video_price': home_video_price,
        'home_lowest_member_price': home_lowest_member_price,
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
        'featured_footer_groups': get_featured_footer_groups(),
    }
    language = "vi" if is_vietnamese_host(request) else "en"
    context.update(build_header_context(language, guest_modal=language == "en", request=request))
    
    return context


def home_page(request):
    if is_vietnamese_host(request):
        return render(request, 'home_vi.html', build_home_context(request))
    return render(request, 'home.html', build_home_context(request))


def register_account(request):
    if request.method != "POST":
        return redirect("home")

    email = request.POST.get("email", "").strip().lower()
    full_name = request.POST.get("full_name", "").strip()
    phone = request.POST.get("phone", "").strip()
    password = request.POST.get("password", "")
    role = request.POST.get("role", "")
    recaptcha_token = request.POST.get("g-recaptcha-response", "").strip()
    errors = []

    if not email:
        errors.append("Please enter your email address.")
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Please enter a valid email address containing @.")
    if not full_name:
        errors.append("Please enter your full name.")
    if not phone:
        errors.append("Please enter a phone number.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if role not in {AccountProfile.ROLE_PATIENT, AccountProfile.ROLE_DOCTOR}:
        errors.append("Please choose whether you are a patient or a doctor.")
    if not verify_recaptcha(recaptcha_token, request.META.get("REMOTE_ADDR", "")):
        errors.append("Please complete the reCAPTCHA verification and try again.")
    if email and User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
        errors.append("This email address is already in use.")
    if AccountProfile.objects.filter(phone=phone).exists():
        errors.append("Phone number is already in use.")

    if errors:
        context = build_home_context(request)
        context.update({
            "registration_errors": errors,
            "registration_form": {
                "email": email,
                "full_name": full_name,
                "phone": phone,
                "role": role,
            },
            "open_register_modal": True,
        })
        return render(request, "home.html", context, status=400)

    user = User.objects.create_user(username=email, email=email, password=password)
    account_profile = AccountProfile.objects.create(
        user=user,
        phone=phone,
        role=role,
    )
    if role == AccountProfile.ROLE_DOCTOR:
        DoctorProfile.objects.create(
            account=account_profile,
            full_name=full_name,
        )
    else:
        PatientProfile.objects.create(account=account_profile, full_name=full_name)
    context = build_home_context(request)
    context["registration_success"] = "Your account has been created."
    return render(request, "home.html", context)


def login_account(request):
    if request.method != "POST":
        return redirect("home")

    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")
    recaptcha_token = request.POST.get("g-recaptcha-response", "").strip()

    login_errors = []
    if not email:
        login_errors.append("Please enter your email address.")
    else:
        try:
            validate_email(email)
        except ValidationError:
            login_errors.append("Please enter a valid email address containing @.")
    if not verify_recaptcha(recaptcha_token, request.META.get("REMOTE_ADDR", "")):
        login_errors.append("Please complete the reCAPTCHA verification and try again.")

    if login_errors:
        context = build_home_context(request)
        context.update({
            "login_errors": login_errors,
            "login_form": {"email": email},
            "open_login_modal": True,
        })
        return render(request, "home.html", context, status=400)

    account = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
    user = authenticate(request, username=account.username, password=password) if account else None

    if user is None:
        context = build_home_context(request)
        context.update({
            "login_errors": ["Email or password is incorrect."],
            "login_form": {"email": email},
            "open_login_modal": True,
        })
        return render(request, "home.html", context, status=400)

    login(request, user)
    return redirect("home")


def logout_account(request):
    logout(request)
    return redirect("home")


@login_required(login_url="home")
def profile_page(request):
    account_profile, _ = AccountProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "phone": f"profile-{request.user.pk}",
            "role": AccountProfile.ROLE_PATIENT,
        },
    )

    if account_profile.role == AccountProfile.ROLE_DOCTOR:
        role_profile, _ = DoctorProfile.objects.get_or_create(
            account=account_profile,
        )
        profile_type = "Doctor"
    else:
        role_profile, _ = PatientProfile.objects.get_or_create(account=account_profile)
        profile_type = "Patient"

    excluded_profile_fields = (
        "account",
        "recommended_doctors",
        "work_schedule_type",
        "custom_work_start",
        "custom_work_end",
        "weekend_off",
    ) if profile_type == "Doctor" else ("account",)
    RoleProfileForm = modelform_factory(
        type(role_profile),
        exclude=excluded_profile_fields,
        widgets={"avatar": forms.FileInput(attrs={"accept": "image/*"})},
    )

    active_tab = request.GET.get("tab", "personal")
    allowed_tabs = {"personal", "security", "information"}
    if profile_type == "Doctor":
        allowed_tabs.add("schedule")
    else:
        allowed_tabs.update({"medical-history", "consultation-requests", "access-requests"})
    if active_tab not in allowed_tabs:
        active_tab = "personal"

    if request.method == "POST" and request.POST.get("profile_action") == "work_schedule" and profile_type == "Doctor":
        schedule_type = request.POST.get("work_schedule_type", "")
        valid_schedule_types = {
            DoctorProfile.WORK_SCHEDULE_OFFICE,
            DoctorProfile.WORK_SCHEDULE_NIGHT,
            DoctorProfile.WORK_SCHEDULE_CUSTOM,
        }
        if schedule_type not in valid_schedule_types:
            messages.error(request, "Kiểu lịch làm việc không hợp lệ.")
            return redirect("/profile?tab=schedule")

        custom_start = None
        custom_end = None
        if schedule_type == DoctorProfile.WORK_SCHEDULE_CUSTOM:
            try:
                custom_start = datetime.strptime(request.POST.get("custom_work_start", ""), "%H:%M").time()
                custom_end = datetime.strptime(request.POST.get("custom_work_end", ""), "%H:%M").time()
            except ValueError:
                messages.error(request, "Vui lòng nhập đầy đủ giờ bắt đầu và giờ kết thúc.")
                return redirect("/profile?tab=schedule")
            if custom_start >= custom_end:
                messages.error(request, "Giờ kết thúc phải muộn hơn giờ bắt đầu.")
                return redirect("/profile?tab=schedule")

        role_profile.work_schedule_type = schedule_type
        role_profile.custom_work_start = custom_start
        role_profile.custom_work_end = custom_end
        role_profile.weekend_off = request.POST.get("weekend_off") == "on"
        role_profile.save(update_fields=["work_schedule_type", "custom_work_start", "custom_work_end", "weekend_off", "updated_at"])
        messages.success(request, "Lịch làm việc mặc định đã được cập nhật.")
        return redirect("/profile?tab=schedule")

    if request.method == "POST" and request.POST.get("profile_action") == "appointment_decision" and profile_type == "Doctor":
        appointment = DoctorAppointment.objects.filter(
            pk=request.POST.get("appointment_id"),
            doctor=role_profile,
            moderation_status=DoctorAppointment.MODERATION_APPROVED,
        ).first()
        decision = request.POST.get("decision", "")

        if not appointment or appointment.status != DoctorAppointment.STATUS_PENDING:
            messages.error(request, "Yêu cầu đặt khám không tồn tại hoặc đã được xử lý.")
        elif decision == "accept":
            appointment.status = DoctorAppointment.STATUS_ACCEPTED
            appointment.referred_doctor = None
            appointment.save(update_fields=["status", "referred_doctor", "updated_at"])
            messages.success(request, "Đã chấp nhận lịch hẹn của bệnh nhân.")
        elif decision == "reject":
            referral_doctor = DoctorProfile.objects.filter(
                pk=request.POST.get("referral_doctor_id"),
            ).exclude(pk=role_profile.pk).first()
            appointment.status = DoctorAppointment.STATUS_REJECTED
            appointment.referred_doctor = referral_doctor
            appointment.save(update_fields=["status", "referred_doctor", "updated_at"])
            if referral_doctor:
                messages.success(request, "Đã từ chối lịch hẹn và ghi nhận bác sĩ được giới thiệu.")
            else:
                messages.success(request, "Đã từ chối lịch hẹn và bỏ qua phần giới thiệu.")
        else:
            messages.error(request, "Thao tác xử lý lịch hẹn không hợp lệ.")

        appointment_month = (
            appointment.appointment_date.strftime("%Y-%m")
            if appointment
            else parse_schedule_month(request.POST.get("schedule_month", "")).strftime("%Y-%m")
        )
        return redirect(f"/profile?tab=schedule&month={appointment_month}")

    if request.method == "POST" and request.POST.get("profile_action") == "schedule" and profile_type == "Doctor":
        month_start = parse_schedule_month(request.POST.get("schedule_month", ""))
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        try:
            selected_date = datetime.strptime(request.POST.get("selected_date", ""), "%Y-%m-%d").date()
        except ValueError:
            selected_date = None

        valid_time_slots = {
            slot["id"]
            for group in build_schedule_time_groups(role_profile)
            for slot in group["slots"]
        }
        selected_time_slots = set(request.POST.getlist("busy_time_slots")) & valid_time_slots

        if selected_date and month_start <= selected_date < next_month:
            with transaction.atomic():
                DoctorBusyDate.objects.filter(doctor=role_profile, date=selected_date).delete()
                DoctorBusyDate.objects.bulk_create([
                    DoctorBusyDate(doctor=role_profile, date=selected_date, time_slot=time_slot)
                    for time_slot in sorted(selected_time_slots)
                ])

            messages.success(request, "Lịch bận của ngày đã được cập nhật.")
        else:
            messages.error(request, "Vui lòng chọn một ngày hợp lệ.")

        return redirect(
            f"/profile?tab=schedule&month={month_start.strftime('%Y-%m')}"
        )

    if request.method == "POST" and request.POST.get("profile_action") == "security":
        current_password = request.POST.get("current_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")
        security_errors = []

        if not request.user.check_password(current_password):
            security_errors.append("Mật khẩu hiện tại không đúng.")
        if new_password != confirm_password:
            security_errors.append("Mật khẩu xác nhận không khớp.")
        if new_password:
            try:
                validate_password(new_password, request.user)
            except ValidationError as validation_error:
                security_errors.extend(validation_error.messages)
        else:
            security_errors.append("Vui lòng nhập mật khẩu mới.")

        if security_errors:
            profile_form = RoleProfileForm(instance=role_profile)
            return render(
                request,
                "profile.html",
                build_profile_context(
                    request,
                    profile_form,
                    profile_type,
                    active_tab="security",
                    security_errors=security_errors,
                ),
                status=400,
            )

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        messages.success(request, "Mật khẩu đã được cập nhật.")
        return redirect("/profile?tab=security")

    if request.method == "POST" and request.POST.get("profile_action") == "profile_access_decision" and profile_type == "Patient":
        access_request = PatientProfileAccessRequest.objects.filter(
            pk=request.POST.get("access_request_id"),
            patient=role_profile,
        ).first()
        decision = request.POST.get("decision")
        if access_request is None:
            messages.error(request, "Yêu cầu xem hồ sơ không tồn tại.")
        elif decision == "approve":
            access_request.status = PatientProfileAccessRequest.STATUS_APPROVED
            access_request.save(update_fields=["status", "updated_at"])
            messages.success(request, "Bạn đã đồng ý cho tài khoản này xem hồ sơ.")
        elif decision == "reject":
            access_request.status = PatientProfileAccessRequest.STATUS_REJECTED
            access_request.save(update_fields=["status", "updated_at"])
            messages.success(request, "Bạn đã từ chối yêu cầu xem hồ sơ.")
        else:
            messages.error(request, "Phản hồi yêu cầu không hợp lệ.")
        return redirect("/profile?tab=access-requests")

    if request.method == "POST":
        profile_form = RoleProfileForm(request.POST, request.FILES, instance=role_profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
        return render(
            request,
            "profile.html",
            build_profile_context(request, profile_form, profile_type, active_tab="personal"),
            status=400,
        )

    profile_form = RoleProfileForm(instance=role_profile)
    return render(
        request,
        "profile.html",
        build_profile_context(request, profile_form, profile_type, active_tab=active_tab),
    )


def appointment_page(request):
    featured_specialties = [
        "Pulmonology",
        "Respiratory care",
        "Dermatology",
        "Obstetrics and gynecology",
        "Endocrinology",
        "Cardiology",
    ]
    featured_doctors = DoctorProfile.objects.select_related("account__user").order_by("full_name")[:4]
    context = {
        "featured_specialties": featured_specialties,
        "featured_doctors": featured_doctors,
    }
    context.update(build_header_context(request=request))
    return render(request, "appointment.html", context)


def doctor_search(request):
    specialty = (request.GET.get("specialty") or request.POST.get("specialty") or "").strip()
    keyword = specialty.lower().replace("-", " ")
    viewer_doctor = None
    if request.user.is_authenticated:
        viewer_doctor = DoctorProfile.objects.filter(account__user=request.user).first()

    if request.method == "POST" and request.POST.get("search_action") == "recommend_doctor" and viewer_doctor:
        recommended_doctor = DoctorProfile.objects.filter(pk=request.POST.get("doctor_id")).exclude(pk=viewer_doctor.pk).first()
        if recommended_doctor:
            viewer_doctor.recommended_doctors.add(recommended_doctor)
            messages.success(request, f"Đã thêm {recommended_doctor.display_name} vào danh sách bác sĩ được giới thiệu.")
        return redirect(f"/dat-kham/search?specialty={parse.quote(specialty)}")

    doctors = DoctorProfile.objects.select_related("account__user").order_by("full_name")

    if keyword:
        matched_doctors = doctors.filter(
            Q(full_name__icontains=keyword)
            | Q(account__user__email__icontains=keyword)
            | Q(specialties__icontains=keyword)
            | Q(position__icontains=keyword)
            | Q(workplace__icontains=keyword)
            | Q(introduction__icontains=keyword)
        )
    else:
        matched_doctors = doctors

    has_direct_match = matched_doctors.exists() or not specialty
    visible_doctors = list(matched_doctors if has_direct_match else doctors)
    recommended_ids = set(viewer_doctor.recommended_doctors.values_list("pk", flat=True)) if viewer_doctor else set()
    for doctor in visible_doctors:
        doctor.is_recommended_by_viewer = doctor.pk in recommended_ids
        doctor.is_viewer = bool(viewer_doctor and doctor.pk == viewer_doctor.pk)

    # Dãy nút thao tác trên mỗi kết quả bác sĩ
    doctor_result_actions = [
        # Nút thêm bác sĩ vào phần giới thiệu của tài khoản bác sĩ
        {"id": "recommend", "label": "Thêm vào giới thiệu", "type": "form", "class_name": "doctor-cta recommend", "doctor_only": True},
        # Nút xem hồ sơ dành cho tài khoản bác sĩ
        {"id": "view", "label": "Xem hồ sơ", "type": "link", "class_name": "doctor-cta secondary", "doctor_only": True},
        # Nút đặt khám dành cho bệnh nhân và khách
        {"id": "book", "label": "Book appointment", "type": "link", "class_name": "doctor-cta primary", "hide_for_doctor": True},
    ]
    context = {
        "specialty": specialty,
        "doctors": visible_doctors,
        "result_count": len(visible_doctors),
        "has_direct_match": has_direct_match,
        "viewer_doctor": viewer_doctor,
        "doctor_result_actions": doctor_result_actions,
    }
    context.update(build_header_context(request=request))

    return render(request, "doctor_search.html", context)


def build_public_booking_options(doctor, month_value=""):
    expire_overdue_appointment_payments()
    month_start = parse_schedule_month(month_value)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    previous_month = (month_start - timedelta(days=1)).replace(day=1)
    first_bookable_date = date.today()
    last_bookable_date = first_bookable_date + timedelta(days=90)
    busy_by_date = {}
    for busy_date, time_slot in doctor.busy_dates.filter(
        date__gte=first_bookable_date,
        date__lte=last_bookable_date,
    ).exclude(time_slot="").values_list("date", "time_slot"):
        busy_by_date.setdefault(busy_date.isoformat(), set()).add(time_slot)

    booked_by_date = {}
    for appointment_date, time_slot in doctor.appointments.filter(
        appointment_date__gte=first_bookable_date,
        appointment_date__lte=last_bookable_date,
    ).exclude(status=DoctorAppointment.STATUS_REJECTED).values_list("appointment_date", "time_slot"):
        booked_by_date.setdefault(appointment_date.isoformat(), set()).add(time_slot)

    time_groups = build_schedule_time_groups(doctor)
    all_slot_ids = {
        slot["id"]
        for group in time_groups
        for slot in group["slots"]
    }
    # Dãy nút chuyển tháng của lịch đặt khám công khai
    month_actions = [
        # Nút cuộn dải ngày sang phía trước
        {"id": "previous", "label": "‹", "direction": -1, "month": previous_month.strftime("%Y-%m"), "aria_label": "View previous dates"},
        # Nút cuộn dải ngày sang phía sau
        {"id": "next", "label": "›", "direction": 1, "month": next_month.strftime("%Y-%m"), "aria_label": "View next dates"},
    ]

    # Dãy nhãn thứ trong tuần của lịch đặt khám
    weekdays = [
        {"label": "Mon"},
        {"label": "Tue"},
        {"label": "Wed"},
        {"label": "Thu"},
        {"label": "Fri"},
        {"label": "Sat"},
        {"label": "Sun"},
    ]

    valid_dates = set()
    quick_dates = []
    for day_offset in range(91):
        booking_date = first_bookable_date + timedelta(days=day_offset)
        date_value = booking_date.isoformat()
        unavailable_slots = busy_by_date.get(date_value, set()) | booked_by_date.get(date_value, set())
        is_weekend_off = doctor.weekend_off and booking_date.weekday() >= 5
        if not is_weekend_off and len(unavailable_slots) < len(all_slot_ids):
            valid_dates.add(date_value)
            # Nút chọn ngày trong dải đặt khám nhanh 90 ngày
            quick_dates.append({
                "value": date_value,
                "unavailable_slots": "|".join(sorted(unavailable_slots)),
                "today": booking_date == date.today(),
                "weekday_label": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][booking_date.weekday()],
                "short_date": booking_date.strftime("%d-%m"),
            })

    weeks = []
    for week in calendar.monthcalendar(month_start.year, month_start.month):
        days = []
        for day_number in week:
            if not day_number:
                days.append({"empty": True})
                continue
            booking_date = month_start.replace(day=day_number)
            date_value = booking_date.isoformat()
            unavailable_slots = busy_by_date.get(date_value, set()) | booked_by_date.get(date_value, set())
            is_weekend_off = doctor.weekend_off and booking_date.weekday() >= 5
            selectable = (
                first_bookable_date <= booking_date <= last_bookable_date
                and not is_weekend_off
                and len(unavailable_slots) < len(all_slot_ids)
            )
            if selectable:
                valid_dates.add(date_value)
            # Nút chọn một ngày trong lịch đặt khám
            days.append({
                "empty": False,
                "day": day_number,
                "value": date_value,
                "unavailable_slots": "|".join(sorted(unavailable_slots)),
                "available_count": len(all_slot_ids - unavailable_slots),
                "selectable": selectable,
                "weekend_off": is_weekend_off,
                "today": booking_date == date.today(),
                "weekday_label": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][booking_date.weekday()],
                "short_date": booking_date.strftime("%d-%m"),
            })
        weeks.append(days)

    calendar_months = []
    calendar_month_cursor = first_bookable_date.replace(day=1)
    last_calendar_month = last_bookable_date.replace(day=1)
    while calendar_month_cursor <= last_calendar_month:
        calendar_weeks = []
        for week in calendar.monthcalendar(calendar_month_cursor.year, calendar_month_cursor.month):
            calendar_days = []
            for day_number in week:
                if not day_number:
                    calendar_days.append({"empty": True})
                    continue
                booking_date = calendar_month_cursor.replace(day=day_number)
                date_value = booking_date.isoformat()
                unavailable_slots = busy_by_date.get(date_value, set()) | booked_by_date.get(date_value, set())
                is_weekend_off = doctor.weekend_off and booking_date.weekday() >= 5
                is_in_booking_range = first_bookable_date <= booking_date <= last_bookable_date
                is_before_booking_range = booking_date < first_bookable_date
                selectable = (
                    is_in_booking_range
                    and not is_weekend_off
                    and len(unavailable_slots) < len(all_slot_ids)
                )
                calendar_days.append({
                    "empty": False,
                    "day": day_number,
                    "value": date_value,
                    "in_booking_range": is_in_booking_range,
                    "before_booking_range": is_before_booking_range,
                    "selectable": selectable,
                    "today": booking_date == date.today(),
                })
            calendar_weeks.append(calendar_days)
        calendar_months.append({
            "value": calendar_month_cursor.strftime("%Y-%m"),
            "label": calendar_month_cursor.strftime("%B %Y"),
            "weeks": calendar_weeks,
        })
        calendar_month_cursor = (
            calendar_month_cursor.replace(day=28) + timedelta(days=4)
        ).replace(day=1)

    return {
        "month_value": month_start.strftime("%Y-%m"),
        "month_label": f"Tháng {month_start.month}, {month_start.year}",
        "month_actions": month_actions,
        "weekdays": weekdays,
        "weeks": weeks,
        "quick_dates": quick_dates,
        "calendar_months": calendar_months,
        "first_bookable_date": first_bookable_date.isoformat(),
        "last_bookable_date": last_bookable_date.isoformat(),
        "time_groups": time_groups,
        "valid_slots": all_slot_ids,
        "valid_dates": valid_dates,
        # Dãy nút thao tác sau khi người dùng mở danh sách ca
        "shift_actions": [
            # Nút đóng modal nhập lý do khám
            {"id": "close-modal", "label": "Close", "icon": "×", "type": "button", "class_name": "booking-request-modal-close", "patient_only": True},
            # Nút gửi yêu cầu đặt khám của bệnh nhân
            {"id": "submit", "label": "Send appointment request", "type": "submit", "class_name": "btn doctor-booking-submit", "patient_only": True},
        ],
    }


def doctor_profile_detail(request, doctor_id):
    doctor = get_object_or_404(
        DoctorProfile.objects.select_related("account__user"),
        pk=doctor_id,
    )
    patient_profile = None
    if request.user.is_authenticated:
        patient_profile = PatientProfile.objects.filter(account__user=request.user).first()
    viewer_is_member = bool(patient_profile and patient_profile.is_member)
    video_consultation_price = calculate_patient_consultation_fee(
        doctor.video_consultation_fee,
        viewer_is_member,
    )
    message_consultation_price = calculate_patient_consultation_fee(
        doctor.message_consultation_fee,
        viewer_is_member,
    )

    # Dãy nút chọn số sao khi bệnh nhân đánh giá bác sĩ
    review_rating_options = [
        # Nút đánh giá 1 sao
        {"value": 1, "label": "1 star"},
        # Nút đánh giá 2 sao
        {"value": 2, "label": "2 stars"},
        # Nút đánh giá 3 sao
        {"value": 3, "label": "3 stars"},
        # Nút đánh giá 4 sao
        {"value": 4, "label": "4 stars"},
        # Nút đánh giá 5 sao
        {"value": 5, "label": "5 stars"},
    ]

    current_review = (
        DoctorReview.objects.filter(doctor=doctor, patient=patient_profile).first()
        if patient_profile
        else None
    )
    review_errors = []
    booking_errors = []
    # Dãy thẻ loại dịch vụ và mức phí tư vấn của bác sĩ
    consultation_services = [
        # Thẻ dịch vụ khám qua video
        {
            "id": DoctorAppointment.SERVICE_VIDEO,
            "label": "Video consultation",
            "fee": video_consultation_price,
            "currency": "$",
            "unit": "/visit",
            "selected": request.POST.get("service_type") == DoctorAppointment.SERVICE_VIDEO,
        },
        # Thẻ dịch vụ khám qua tin nhắn
        {
            "id": DoctorAppointment.SERVICE_MESSAGE,
            "label": "Message consultation",
            "fee": message_consultation_price,
            "currency": "$",
            "unit": "/visit",
            "selected": request.POST.get("service_type") == DoctorAppointment.SERVICE_MESSAGE,
        },
    ]
    selected_booking_month = request.POST.get("booking_month") or request.GET.get("month", "")
    booking_options = build_public_booking_options(doctor, selected_booking_month)

    if request.method == "POST" and request.POST.get("profile_action") == "book_appointment":
        if not patient_profile:
            booking_errors.append("Only signed-in patient accounts can book appointments.")
        else:
            selected_date_value = request.POST.get("appointment_date", "")
            selected_time_slot = request.POST.get("time_slot", "")
            selected_service_type = request.POST.get("service_type", "")
            reason = request.POST.get("reason", "").strip()
            attachments = request.FILES.getlist("attachments")
            allowed_media_types = {
                "image/jpeg": AppointmentAttachment.MEDIA_IMAGE,
                "image/png": AppointmentAttachment.MEDIA_IMAGE,
                "image/webp": AppointmentAttachment.MEDIA_IMAGE,
                "image/gif": AppointmentAttachment.MEDIA_IMAGE,
                "video/mp4": AppointmentAttachment.MEDIA_VIDEO,
                "video/webm": AppointmentAttachment.MEDIA_VIDEO,
                "video/quicktime": AppointmentAttachment.MEDIA_VIDEO,
            }
            allowed_extensions = {
                ".jpg": AppointmentAttachment.MEDIA_IMAGE,
                ".jpeg": AppointmentAttachment.MEDIA_IMAGE,
                ".png": AppointmentAttachment.MEDIA_IMAGE,
                ".webp": AppointmentAttachment.MEDIA_IMAGE,
                ".gif": AppointmentAttachment.MEDIA_IMAGE,
                ".mp4": AppointmentAttachment.MEDIA_VIDEO,
                ".webm": AppointmentAttachment.MEDIA_VIDEO,
                ".mov": AppointmentAttachment.MEDIA_VIDEO,
            }
            if selected_date_value not in booking_options["valid_dates"]:
                booking_errors.append("Please choose a valid appointment date.")
            if selected_time_slot not in booking_options["valid_slots"]:
                booking_errors.append("Please choose a valid appointment time.")
            service_fees = {
                DoctorAppointment.SERVICE_VIDEO: video_consultation_price,
                DoctorAppointment.SERVICE_MESSAGE: message_consultation_price,
            }
            selected_consultation_fee = service_fees.get(selected_service_type)
            if selected_service_type not in service_fees:
                booking_errors.append("Please choose a consultation service.")
            elif selected_consultation_fee is None:
                booking_errors.append("The selected consultation service is not currently available.")
            if len(attachments) > 5:
                booking_errors.append("You can attach up to 5 photos or videos.")
            for attachment in attachments:
                extension = Path(attachment.name).suffix.lower()
                media_type_matches = (
                    attachment.content_type in allowed_media_types
                    and extension in allowed_extensions
                    and allowed_media_types.get(attachment.content_type) == allowed_extensions.get(extension)
                )
                if not media_type_matches:
                    booking_errors.append(f"{attachment.name} is not a supported photo or video format.")
                elif allowed_media_types[attachment.content_type] == AppointmentAttachment.MEDIA_VIDEO:
                    video_duration = get_uploaded_video_duration(attachment)
                    if video_duration is None:
                        booking_errors.append(f"The duration of {attachment.name} could not be verified. Please use a valid MP4, MOV, or WebM video.")
                    elif video_duration > 30:
                        booking_errors.append(f"{attachment.name} is longer than the 30-second video limit.")
                if (
                    attachment.content_type not in allowed_media_types
                    or extension not in allowed_extensions
                    or allowed_media_types.get(attachment.content_type) != allowed_extensions.get(extension)
                ):
                    continue
                if attachment.size > 50 * 1024 * 1024:
                    booking_errors.append(f"{attachment.name} exceeds the 50 MB file limit.")
            if sum(attachment.size for attachment in attachments) > 150 * 1024 * 1024:
                booking_errors.append("The total attachment size cannot exceed 150 MB.")

            if not booking_errors:
                selected_date = datetime.strptime(selected_date_value, "%Y-%m-%d").date()
                is_busy = doctor.busy_dates.filter(date=selected_date, time_slot=selected_time_slot).exists()
                is_booked = doctor.appointments.filter(
                    appointment_date=selected_date,
                    time_slot=selected_time_slot,
                ).exclude(status=DoctorAppointment.STATUS_REJECTED).exists()
                if is_busy or is_booked:
                    booking_errors.append("This time was just booked or marked unavailable. Please choose another time.")
                else:
                    try:
                        with transaction.atomic():
                            appointment = DoctorAppointment.objects.create(
                                patient=patient_profile,
                                doctor=doctor,
                                appointment_date=selected_date,
                                time_slot=selected_time_slot,
                                service_type=selected_service_type,
                                consultation_fee=selected_consultation_fee,
                                reason=reason,
                            )
                            for attachment in attachments:
                                AppointmentAttachment.objects.create(
                                    appointment=appointment,
                                    file=attachment,
                                    media_type=allowed_media_types[attachment.content_type],
                                    original_name=attachment.name[:255],
                                )
                    except IntegrityError:
                        booking_errors.append("This time was just booked by another patient. Please choose another time.")
                    else:
                        messages.success(request, "Your appointment request was submitted for admin review.")
                        return redirect("doctor_profile_detail", doctor_id=doctor.pk)

    if request.method == "POST" and request.POST.get("profile_action") == "review":
        if not patient_profile:
            review_errors.append("Only signed-in patient accounts can review doctors.")
        else:
            try:
                rating = int(request.POST.get("rating", ""))
            except (TypeError, ValueError):
                rating = 0
            comment = request.POST.get("comment", "").strip()
            if rating not in {option["value"] for option in review_rating_options}:
                review_errors.append("Please choose a rating from 1 to 5 stars.")
            if len(comment) > 2000:
                review_errors.append("The review cannot exceed 2,000 characters.")

            if not review_errors:
                DoctorReview.objects.update_or_create(
                    doctor=doctor,
                    patient=patient_profile,
                    defaults={"rating": rating, "comment": comment},
                )
                messages.success(request, "Đánh giá của bạn đã được lưu.")
                return redirect("doctor_profile_detail", doctor_id=doctor.pk)

    reviews = doctor.reviews.select_related("patient__account__user")
    review_summary = reviews.aggregate(average=Avg("rating"))
    context = {
        "doctor": doctor,
        "consultation_services": consultation_services,
        "visit_count": doctor.appointments.filter(status=DoctorAppointment.STATUS_ACCEPTED).count(),
        "reviews": reviews,
        "review_count": reviews.count(),
        "average_rating": round(review_summary["average"] or 0, 1),
        "review_rating_options": review_rating_options,
        "current_review": current_review,
        "review_errors": review_errors,
        "can_review": patient_profile is not None,
        "booking_options": booking_options,
        "booking_errors": booking_errors,
        "can_book": patient_profile is not None,
        "viewer_is_member": viewer_is_member,
        "consultation_price_note": (
            "Member price: the doctor's base fee is multiplied by 1.5."
            if viewer_is_member
            else "Standard price: the doctor's base fee is multiplied by 2.05."
        ),
        "recommended_doctors": doctor.recommended_doctors.select_related("account__user").order_by("full_name"),
    }
    context.update(build_header_context(request=request))
    return render(
        request,
        "doctor_profile_detail.html",
        context,
        status=400 if review_errors or booking_errors else 200,
    )
