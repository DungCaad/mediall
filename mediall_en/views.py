import random

from django.contrib.auth import authenticate, login, logout
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


def is_vietnamese_host(request):
    host = request.get_host().split(":", 1)[0].lower()
    return host.startswith("vi.")


def build_home_context(request):
    # Dữ liệu cho Carousel (Băng chuyền các loại bệnh)
    carousel_conditions = [
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Urinary-Tract-Infection_Carousel_1x_220x220.png", "title": "Pain & Fever Relief", "specialty": "Pain & Fever Relief"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Erectile-Dysfunction_Carousel_1x_220x220.png", "title": "Erectile<br>dysfunction", "specialty": "Erectile dysfunction"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/menopause/K_Conditions_Menopause_Carousel_1x_220x220.png", "title": "Menopause", "specialty": "Menopause"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Vaginal-Yeast-Infection_Carousel_1x_220x220.png", "title": "Vaginal yeast<br>infection", "specialty": "Vaginal yeast infection"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Cough-Cold-Flu-Strep_Carousel_1x_220x220.png", "title": "Cold and flu", "specialty": "Cold and flu"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_DiabetesType2_Carousel_1x_220x220.png", "title": "Hair & Scalp Care", "specialty": "Hair & Scalp Care"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Anti-Aging_Carousel_1x_220x220.png", "title": "Anti-aging skin<br>care", "specialty": "Anti-aging skin care"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Pink-Eye_Carousel_1x_220x220.png", "title": "Pink eye", "specialty": "Pink eye"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Male-Hair-Loss_Carousel_1x_220x220.png", "title": "Male-pattern<br>hair loss", "specialty": "Male-pattern hair loss"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Bacterial-Vaginosis_Carousel_1x_220x220.png", "title": "Anxiety, stress, and depression", "specialty": "Anxiety, stress, and depression"},
        {"img": "https://m.media-amazon.com/images/G/01/katara/kyanite/K_Conditions_Birth-Control_Carousel_1x_220x220.png", "title": "Birth control", "specialty": "Birth control"},
    ]

    # Dữ liệu cho danh sách bệnh lưới (Grid)
    condition_tabs = [
        {
            "name": "Most popular",
            "active": True,
            "conditions": [
                "Anti-aging skin care", "Anxiety, stress, and depression", "Birth control",
                "Cold and flu", "COVID-19", "Erectile dysfunction",
                "Male-pattern hair loss", "Pink eye", "Sinus infection",
                "Urgent virtual care", "Pain & Fever Relief", "Weight loss",
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
                "Anxiety, stress, and depression", "Birth control", "Emergency contraception",
                "Menopause", "Period cramps", "Positive pregnancy test",
                "Pain & Fever Relief", "Vaginal dryness", "Vaginal yeast infection",
            ],
        },
        {
            "name": "General health",
            "conditions": [
                "Acid reflux", "Anxiety", "Asthma",
                "Blood pressure", "Cholesterol", "Cold and flu",
                "Cold sores", "COVID-19", "Depression",
                "Hair & Scalp Care", "Gout attack", "Hypothyroidism",
                "Mental health", "Motion sickness", "Pink eye",
                "Quit smoking", "Seasonal allergies", "Sinus infection",
                "Skin issue", "Urgent virtual care", "Weight loss",
            ],
        },
        {
            "name": "Sexual health",
            "conditions": [
                "Anxiety, stress, and depression", "Birth control", "Emergency contraception",
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
            "img": "https://m.media-amazon.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_ciq._CB1715995169_.png",
            "title": "Answer some questions",
            "desc": "Choose a condition you need help with, answer some questions, and connect with a provider through direct message or video."
        },
        {
            "step": 2,
            "img": "https://m.media-amazon.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_treatmentplan._CB1715995169_.png",
            "title": "Get a care summary",
            "desc": "Your provider will determine what's medically appropriate for you and send any prescriptions to a pharmacy of your choice."
        },
        {
            "step": 3,
            "img": "https://m.media-amazon.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_followup._CB1715995169_.png",
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
    if is_vietnamese_host(request):
        return render(request, 'home_vi.html', build_home_context(request))
    return render(request, 'home.html', build_home_context(request))


def register_account(request):
    if request.method != "POST":
        return redirect("home")

    username = request.POST.get("username", "").strip()
    phone = request.POST.get("phone", "").strip()
    password = request.POST.get("password", "")
    role = request.POST.get("role", "")
    photo = request.POST.get("photo", "").strip()
    clinic_address = request.POST.get("clinic_address", "").strip()
    captcha = request.POST.get("captcha", "").strip()
    expected_captcha = request.session.get("registration_captcha_answer")
    errors = []

    if not username:
        errors.append("Please enter a username.")
    if not phone:
        errors.append("Please enter a phone number.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if role not in {AccountProfile.ROLE_PATIENT, AccountProfile.ROLE_DOCTOR}:
        errors.append("Please choose whether you are a patient or a doctor.")
    if role == AccountProfile.ROLE_DOCTOR and not photo:
        errors.append("Doctors must provide a profile photo URL.")
    if role == AccountProfile.ROLE_DOCTOR and not clinic_address:
        errors.append("Doctors must provide a clinic address.")
    if not captcha.isdigit() or int(captcha) != expected_captcha:
        errors.append("Captcha is incorrect.")
    if User.objects.filter(username=username).exists():
        errors.append("Username already exists.")
    if AccountProfile.objects.filter(phone=phone).exists():
        errors.append("Phone number is already in use.")

    if errors:
        context = build_home_context(request)
        context.update({
            "registration_errors": errors,
            "registration_form": {
                "username": username,
                "phone": phone,
                "role": role,
                "photo": photo,
                "clinic_address": clinic_address,
            },
            "open_register_modal": True,
        })
        return render(request, "home.html", context, status=400)

    user = User.objects.create_user(username=username, password=password)
    AccountProfile.objects.create(
        user=user,
        phone=phone,
        role=role,
        photo=photo,
        clinic_address=clinic_address,
    )
    request.session.pop("registration_captcha_answer", None)

    context = build_home_context(request)
    context["registration_success"] = "Your account has been created."
    return render(request, "home.html", context)


def login_account(request):
    if request.method != "POST":
        return redirect("home")

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    user = authenticate(request, username=username, password=password)

    if user is None:
        context = build_home_context(request)
        context.update({
            "login_errors": ["Username or password is incorrect."],
            "login_form": {"username": username},
            "open_login_modal": True,
        })
        return render(request, "home.html", context, status=400)

    login(request, user)
    return redirect("home")


def logout_account(request):
    logout(request)
    return redirect("home")


def appointment_page(request):
    featured_specialties = [
        "Pulmonology",
        "Respiratory care",
        "Dermatology",
        "Obstetrics and gynecology",
        "Endocrinology",
        "Cardiology",
    ]
    featured_doctors = Doctor.objects.filter(is_active=True)[:4]
    context = {
        "featured_specialties": featured_specialties,
        "featured_doctors": featured_doctors,
    }
    return render(request, "appointment.html", context)


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
