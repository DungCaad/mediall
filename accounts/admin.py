from datetime import timedelta

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import AccountProfile, AppointmentAttachment, DoctorAppointment, DoctorBusyDate, DoctorProfile, DoctorReview, MedicalRecord, PatientProfile, PatientProfileAccessRequest


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "phone")


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("account", "full_name", "is_member", "birth_year", "updated_at")
    list_filter = ("is_member",)
    search_fields = ("account__user__username", "full_name")


@admin.register(PatientProfileAccessRequest)
class PatientProfileAccessRequestAdmin(admin.ModelAdmin):
    list_display = ("patient", "requester", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("patient__full_name", "patient__account__user__email", "requester__email")


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ("account", "full_name", "is_verified", "work_schedule_type", "workplace", "updated_at")
    list_filter = ("is_verified", "work_schedule_type")
    search_fields = ("account__user__username", "full_name", "workplace", "specialties")


@admin.register(DoctorBusyDate)
class DoctorBusyDateAdmin(admin.ModelAdmin):
    list_display = ("doctor", "date", "time_slot", "created_at")
    list_filter = ("date",)
    search_fields = ("doctor__account__user__username", "doctor__full_name")


class AppointmentAttachmentInline(admin.TabularInline):
    model = AppointmentAttachment
    extra = 0
    readonly_fields = ("media_type", "original_name", "uploaded_at")


@admin.register(DoctorAppointment)
class DoctorAppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "appointment_date", "time_slot", "service_type", "consultation_fee", "moderation_badge", "appointment_badge", "payment_badge", "referred_doctor")
    list_filter = ("moderation_status", "status", "payment_status", "appointment_date")
    search_fields = (
        "patient__full_name",
        "patient__account__user__email",
        "doctor__full_name",
        "doctor__account__user__email",
    )
    inlines = (AppointmentAttachmentInline,)
    actions = ("approve_for_doctor", "reject_during_review")
    date_hierarchy = "appointment_date"
    list_per_page = 25
    list_select_related = ("patient__account__user", "doctor__account__user", "referred_doctor")

    @admin.display(description="Admin review", ordering="moderation_status")
    def moderation_badge(self, obj):
        badge_classes = {
            DoctorAppointment.MODERATION_PENDING: "status-badge status-pending",
            DoctorAppointment.MODERATION_APPROVED: "status-badge status-approved",
            DoctorAppointment.MODERATION_REJECTED: "status-badge status-rejected",
        }
        return format_html(
            '<span class="{}">{}</span>',
            badge_classes.get(obj.moderation_status, "status-badge"),
            obj.get_moderation_status_display(),
        )

    @admin.display(description="Doctor response", ordering="status")
    def appointment_badge(self, obj):
        badge_classes = {
            DoctorAppointment.STATUS_PENDING: "status-badge status-pending",
            DoctorAppointment.STATUS_ACCEPTED: "status-badge status-approved",
            DoctorAppointment.STATUS_REJECTED: "status-badge status-rejected",
        }
        return format_html(
            '<span class="{}">{}</span>',
            badge_classes.get(obj.status, "status-badge"),
            obj.get_status_display(),
        )

    @admin.display(description="Payment", ordering="payment_status")
    def payment_badge(self, obj):
        if obj.payment_status == DoctorAppointment.PAYMENT_PAID:
            class_name = "status-badge status-paid"
        elif obj.payment_status == DoctorAppointment.PAYMENT_EXPIRED:
            class_name = "status-badge status-rejected"
        else:
            class_name = "status-badge status-neutral"
        return format_html('<span class="{}">{}</span>', class_name, obj.get_payment_status_display())

    def save_model(self, request, obj, form, change):
        if obj.moderation_status == DoctorAppointment.MODERATION_REJECTED:
            obj.status = DoctorAppointment.STATUS_REJECTED
        elif (
            obj.moderation_status == DoctorAppointment.MODERATION_APPROVED
            and obj.payment_status == DoctorAppointment.PAYMENT_AWAITING
            and obj.payment_due_at is None
        ):
            obj.payment_due_at = timezone.now() + timedelta(hours=24)
        super().save_model(request, obj, form, change)

    @admin.action(description="Approve selected requests and send them to doctors")
    def approve_for_doctor(self, request, queryset):
        updated = queryset.filter(
            moderation_status=DoctorAppointment.MODERATION_PENDING,
        ).update(
            moderation_status=DoctorAppointment.MODERATION_APPROVED,
            payment_due_at=timezone.now() + timedelta(hours=24),
        )
        self.message_user(request, f"{updated} appointment request(s) sent to doctors.")

    @admin.action(description="Reject selected requests during admin review")
    def reject_during_review(self, request, queryset):
        updated = queryset.filter(
            moderation_status=DoctorAppointment.MODERATION_PENDING,
        ).update(
            moderation_status=DoctorAppointment.MODERATION_REJECTED,
            status=DoctorAppointment.STATUS_REJECTED,
        )
        self.message_user(request, f"{updated} appointment request(s) rejected.")


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("appointment", "diagnosis", "follow_up_date", "updated_at")
    search_fields = (
        "appointment__patient__full_name",
        "appointment__patient__account__user__email",
        "appointment__doctor__full_name",
        "diagnosis",
    )
    list_filter = ("follow_up_date", "updated_at")


@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "rating", "updated_at")
    list_filter = ("rating",)
    search_fields = ("patient__full_name", "doctor__full_name", "comment")


admin.site.site_header = "Mediall Administration"
admin.site.site_title = "Mediall Admin"
admin.site.index_title = "Healthcare management dashboard"
