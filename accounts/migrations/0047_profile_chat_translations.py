from django.db import migrations


TRANSLATIONS = {
    "Profile sections": "Các mục hồ sơ",
    "Choose an avatar": "Chọn ảnh đại diện",
    "Change": "Thay đổi",
    "Diagnoses, treatments, prescriptions, and follow-up appointments from previous visits.": "Chẩn đoán, điều trị, đơn thuốc và lịch tái khám từ các lần khám trước.",
    "The medical record for this appointment has not been added yet.": "Hồ sơ bệnh án của lịch hẹn này chưa được bổ sung.",
    "Track admin review and doctor responses for each consultation request.": "Theo dõi trạng thái duyệt của quản trị viên và phản hồi của bác sĩ cho từng yêu cầu tư vấn.",
    "Request #": "Yêu cầu #",
    "Admin review": "Quản trị viên duyệt",
    "Approved by admin": "Đã được quản trị viên duyệt",
    "Rejected by admin": "Bị quản trị viên từ chối",
    "Pending admin review": "Đang chờ quản trị viên duyệt",
    "Doctor approval": "Bác sĩ duyệt",
    "Not sent to doctor": "Chưa gửi đến bác sĩ",
    "Waiting for admin review": "Đang chờ quản trị viên duyệt",
    "Accepted by doctor": "Đã được bác sĩ chấp nhận",
    "Rejected by doctor": "Bị bác sĩ từ chối",
    "Waiting for doctor": "Đang chờ bác sĩ",
    "Payment expired": "Thanh toán đã hết hạn",
    "The 24-hour deadline passed and this appointment is no longer held.": "Đã quá thời hạn 24 giờ và lịch hẹn này không còn được giữ.",
    "Paid": "Đã thanh toán",
    "Pay before": "Thanh toán trước",
    "The appointment is held for 24 hours after admin verification.": "Lịch hẹn được giữ trong 24 giờ sau khi quản trị viên xác minh.",
    "Awaiting confirmation": "Đang chờ xác nhận",
    "Pay now": "Thanh toán ngay",
    "Consultation payment": "Thanh toán phí tư vấn",
    "SECURE PAYMENT": "THANH TOÁN AN TOÀN",
    "Cardholder name": "Tên chủ thẻ",
    "Card number": "Số thẻ",
    "Expiry date": "Ngày hết hạn",
    "Card details are used only for this interface simulation and are not stored.": "Thông tin thẻ chỉ được dùng để mô phỏng giao diện và không được lưu trữ.",
    "Only people you approve can view your personal profile information.": "Chỉ những người bạn chấp thuận mới có thể xem thông tin hồ sơ cá nhân.",
    "Requested": "Đã yêu cầu",
    "No one has requested access to your profile.": "Chưa có ai yêu cầu truy cập hồ sơ của bạn.",
    "Approve": "Chấp thuận",
    "Reject": "Từ chối",
    "Country": "Quốc gia",
    "Member": "Thành viên",
    "Patient": "Bệnh nhân",
    "Doctor": "Bác sĩ",
    "Back to chat": "Quay lại trò chuyện",
    "Chat | Mediall": "Trò chuyện | Mediall",
    "Back to Mediall home": "Quay lại trang chủ Mediall",
    "Options": "Tùy chọn",
    "New conversation": "Cuộc trò chuyện mới",
    "Conversation filters": "Bộ lọc cuộc trò chuyện",
    "Start a conversation": "Bắt đầu cuộc trò chuyện",
    "Back to conversation list": "Quay lại danh sách trò chuyện",
    "Active now": "Đang hoạt động",
    "Loading messages…": "Đang tải tin nhắn…",
    "Load older messages": "Tải tin nhắn cũ hơn",
    "New messages ↓": "Tin nhắn mới ↓",
    "Message": "Tin nhắn",
    "Add attachment": "Thêm tệp đính kèm",
    "Document": "Tài liệu",
    "Photos & videos": "Ảnh và video",
    "Send message": "Gửi tin nhắn",
    "Your messages": "Tin nhắn của bạn",
    "Select a conversation or start a new one.": "Chọn một cuộc trò chuyện hoặc bắt đầu cuộc trò chuyện mới.",
    "New message": "Tin nhắn mới",
    "To:": "Đến:",
    "Enter a member name": "Nhập tên thành viên",
    "No members available.": "Không có thành viên khả dụng.",
    " · Sent": " · Đã gửi",
    " · Failed to send": " · Gửi thất bại",
    "Check the message and try again.": "Kiểm tra tin nhắn và thử lại.",
    "Close": "Đóng",
    "Service not selected": "Chưa chọn dịch vụ",
    "requests": "yêu cầu",
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
    dependencies = [("accounts", "0046_condition_topic_translations")]

    operations = [migrations.RunPython(add_translations, remove_translations)]
