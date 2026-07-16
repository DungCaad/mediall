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
    all_conditions = [
        "Acid reflux", "Acne", "Anti-aging skin care", "Anxiety", "Asthma", "Athlete's foot",
        "Bacterial vaginosis", "Birth control", "Blood pressure", "Cholesterol", "Cold sores", 
        "Cold and flu", "COVID-19", "Dandruff", "Dark spots & melasma", "Depression", "Diaper rash", 
        "Diabetes type 2", "Eczema", "Emergency contraception", "Epinephrine & EpiPens", 
        "Erectile dysfunction", "Eyelash growth", "Genital herpes"
    ]

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
        'all_conditions': all_conditions,
        'how_it_works': how_it_works,
    }
    
    return render(request, 'home.html', context)