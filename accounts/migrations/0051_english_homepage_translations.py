from django.db import migrations


TRANSLATIONS = {
    "Health Education & Information Sessions from": "Phiên hướng dẫn và cung cấp thông tin sức khỏe từ",
    "Schedule your Health Education Session NOW or at your preferred time": "Đặt phiên hướng dẫn sức khỏe ngay hoặc vào thời gian bạn mong muốn",
    "Two options for health education support": "Hai lựa chọn hỗ trợ giáo dục sức khỏe",
    "Compare options": "So sánh các lựa chọn",
    "Membership option comparison": "So sánh lựa chọn thành viên",
    "Close comparison": "Đóng bảng so sánh",
    "What would you like help with?": "Bạn muốn được hỗ trợ vấn đề gì?",
    "Instant Guidance": "Hướng dẫn tức thì",
    "No Waiting Until Tomorrow": "Không cần chờ đến ngày mai",
    "No Long Waiting Times: Skip the days or weeks of waiting for a traditional doctor's appointment.": "Không phải chờ đợi lâu: Bỏ qua nhiều ngày hoặc nhiều tuần chờ lịch khám truyền thống.",
    "Instant, On-Demand Access: Our international health education services are available right now, exactly when you need it most.": "Tiếp cận tức thì theo nhu cầu: Dịch vụ giáo dục sức khỏe quốc tế luôn sẵn sàng đúng lúc bạn cần nhất.",
    "Available Worldwide: We proudly provide immediate, virtual informational guidance to users globally.": "Phục vụ toàn cầu: Chúng tôi cung cấp hướng dẫn thông tin trực tuyến tức thì cho người dùng trên toàn thế giới.",
    "Strictly Educational: All on-demand sessions focus exclusively on wellness education and general health information.": "Chỉ nhằm mục đích giáo dục: Mọi phiên theo yêu cầu tập trung vào kiến thức chăm sóc sức khỏe và thông tin sức khỏe tổng quát.",
    "One Medical membership benefits": "Quyền lợi thành viên One Medical",
    "Already purchased membership on Medi All?": "Bạn đã mua gói thành viên trên Medi All?",
    "See membership benefits ›": "Xem quyền lợi thành viên ›",
    "Our Scope of Service": "Phạm vi dịch vụ của chúng tôi",
    "We focus exclusively on providing wellness education and informational guidance for minor, everyday ailments (such as common colds, mild allergies, or general health questions), as well as routine skincare and haircare education (such as managing mild acne, dry skin, or general hair health).This includes helping you understand safe, Over-the-Counter (OTC) products, topical solutions, and non-prescription options available in your country to manage your mild symptoms effectively.": "Chúng tôi tập trung cung cấp kiến thức chăm sóc sức khỏe và hướng dẫn thông tin cho các vấn đề nhẹ thường ngày (như cảm lạnh thông thường, dị ứng nhẹ hoặc câu hỏi sức khỏe tổng quát), cùng kiến thức chăm sóc da và tóc định kỳ (như kiểm soát mụn nhẹ, da khô hoặc sức khỏe tóc). Nội dung này giúp bạn hiểu về các sản phẩm không kê đơn (OTC), dung dịch dùng ngoài và lựa chọn không cần đơn thuốc an toàn tại quốc gia của bạn để kiểm soát hiệu quả các triệu chứng nhẹ.",
    "See locations and appointment availability": "Xem địa điểm và lịch hẹn còn trống",
    "ON-DEMAND CARE": "CHĂM SÓC THEO YÊU CẦU",
    "Just want one-time virtual care?": "Bạn chỉ cần một phiên chăm sóc trực tuyến?",
    "Day or night, you can request one-time virtual care from Mediall One Medical to find treatment for 30+ common conditions.": "Dù ngày hay đêm, bạn có thể yêu cầu một phiên chăm sóc trực tuyến từ Mediall One Medical cho hơn 30 vấn đề sức khỏe phổ biến.",
    "Educational support fees vary by topic. Fees are subject to change. Direct messaging availability varies by state and country.": "Phí hỗ trợ giáo dục thay đổi theo chủ đề và có thể được điều chỉnh. Khả năng tư vấn qua tin nhắn phụ thuộc vào khu vực và quốc gia.",
    "Request information": "Yêu cầu thông tin",
    "How On-Demand Care works": "Chăm sóc theo yêu cầu hoạt động như thế nào",
    "Frequently asked questions": "Câu hỏi thường gặp",
    "See all Mediall One Medical FAQs": "Xem tất cả câu hỏi thường gặp về Mediall One Medical",
    "Global Legal Notice & Disclaimer": "Thông báo pháp lý và tuyên bố miễn trừ trách nhiệm toàn cầu",
    '"As a physician licensed outside your local jurisdiction, please be advised that this on-demand service is strictly for educational and informational purposes. These sessions do not constitute the practice of medicine. We do not provide local clinical diagnoses, write medical prescriptions, dispense medications, or manage prescription drug therapies under your country\'s laws. This service does not replace formal medical care or the professional judgment of a local healthcare provider in your area. If you are experiencing a medical emergency, severe allergic reactions, acute skin conditions, or severe symptoms, please contact your local emergency services immediately."': '"Xin lưu ý rằng bác sĩ có thể được cấp phép ngoài khu vực pháp lý nơi bạn sinh sống và dịch vụ theo yêu cầu này chỉ nhằm mục đích giáo dục, cung cấp thông tin. Các phiên này không cấu thành hoạt động hành nghề y. Chúng tôi không chẩn đoán lâm sàng tại địa phương, kê đơn, cấp phát thuốc hoặc quản lý liệu pháp thuốc kê đơn theo luật pháp quốc gia của bạn. Dịch vụ không thay thế chăm sóc y tế chính thức hoặc nhận định chuyên môn của nhân viên y tế tại địa phương. Nếu gặp tình trạng cấp cứu, phản ứng dị ứng nghiêm trọng, bệnh da cấp tính hoặc triệu chứng nặng, hãy liên hệ ngay dịch vụ cấp cứu tại nơi bạn sống."',
    "Get virtual care fast": "Nhận hỗ trợ trực tuyến nhanh chóng",
    "Doctor smiling": "Bác sĩ đang mỉm cười",
    "Mother and child": "Mẹ và con",
    "Nurse and patient": "Điều dưỡng và bệnh nhân",
    "Man on bench": "Người đàn ông ngồi trên ghế",
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
    dependencies = [("accounts", "0050_footer_ui_translations")]

    operations = [migrations.RunPython(add_translations, remove_translations)]
