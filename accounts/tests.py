from importlib import import_module

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


class VietnameseTranslationCatalogTests(TestCase):
    def test_footer_and_accessibility_translations_are_seeded(self):
        migration = import_module(
            "accounts.migrations.0050_footer_ui_translations"
        )

        self.assertEqual(migration.TRANSLATIONS["Featured posts"], "Bài viết nổi bật")
        self.assertEqual(migration.TRANSLATIONS["Allergies"], "Dị ứng")
        self.assertEqual(
            migration.TRANSLATIONS["Condition categories"],
            "Danh mục chủ đề sức khỏe",
        )
