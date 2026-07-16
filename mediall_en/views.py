from django.db.models import Q
from django.shortcuts import render

from doctors.models import Doctor

def home_page(request):
    # Dữ liệu cho Carousel (Băng chuyền các loại bệnh)
    carousel_conditions = [
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Urinary-Tract-Infection_Carousel_1x_220x220.png", "title": "Urinary tract<br>infection (UTI)"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Erectile-Dysfunction_Carousel_1x_220x220.png", "title": "Erectile<br>dysfunction"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/menopause/K_Conditions_Menopause_Carousel_1x_220x220.png", "title": "Menopause"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Vaginal-Yeast-Infection_Carousel_1x_220x220.png", "title": "Vaginal yeast<br>infection"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Cough-Cold-Flu-Strep_Carousel_1x_220x220.png", "title": "Cold and flu"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_DiabetesType2_Carousel_1x_220x220.png", "title": "Type 2 diabetes"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Anti-Aging_Carousel_1x_220x220.png", "title": "Anti-aging skin<br>care"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Pink-Eye_Carousel_1x_220x220.png", "title": "Pink eye"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Male-Hair-Loss_Carousel_1x_220x220.png", "title": "Male-pattern<br>hair loss"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Bacterial-Vaginosis_Carousel_1x_220x220.png", "title": "Bacterial<br>vaginosis (BV)"},
        {"img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/K_Conditions_Birth-Control_Carousel_1x_220x220.png", "title": "Birth control"},
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
            "img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_ciq._CB1715995169_.png",
            "title": "Answer some questions",
            "desc": "Choose a condition you need help with, answer some questions, and connect with a provider through direct message or video."
        },
        {
            "step": 2,
            "img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_treatmentplan._CB1715995169_.png",
            "title": "Get a care summary",
            "desc": "Your provider will determine what's medically appropriate for you and send any prescriptions to a pharmacy of your choice."
        },
        {
            "step": 3,
            "img": "https://m.media-Mediall.com/images/G/01/katara/kyanite/storefront/Illustration_HIW_followup._CB1715995169_.png",
            "title": "14 days to follow up",
            "desc": "You'll have unlimited follow-up messaging with your provider for 14 days after you receive your care summary."
        }
    ]

    context = {
        'carousel_conditions': carousel_conditions,
        'condition_tabs': condition_tabs,
        'how_it_works': how_it_works,
    }
    
    return render(request, 'home.html', context)


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
