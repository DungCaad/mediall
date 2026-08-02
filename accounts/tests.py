from django.test import RequestFactory, TestCase

from accounts.context_processors import ui_localization


class UiLocalizationHostTests(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_azo_domains_use_vietnamese_interface(self):
        for host in ("khambenh.azo.vn", "mediall.azo.vn"):
            with self.subTest(host=host):
                context = ui_localization(self.request_factory.get("/", HTTP_HOST=host))
                self.assertTrue(context["is_vi"])
                self.assertEqual(context["page_language"], "vi")

    def test_main_domain_keeps_english_interface(self):
        context = ui_localization(
            self.request_factory.get("/", HTTP_HOST="mediall.net")
        )

        self.assertFalse(context["is_vi"])
        self.assertEqual(context["page_language"], "en")
