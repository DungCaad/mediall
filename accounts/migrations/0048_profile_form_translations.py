from django.db import migrations


TRANSLATIONS = {
    "Full name": "Họ và tên",
    "Birth year": "Năm sinh",
    "Avatar": "Ảnh đại diện",
    "Home address": "Địa chỉ nhà",
    "Specialties": "Chuyên khoa",
    "Position": "Chức vụ",
    "Workplace": "Nơi làm việc",
    "Video consultation fee ($/visit)": "Phí tư vấn qua video ($/lượt khám)",
    "Message consultation fee ($/visit)": "Phí tư vấn qua tin nhắn ($/lượt khám)",
    "Current password": "Mật khẩu hiện tại",
    "New password": "Mật khẩu mới",
    "Confirm new password": "Xác nhận mật khẩu mới",
    "Save changes": "Lưu thay đổi",
    "Cancel": "Hủy",
    "Email": "Email",
    "Phone number": "Số điện thoại",
    "Account type": "Loại tài khoản",
    "Specialty not provided": "Chưa cung cấp chuyên khoa",
    "Revoke access": "Thu hồi quyền truy cập",
    "Pending": "Đang chờ",
    "Approved": "Đã chấp thuận",
    "Rejected": "Đã từ chối",
    "Confirm payment": "Xác nhận thanh toán",
    "Your password was updated.": "Mật khẩu của bạn đã được cập nhật.",
    "The current password is incorrect.": "Mật khẩu hiện tại không đúng.",
    "The new password and confirmation do not match.": "Mật khẩu mới và phần xác nhận không khớp.",
    "The new password must be at least 6 characters.": "Mật khẩu mới phải có ít nhất 6 ký tự.",
    "This account can now view your profile.": "Tài khoản này hiện có thể xem hồ sơ của bạn.",
    "The profile access request was rejected.": "Yêu cầu truy cập hồ sơ đã bị từ chối.",
    "Profile access was revoked.": "Quyền truy cập hồ sơ đã được thu hồi.",
}


def add_translations(apps, schema_editor):
    UiTranslation = apps.get_model("accounts", "UiTranslation")
    for source_text, vietnamese_text in TRANSLATIONS.items():
        UiTranslation.objects.update_or_create(
            source_text=source_text,
            defaults={"vietnamese_text": vietnamese_text},
        )


def remove_translations(apps, schema_editor):
    UiTranslation = apps.get_model("accounts", "UiTranslation")
    UiTranslation.objects.filter(source_text__in=TRANSLATIONS).delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0047_profile_chat_translations")]

    operations = [migrations.RunPython(add_translations, remove_translations)]
