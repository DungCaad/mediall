from django.db import models


class Doctor(models.Model):
    PROVIDER_TYPES = [
        ("doctor", "Doctor"),
        ("clinic", "Clinic"),
    ]

    CTA_STYLES = [
        ("primary", "Primary"),
        ("success", "Success"),
    ]

    name = models.CharField(max_length=160)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES, default="doctor")
    avatar = models.CharField(max_length=255, blank=True)
    specialties = models.CharField(max_length=255, help_text="Separate specialties with |")
    address = models.CharField(max_length=255, blank=True)
    cta = models.CharField(max_length=40, default="Dat kham")
    cta_style = models.CharField(max_length=20, choices=CTA_STYLES, default="primary")
    search_terms = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def specialty_list(self):
        return [item.strip() for item in self.specialties.split("|") if item.strip()]
