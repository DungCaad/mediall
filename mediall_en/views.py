from django.shortcuts import render

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


DOCTORS = [
    {
        "name": "ThS. BS. CK2 Nguyen Thi Hong Hanh",
        "type": "doctor",
        "avatar": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=240&q=80",
        "specialties": ["Ho hap", "Lao - benh phoi"],
        "address": "210 Phan Van Tri, Phuong 12, Quan Binh Thanh, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap",
    },
    {
        "name": "TS. BS Nguyen Duc Bang",
        "type": "doctor",
        "avatar": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=240&q=80",
        "specialties": ["Ho hap", "Lao - benh phoi"],
        "address": "So 005 Chung cu Ngo Quyen, Phuong 9, Quan 5, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap",
    },
    {
        "name": "Bac si Nguyen Thanh Thai",
        "type": "doctor",
        "avatar": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=240&q=80",
        "specialties": ["Ho hap", "Lao - benh phoi"],
        "address": "Can Tho",
        "cta": "Dat lich tu van",
        "cta_style": "success",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap",
    },
    {
        "name": "Benh vien Phoi Soc Trang",
        "type": "clinic",
        "avatar": "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?auto=format&fit=crop&w=240&q=80",
        "specialties": ["Lao - benh phoi"],
        "address": "So 468 Duong 30/4, Phuong Phu Loi, Can Tho",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap hospital clinic",
    },
    {
        "name": "Phong kham Phoi Quoc te An Duc",
        "type": "clinic",
        "avatar": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=240&q=80",
        "specialties": ["Lao - benh phoi"],
        "address": "35 Nguyen Van Cu, Quan 5, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "respiratory asthma cold flu covid cough lao benh phoi ho hap hospital clinic",
    },
    {
        "name": "BS. Tran Minh Quan",
        "type": "doctor",
        "avatar": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=240&q=80",
        "specialties": ["Da lieu", "Cham soc da"],
        "address": "12 Nguyen Trai, Quan 1, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "acne anti aging skin care eczema dark spots melasma dandruff hair skin",
    },
    {
        "name": "BS. Le Thu Ha",
        "type": "doctor",
        "avatar": "https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&w=240&q=80",
        "specialties": ["San phu khoa", "Suc khoe phu nu"],
        "address": "80 Ly Thuong Kiet, Quan 10, Ho Chi Minh",
        "cta": "Dat lich tu van",
        "cta_style": "success",
        "search_terms": "birth control menopause vaginal yeast infection bacterial vaginosis women emergency contraception",
    },
    {
        "name": "ThS. BS Pham Anh Tuan",
        "type": "doctor",
        "avatar": "https://images.unsplash.com/photo-1605684954998-685c79d6a018?auto=format&fit=crop&w=240&q=80",
        "specialties": ["Noi tiet", "Tim mach"],
        "address": "56 Pasteur, Quan 3, Ho Chi Minh",
        "cta": "Dat kham",
        "cta_style": "primary",
        "search_terms": "diabetes type 2 cholesterol blood pressure acid reflux anxiety depression general health",
    },
]


def doctor_search(request):
    specialty = request.GET.get("specialty", "").strip()
    keyword = specialty.lower().replace("-", " ")

    if keyword:
        matched_doctors = [
            doctor for doctor in DOCTORS
            if keyword in doctor["search_terms"].lower()
            or any(keyword in item.lower().replace("-", " ") for item in doctor["specialties"])
        ]
    else:
        matched_doctors = DOCTORS

    context = {
        "specialty": specialty,
        "doctors": matched_doctors or DOCTORS,
        "result_count": len(matched_doctors or DOCTORS),
        "has_direct_match": bool(matched_doctors) or not specialty,
    }

    return render(request, "doctor_search.html", context)
