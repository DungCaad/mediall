from django.contrib import admin

from .models import AccountProfile, DoctorAppointment, DoctorBusyDate, DoctorProfile, DoctorReview, MedicalRecord, PatientProfile


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "phone")


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("account", "full_name", "birth_year", "updated_at")
    search_fields = ("account__user__username", "full_name")


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


@admin.register(DoctorAppointment)
class DoctorAppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "appointment_date", "time_slot", "status", "payment_status", "referred_doctor")
    list_filter = ("status", "payment_status", "appointment_date")
    search_fields = (
        "patient__full_name",
        "patient__account__user__email",
        "doctor__full_name",
        "doctor__account__user__email",
    )


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
