from .models import UiTranslation


def ui_localization(request):
    host = request.get_host().split(":", 1)[0].lower()
    is_vi = host.startswith("vi.")
    return {
        "page_language": "vi" if is_vi else "en",
        "is_vi": is_vi,
        "ui_translations": (
            dict(UiTranslation.objects.values_list("source_text", "vietnamese_text"))
            if is_vi
            else {}
        ),
    }
