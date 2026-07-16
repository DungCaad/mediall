from django.contrib import admin

from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_type", "specialties", "address", "is_active")
    list_filter = ("provider_type", "is_active", "cta_style")
    search_fields = ("name", "specialties", "address", "search_terms")
