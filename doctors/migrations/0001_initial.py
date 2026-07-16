from django.db import migrations, models


INITIAL_DOCTORS = [
    {
        "name": "ThS. BS. CK2 Nguyen Thi Hong Hanh",
        "provider_type": "doctor",
        "avatar": "/static/images/doctor-female.svg",
        "specialties": "Ho hap|Lao - benh phoi",
        "address": "210 Phan Van Tri, Phuong 12, Quan Binh Thanh, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap",
    },
    {
        "name": "TS. BS Nguyen Duc Bang",
        "provider_type": "doctor",
        "avatar": "/static/images/doctor-male.svg",
        "specialties": "Ho hap|Lao - benh phoi",
        "address": "So 005 Chung cu Ngo Quyen, Phuong 9, Quan 5, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap",
    },
    {
        "name": "Bac si Nguyen Thanh Thai",
        "provider_type": "doctor",
        "avatar": "/static/images/doctor-male.svg",
        "specialties": "Ho hap|Lao - benh phoi",
        "address": "Can Tho",
        "cta": "Dat lich tu van",
        "cta_style": "success",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap",
    },
    {
        "name": "Benh vien Phoi Soc Trang",
        "provider_type": "clinic",
        "avatar": "/static/images/clinic.svg",
        "specialties": "Lao - benh phoi",
        "address": "So 468 Duong 30/4, Phuong Phu Loi, Can Tho",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap hospital clinic",
    },
    {
        "name": "Phong kham Phoi Quoc te An Duc",
        "provider_type": "clinic",
        "avatar": "/static/images/clinic.svg",
        "specialties": "Lao - benh phoi",
        "address": "35 Nguyen Van Cu, Quan 5, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap hospital clinic",
    },
    {
        "name": "BS. Tran Minh Quan",
        "provider_type": "doctor",
        "avatar": "/static/images/doctor-male.svg",
        "specialties": "Da lieu|Cham soc da",
        "address": "12 Nguyen Trai, Quan 1, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "acne anti aging skin care eczema dark spots melasma dandruff hair skin",
    },
    {
        "name": "BS. Le Thu Ha",
        "provider_type": "doctor",
        "avatar": "/static/images/doctor-female.svg",
        "specialties": "San phu khoa|Suc khoe phu nu",
        "address": "80 Ly Thuong Kiet, Quan 10, Ho Chi Minh",
        "cta": "Dat lich tu van",
        "cta_style": "success",
        "search_terms": "birth control menopause vaginal yeast infection bacterial vaginosis women emergency contraception",
    },
    {
        "name": "ThS. BS Pham Anh Tuan",
        "provider_type": "doctor",
        "avatar": "/static/images/doctor-male.svg",
        "specialties": "Noi tiet|Tim mach",
        "address": "56 Pasteur, Quan 3, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "diabetes type 2 cholesterol blood pressure acid reflux anxiety depression general health",
    },
]


def seed_doctors(apps, schema_editor):
    Doctor = apps.get_model("doctors", "Doctor")
    for doctor in INITIAL_DOCTORS:
        Doctor.objects.update_or_create(
            name=doctor["name"],
            defaults=doctor,
        )


def remove_seed_doctors(apps, schema_editor):
    Doctor = apps.get_model("doctors", "Doctor")
    Doctor.objects.filter(name__in=[doctor["name"] for doctor in INITIAL_DOCTORS]).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Doctor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("provider_type", models.CharField(choices=[("doctor", "Doctor"), ("clinic", "Clinic")], default="doctor", max_length=20)),
                ("avatar", models.CharField(blank=True, max_length=255)),
                ("specialties", models.CharField(help_text="Separate specialties with |", max_length=255)),
                ("address", models.CharField(blank=True, max_length=255)),
                ("cta", models.CharField(default="Dat kham", max_length=40)),
                ("cta_style", models.CharField(choices=[("primary", "Primary"), ("success", "Success")], default="primary", max_length=20)),
                ("search_terms", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(seed_doctors, remove_seed_doctors),
    ]
