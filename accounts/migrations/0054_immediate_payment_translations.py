from django.db import migrations


TRANSLATIONS = {
    "Payment available now": "Có thể thanh toán ngay",
    "The appointment is held for 24 hours while your request is reviewed.": "Lịch hẹn được giữ trong 24 giờ trong khi yêu cầu của bạn được xét duyệt.",
    "Pay securely with Paddle": "Thanh toán an toàn với Paddle",
    "Payment is securely processed by Paddle. Mediall never receives or stores your card details.": "Thanh toán được Paddle xử lý an toàn. Mediall không nhận hoặc lưu thông tin thẻ của bạn.",
}


def seed_translations(apps, schema_editor):
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
    dependencies = [("accounts", "0053_doctorappointment_paddle_transaction_id")]

    operations = [migrations.RunPython(seed_translations, remove_translations)]
