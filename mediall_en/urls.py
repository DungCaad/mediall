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
    path("admin/creat", views.admin_create_post, name="admin_create_post"),
    path("admin/posts", views.admin_posts, name="admin_posts"),
    path("admin/orders", views.admin_orders, name="admin_orders"),
    path("admin/orders/<int:appointment_id>", views.admin_order_detail, name="admin_order_detail"),
    path("appointments/<int:appointment_id>/payment", views.submit_appointment_payment, name="submit_appointment_payment"),
    path("admin/profiles/doctor/", views.admin_profiles, {"profile_type": "doctor"}, name="admin_doctor_profiles"),
    path("admin/profiles/doctor/<int:profile_id>", views.admin_profile_detail, {"profile_type": "doctor"}, name="admin_doctor_profile_detail"),
    path("admin/profiles/users/", views.admin_profiles, {"profile_type": "users"}, name="admin_user_profiles"),
    path("admin/profiles/users/<int:profile_id>", views.admin_profile_detail, {"profile_type": "users"}, name="admin_user_profile_detail"),
    path("admin/profiles/<int:account_id>", views.admin_profile_detail, name="admin_profile_detail"),
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
    path("appointment-attachments/<int:attachment_id>", views.appointment_attachment_file, name="appointment_attachment"),
    path("post/<int:post_id>", views.post_detail, name="post_detail"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
