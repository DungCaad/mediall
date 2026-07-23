from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
import re
from pathlib import Path
from uuid import uuid4


def appointment_attachment_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()[:10]
    return f"appointments/attachments/{uuid4().hex}{suffix}"


class AccountProfile(models.Model):
    ROLE_PATIENT = "patient"
    ROLE_DOCTOR = "doctor"
    ROLE_CHOICES = [
        (ROLE_PATIENT, "Patient"),
        (ROLE_DOCTOR, "Doctor"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField("Phone number", max_length=20, unique=True)
    role = models.CharField("Account role", max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class BaseRoleProfile(models.Model):
    full_name = models.CharField("Full name", max_length=150, blank=True)
    birth_year = models.PositiveSmallIntegerField("Birth year", blank=True, null=True)
    country = models.CharField("Country", max_length=100, blank=True)
    avatar = models.ImageField("Avatar", upload_to="profiles/avatars/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PatientProfile(BaseRoleProfile):
    account = models.OneToOneField(AccountProfile, on_delete=models.CASCADE, related_name="patient_details")
    address = models.CharField("Home address", max_length=255, blank=True)
    is_member = models.BooleanField("Member", default=False, editable=False)

    def __str__(self):
        return f"Patient profile: {self.account.user.username}"


class PatientProfileAccessRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="profile_access_requests",
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile_access_requests",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "requester"],
                name="unique_patient_profile_access_request",
            ),
        ]

    def __str__(self):
        return f"{self.requester} requests access to {self.patient}"


class DoctorProfile(BaseRoleProfile):
    WORK_SCHEDULE_OFFICE = "office"
    WORK_SCHEDULE_NIGHT = "night"
    WORK_SCHEDULE_CUSTOM = "custom"
    WORK_SCHEDULE_CHOICES = [
        (WORK_SCHEDULE_OFFICE, "Giờ hành chính"),
        (WORK_SCHEDULE_NIGHT, "Ca đêm"),
        (WORK_SCHEDULE_CUSTOM, "Tùy chỉnh"),
    ]

    account = models.OneToOneField(AccountProfile, on_delete=models.CASCADE, related_name="doctor_details")
    is_verified = models.BooleanField("Verified doctor", default=False, editable=False)
    specialties = models.CharField("Specialties", max_length=255, blank=True)
    position = models.CharField("Position", max_length=150, blank=True)
    workplace = models.CharField("Workplace", max_length=255, blank=True)
    introduction = models.TextField("Introduction", blank=True)
    training_history = models.TextField("Training history", blank=True)
    years_experience = models.PositiveSmallIntegerField("Years of experience", blank=True, null=True)
    video_consultation_fee = models.DecimalField(
        "Video consultation fee ($/visit)",
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    message_consultation_fee = models.DecimalField(
        "Message consultation fee ($/visit)",
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    work_schedule_type = models.CharField(max_length=20, choices=WORK_SCHEDULE_CHOICES, default=WORK_SCHEDULE_OFFICE)
    custom_work_start = models.TimeField("Giờ bắt đầu tùy chỉnh", blank=True, null=True)
    custom_work_end = models.TimeField("Giờ kết thúc tùy chỉnh", blank=True, null=True)
    weekend_off = models.BooleanField("Nghỉ Thứ 7 và Chủ nhật", default=False)
    recommended_doctors = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="recommended_by_doctors",
        blank=True,
    )

    def __str__(self):
        return f"Doctor profile: {self.account.user.username}"

    @property
    def display_name(self):
        return self.full_name or self.account.user.email or self.account.user.username

    @property
    def specialty_list(self):
        return [item.strip() for item in re.split(r"[|,]", self.specialties) if item.strip()]

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else ""


class DoctorBusyDate(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="busy_dates")
    date = models.DateField("Busy date")
    time_slot = models.CharField("Busy time slot", max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time_slot"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "time_slot"],
                name="unique_doctor_busy_time_slot",
            ),
        ]

    def __str__(self):
        return f"{self.doctor.account.user.username}: {self.date} {self.time_slot}"


class DoctorAppointment(models.Model):
    SERVICE_VIDEO = "video"
    SERVICE_MESSAGE = "message"
    SERVICE_TYPE_CHOICES = [
        (SERVICE_VIDEO, "Video consultation"),
        (SERVICE_MESSAGE, "Message consultation"),
    ]
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Chờ xác nhận"),
        (STATUS_ACCEPTED, "Đã chấp nhận"),
        (STATUS_REJECTED, "Đã từ chối"),
    ]
    PAYMENT_AWAITING = "awaiting"
    PAYMENT_PAID = "paid"
    PAYMENT_EXPIRED = "expired"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_AWAITING, "Chờ thanh toán"),
        (PAYMENT_PAID, "Đã thanh toán"),
        (PAYMENT_EXPIRED, "Payment expired"),
    ]
    MODERATION_PENDING = "pending"
    MODERATION_APPROVED = "approved"
    MODERATION_REJECTED = "rejected"
    MODERATION_STATUS_CHOICES = [
        (MODERATION_PENDING, "Pending admin review"),
        (MODERATION_APPROVED, "Approved by admin"),
        (MODERATION_REJECTED, "Rejected by admin"),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="appointments")
    appointment_date = models.DateField("Appointment date")
    time_slot = models.CharField("Appointment time slot", max_length=20)
    service_type = models.CharField("Consultation service", max_length=20, choices=SERVICE_TYPE_CHOICES, blank=True, default="")
    consultation_fee = models.DecimalField(
        "Consultation fee ($/visit)",
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        editable=False,
        validators=[MinValueValidator(0)],
    )
    reason = models.TextField("Reason for visit", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_AWAITING,
    )
    payment_due_at = models.DateTimeField("Payment deadline", blank=True, null=True, editable=False)
    payment_submitted_at = models.DateTimeField("Payment submitted at", blank=True, null=True, editable=False)
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default=MODERATION_PENDING,
    )
    referred_doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.SET_NULL,
        related_name="received_referrals",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["appointment_date", "time_slot"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "appointment_date", "time_slot"],
                condition=~models.Q(status="rejected"),
                name="unique_doctor_appointment_time_slot",
            ),
        ]

    def __str__(self):
        return f"{self.patient.account.user.username} → {self.doctor.account.user.username}: {self.appointment_date} {self.time_slot}"


