from django.db import migrations


TRANSLATIONS = {
    "Condition": "Chủ đề sức khỏe",
    "Condition categories": "Danh mục chủ đề sức khỏe",
    "Step 1": "Bước 1",
    "Step 2": "Bước 2",
    "Step 3": "Bước 3",
    "Featured posts": "Bài viết nổi bật",
    "Tools & Info": "Công cụ & Thông tin",
    "Mediall for healthcare professionals": "Mediall dành cho chuyên gia y tế",
    "How Mediall works": "Mediall hoạt động như thế nào",
    "Pharmacies near you": "Nhà thuốc gần bạn",
    "Health": "Sức khỏe",
    "Health questions and answers": "Hỏi đáp sức khỏe",
    "Seasonal flu": "Cúm mùa",
    "Covid-19": "COVID-19",
    "UTI": "Nhiễm trùng đường tiết niệu",
    "Allergies": "Dị ứng",
    "Newsletters": "Bản tin",
    "Latest health news": "Tin sức khỏe mới nhất",
    "Support": "Hỗ trợ",
    "Help & FAQs": "Trợ giúp & Câu hỏi thường gặp",
    "Company": "Công ty",
    "Jobs": "Việc làm",
    "Mediall Helps": "Mediall đồng hành",
    "Legal": "Pháp lý",
    "Your Privacy Choices": "Lựa chọn quyền riêng tư của bạn",
    "Consumer Health Data Privacy Notice": "Thông báo quyền riêng tư dữ liệu sức khỏe người dùng",
    "Collection Notice": "Thông báo thu thập dữ liệu",
    "Site Disclaimer": "Tuyên bố miễn trừ trách nhiệm của trang",
    "Terms of Use": "Điều khoản sử dụng",
    "Privacy Center": "Trung tâm quyền riêng tư",
    "Privacy Policy": "Chính sách quyền riêng tư",
    "Cookie Preferences": "Tùy chọn cookie",
    "Corporate news": "Tin tức doanh nghiệp",
    "Investors": "Nhà đầu tư",
    "Research": "Nghiên cứu",
    "Press": "Báo chí",
    "About Mediall": "Giới thiệu Mediall",
    "Accessibility": "Khả năng tiếp cận",
    "Mediall prescription savings card": "Thẻ tiết kiệm chi phí đơn thuốc Mediall",
    "Mediall Care": "Chăm sóc Mediall",
    "Mediall Companion": "Đồng hành cùng Mediall",
    "Mediall for pets": "Mediall dành cho thú cưng",
    "Brand-name medications": "Thuốc biệt dược",
    "Out-of-pocket costs": "Chi phí tự thanh toán",
    "Classes of medications": "Nhóm thuốc",
    "Medications by health conditions": "Thuốc theo tình trạng sức khỏe",
    "Medications A-Z": "Danh mục thuốc A-Z",
    "Mobile apps": "Ứng dụng di động",
    "Insurance": "Bảo hiểm",
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
    dependencies = [("accounts", "0049_delete_expired_appointments")]

    operations = [migrations.RunPython(add_translations, remove_translations)]
