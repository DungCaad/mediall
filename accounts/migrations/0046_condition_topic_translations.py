from django.db import migrations


TRANSLATIONS = {
    "Anti-aging skin care education": "Hướng dẫn chăm sóc da chống lão hóa",
    "Cold and flu info": "Thông tin về cảm lạnh và cúm",
    "COVID-19 information": "Thông tin về COVID-19",
    "Hair loss education": "Hướng dẫn về rụng tóc",
    "Pink eye info": "Thông tin về đau mắt đỏ",
    "Sinus infection info": "Thông tin về viêm xoang",
    "General virtual wellness guidance": "Hướng dẫn chăm sóc sức khỏe trực tuyến",
    "Weight management education": "Hướng dẫn kiểm soát cân nặng",
    "Yeast infection info": "Thông tin về nhiễm nấm men",
    "Male-pattern hair loss": "Rụng tóc kiểu nam giới",
    "Premature ejaculation": "Xuất tinh sớm",
    "Birth control information": "Thông tin về biện pháp tránh thai",
    "Menopause wellness guidance": "Hướng dẫn chăm sóc sức khỏe thời kỳ mãn kinh",
    "Period cramps information": "Thông tin về đau bụng kinh",
    "Vaginal dryness education": "Hướng dẫn về khô âm đạo",
    "Yeast infection education": "Hướng dẫn về nhiễm nấm men",
    "Acid reflux education": "Hướng dẫn về trào ngược axit",
    "Anxiety wellness guidance": "Hướng dẫn chăm sóc sức khỏe khi lo âu",
    "Cold sore education": "Hướng dẫn về mụn rộp môi",
    "Depression support guidance": "Hướng dẫn hỗ trợ trầm cảm",
    "Gout attack education": "Hướng dẫn xử lý cơn gút",
    "Mental health wellness guidance": "Hướng dẫn chăm sóc sức khỏe tinh thần",
    "Motion sickness information": "Thông tin về say tàu xe",
    "Smoking cessation support": "Hỗ trợ cai thuốc lá",
    "Seasonal allergy education": "Hướng dẫn về dị ứng theo mùa",
    "Skin care education": "Hướng dẫn chăm sóc da",
    "Emergency contraception education": "Hướng dẫn tránh thai khẩn cấp",
    "Acne education": "Hướng dẫn về mụn trứng cá",
    "Anti-aging skin care information": "Thông tin chăm sóc da chống lão hóa",
    "Athlete's foot education": "Hướng dẫn về nấm bàn chân",
    "Dandruff education": "Hướng dẫn về gàu",
    "Dark spot and melasma education": "Hướng dẫn về đốm nâu và nám da",
    "Diaper rash education": "Hướng dẫn về hăm tã",
    "Eczema education": "Hướng dẫn về bệnh chàm",
    "Eyelash growth information": "Thông tin về phát triển lông mi",
    "Head lice education": "Hướng dẫn về chấy",
    "Male-pattern hair loss education": "Hướng dẫn về rụng tóc kiểu nam giới",
    "Rosacea education": "Hướng dẫn về bệnh trứng cá đỏ",
    "Toenail fungus education": "Hướng dẫn về nấm móng chân",
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
    dependencies = [("accounts", "0045_ui_translation")]

    operations = [migrations.RunPython(add_translations, remove_translations)]
