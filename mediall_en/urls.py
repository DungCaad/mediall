"""
URL configuration for mediall_en project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home_page, name="home"),
    path("dat-kham/", views.appointment_page, name="appointment"),
    path("dat-kham/search", views.doctor_search, name="doctor_search"),
    path("bac-si/<int:doctor_id>/", views.doctor_profile_detail, name="doctor_profile_detail"),
    path("accounts/register", views.register_account, name="register_account"),
    path("accounts/login", views.login_account, name="login_account"),
    path("accounts/logout", views.logout_account, name="logout_account"),
    path("profile", views.profile_page, name="profile"),
    path("medical-records", views.medical_records_page, name="medical_records"),
    path("translate/english", views.translate_to_english, name="translate_to_english"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