class AppointmentAttachment(models.Model):
    MEDIA_IMAGE = "image"
    MEDIA_VIDEO = "video"
    MEDIA_TYPE_CHOICES = [
        (MEDIA_IMAGE, "Image"),
        (MEDIA_VIDEO, "Video"),
    ]

    appointment = models.ForeignKey(
        DoctorAppointment,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField("Attachment", upload_to=appointment_attachment_upload_to)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return self.original_name


class MedicalRecord(models.Model):
    appointment = models.OneToOneField(
        DoctorAppointment,
        on_delete=models.CASCADE,
        related_name="medical_record",
    )
    diagnosis = models.TextField("Diagnosis")
    treatment = models.TextField("Treatment", blank=True)
    prescription = models.TextField("Prescription", blank=True)
    notes = models.TextField("Doctor's notes", blank=True)
    follow_up_date = models.DateField("Follow-up date", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment__appointment_date", "-updated_at"]

    def __str__(self):
        return f"Medical record #{self.pk} - {self.appointment.patient.account.user.email}"


class DoctorReview(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="doctor_reviews")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField("Rating")
    comment = models.TextField("Comment", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["patient", "doctor"], name="unique_patient_doctor_review"),
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name="doctor_review_rating_1_to_5"),
        ]

    def __str__(self):
        return f"{self.patient.account.user.username} → {self.doctor.account.user.username}: {self.rating}/5"


class FeaturedPostGroup(models.Model):
    name = models.CharField("Group name", max_length=100, unique=True)
    position = models.PositiveIntegerField("Position", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField("Title", max_length=200)
    content_html = models.TextField("Content")
    seo_description = models.CharField("SEO description", max_length=160, blank=True)
    tags = models.CharField("Tags", max_length=500, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="blog_posts",
        blank=True,
        null=True,
    )
    is_published = models.BooleanField("Published", default=True)
    is_featured = models.BooleanField("Featured in footer", default=False)
    featured_group = models.ForeignKey(
        FeaturedPostGroup,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
    )
    view_count = models.PositiveIntegerField("View count", default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
