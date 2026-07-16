from django.contrib import admin

from .models import AccountProfile


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "role", "clinic_address", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "phone", "clinic_address")
