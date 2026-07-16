from django.db import migrations, models


PROVIDER_UPDATES = {
    "ThS. BS. CK2 Nguyen Thi Hong Hanh": {
        "name": "Dr. Nguyen Thi Hong Hanh",
        "specialties": "Respiratory care|Pulmonology",
        "cta": "Book appointment",
        "search_terms": "respiratory asthma cold flu covid cough pulmonology lung care",
    },
    "TS. BS Nguyen Duc Bang": {
        "name": "Dr. Nguyen Duc Bang",
        "specialties": "Respiratory care|Pulmonology",
        "cta": "Book appointment",
        "search_terms": "respiratory asthma cold flu covid cough pulmonology lung care",
    },
    "Bac si Nguyen Thanh Thai": {
        "name": "Dr. Nguyen Thanh Thai",
        "specialties": "Respiratory care|Pulmonology",
        "cta": "Request consult",
        "search_terms": "respiratory asthma cold flu covid cough pulmonology lung care",
    },
    "Benh vien Phoi Soc Trang": {
        "name": "Soc Trang Lung Hospital",
        "specialties": "Pulmonology",
        "cta": "Book appointment",
        "search_terms": "respiratory asthma cold flu covid cough pulmonology lung hospital clinic",
    },
    "Phong kham Phoi Quoc te An Duc": {
        "name": "An Duc International Lung Clinic",
        "specialties": "Pulmonology",
        "cta": "Book appointment",
        "search_terms": "respiratory asthma cold flu covid cough pulmonology lung hospital clinic",
    },
    "BS. Tran Minh Quan": {
        "name": "Dr. Tran Minh Quan",
        "specialties": "Dermatology|Skin care",
        "cta": "Book appointment",
        "search_terms": "acne anti aging skin care eczema dark spots melasma dandruff hair dermatology",
    },
    "BS. Le Thu Ha": {
        "name": "Dr. Le Thu Ha",
        "specialties": "Obstetrics and gynecology|Women's health",
        "cta": "Request consult",
        "search_terms": "birth control menopause vaginal yeast infection bacterial vaginosis women emergency contraception obgyn",
    },
    "ThS. BS Pham Anh Tuan": {
        "name": "Dr. Pham Anh Tuan",
        "specialties": "Endocrinology|Cardiology",
        "cta": "Book appointment",
        "search_terms": "diabetes type 2 cholesterol blood pressure acid reflux anxiety depression general health endocrinology cardiology",
    },
}


def apply_english_copy(apps, schema_editor):
    Doctor = apps.get_model("doctors", "Doctor")
    for old_name, updates in PROVIDER_UPDATES.items():
        Doctor.objects.filter(name=old_name).update(**updates)


class Migration(migrations.Migration):
    dependencies = [
        ("doctors", "0003_restore_remote_doctor_avatars"),
    ]

    operations = [
        migrations.AlterField(
            model_name="doctor",
            name="cta",
            field=models.CharField(default="Book appointment", max_length=40),
        ),
        migrations.RunPython(apply_english_copy, migrations.RunPython.noop),
    ]
