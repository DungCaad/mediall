import random

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render

from accounts.models import AccountProfile
from doctors.models import Doctor


def set_registration_captcha(request):
    first_number = random.randint(2, 9)
    second_number = random.randint(2, 9)
    request.session["registration_captcha_answer"] = first_number + second_number
    return f"{first_number} + {second_number}"

def build_home_context(request):
    # Dữ liệu cho Carousel (Băng chuyền các loại bệnh)
    carousel_conditions = [
        {"img": "/static/images/condition-care.svg", "title": "Urinary tract<br>infection (UTI)"},
        {"img": "/static/images/condition-care.svg", "title": "Erectile<br>dysfunction"},
        {"img": "/static/images/condition-care.svg", "title": "Menopause"},
        {"img": "/static/images/condition-care.svg", "title": "Vaginal yeast<br>infection"},
        {"img": "/static/images/condition-care.svg", "title": "Cold and flu"},
        {"img": "/static/images/condition-care.svg", "title": "Type 2 diabetes"},
        {"img": "/static/images/condition-care.svg", "title": "Anti-aging skin<br>care"},
        {"img": "/static/images/condition-care.svg", "title": "Pink eye"},
        {"img": "/static/images/condition-care.svg", "title": "Male-pattern<br>hair loss"},
        {"img": "/static/images/condition-care.svg", "title": "Bacterial<br>vaginosis (BV)"},
        {"img": "/static/images/condition-care.svg", "title": "Birth control"},
    ]

    # Dữ liệu cho danh sách bệnh lưới (Grid)
    condition_tabs = [
        {
            "name": "Most popular",
            "active": True,
            "conditions": [
                "Anti-aging skin care", "Bacterial vaginosis", "Birth control",
                "Cold and flu", "COVID-19", "Erectile dysfunction",
                "Male-pattern hair loss", "Pink eye", "Sinus infection",
                "Urgent virtual care", "Urinary tract infection", "Weight loss",
                "Vaginal yeast infection",
            ],
        },
        {
            "name": "Men's health",
            "conditions": [
                "Erectile dysfunction", "Male-pattern hair loss", "Premature ejaculation",
            ],
        },
        {
            "name": "Women's health",
            "conditions": [
                "Bacterial vaginosis", "Birth control", "Emergency contraception",
                "Menopause", "Period cramps", "Positive pregnancy test",
                "Urinary tract infection", "Vaginal dryness", "Vaginal yeast infection",
            ],
        },
        {
            "name": "General health",
            "conditions": [
                "Acid reflux", "Anxiety", "Asthma",
                "Blood pressure", "Cholesterol", "Cold and flu",
                "Cold sores", "COVID-19", "Depression",
                "Diabetes type 2", "Gout attack", "Hypothyroidism",
                "Mental health", "Motion sickness", "Pink eye",
                "Quit smoking", "Seasonal allergies", "Sinus infection",
                "Skin issue", "Urgent virtual care", "Weight loss",
            ],
        },
        {
            "name": "Sexual health",
            "conditions": [
                "Bacterial vaginosis", "Birth control", "Emergency contraception",
                "Erectile dysfunction", "Genital herpes", "Genital warts",
                "Premature ejaculation", "PrEP", "STI testing",
                "Vaginal dryness",
            ],
        },
        {
            "name": "Skin and hair",
            "conditions": [
                "Acne", "Anti-aging skin care", "Athlete's foot",
                "Dandruff", "Dark spots & melasma", "Diaper rash",
                "Eczema", "Eyelash growth", "Head lice",
                "Male-pattern hair loss", "Rosacea", "Skin issue",
                "Toenail fungus",
            ],
        },
        {
            "name": "Prescription renewal",
            "conditions": [
                "Anxiety", "Asthma", "Blood pressure",
                "Cholesterol", "Depression", "Epinephrine & EpiPens",
                "Hypothyroidism", "Other medications",
            ],
        },
    ]

    all_conditions = sorted({
        condition
        for tab in condition_tabs
        for condition in tab["conditions"]
    }, key=str.lower)
    condition_tabs.append({
        "name": "All conditions",
        "conditions": all_conditions,
    })

    # Dữ liệu cho mục "How it works"
    how_it_works = [
        {
            "step": 1,
            "img": "/static/images/step-questions.svg",
            "title": "Answer some questions",
            "desc": "Choose a condition you need help with, answer some questions, and connect with a provider through direct message or video."
        },
        {
            "step": 2,
            "img": "/static/images/step-plan.svg",
            "title": "Get a care summary",
            "desc": "Your provider will determine what's medically appropriate for you and send any prescriptions to a pharmacy of your choice."
        },
        {
            "step": 3,
            "img": "/static/images/step-followup.svg",
            "title": "14 days to follow up",
            "desc": "You'll have unlimited follow-up messaging with your provider for 14 days after you receive your care summary."
        }
    ]

    context = {
        'carousel_conditions': carousel_conditions,
        'condition_tabs': condition_tabs,
        'how_it_works': how_it_works,
        'captcha_question': set_registration_captcha(request),
    }
    
    return context


def home_page(request):
    return render(request, 'home.html', build_home_context(request))


def register_account(request):
    if request.method != "POST":
        return redirect("home")

    username = request.POST.get("username", "").strip()
    phone = request.POST.get("phone", "").strip()
    password = request.POST.get("password", "")
    role = request.POST.get("role", "")
    captcha = request.POST.get("captcha", "").strip()
    expected_captcha = request.session.get("registration_captcha_answer")
    errors = []

    if not username:
        errors.append("Vui long nhap ten tai khoan.")
    if not phone:
        errors.append("Vui long nhap so dien thoai.")
    if len(password) < 6:
        errors.append("Mat khau can toi thieu 6 ky tu.")
    if role not in {AccountProfile.ROLE_PATIENT, AccountProfile.ROLE_DOCTOR}:
        errors.append("Vui long chon ban la benh nhan hay bac si.")
    if not captcha.isdigit() or int(captcha) != expected_captcha:
        errors.append("Captcha khong dung.")
    if User.objects.filter(username=username).exists():
        errors.append("Ten tai khoan da ton tai.")
    if AccountProfile.objects.filter(phone=phone).exists():
        errors.append("So dien thoai da duoc su dung.")

    if errors:
        context = build_home_context(request)
        context.update({
            "registration_errors": errors,
            "registration_form": {
                "username": username,
                "phone": phone,
                "role": role,
            },
            "open_register_modal": True,
        })
        return render(request, "home.html", context, status=400)

    user = User.objects.create_user(username=username, password=password)
    AccountProfile.objects.create(user=user, phone=phone, role=role)
    request.session.pop("registration_captcha_answer", None)

    context = build_home_context(request)
    context["registration_success"] = "Dang ky tai khoan thanh cong."
    return render(request, "home.html", context)


def doctor_search(request):
    specialty = request.GET.get("specialty", "").strip()
    keyword = specialty.lower().replace("-", " ")
    doctors = Doctor.objects.filter(is_active=True)

    if keyword:
        matched_doctors = doctors.filter(
            Q(name__icontains=keyword)
            | Q(specialties__icontains=keyword)
            | Q(address__icontains=keyword)
            | Q(search_terms__icontains=keyword)
        )
    else:
        matched_doctors = doctors

    has_direct_match = matched_doctors.exists() or not specialty
    visible_doctors = matched_doctors if has_direct_match else doctors
    context = {
        "specialty": specialty,
        "doctors": visible_doctors,
        "result_count": visible_doctors.count(),
        "has_direct_match": has_direct_match,
    }

    return render(request, "doctor_search.html", context)
