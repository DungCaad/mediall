from django.conf import settings
from django.db import models


class AccountProfile(models.Model):
    ROLE_PATIENT = "patient"
    ROLE_DOCTOR = "doctor"
    ROLE_CHOICES = [
        (ROLE_PATIENT, "Patient"),
        (ROLE_DOCTOR, "Doctor"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    photo = models.URLField(blank=True)
    clinic_address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
