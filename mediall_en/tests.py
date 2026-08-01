from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import BlogPost, FeaturedPostGroup
from mediall_en.views import build_post_editor_toolbar, sanitize_post_html


class AdminPostManagementTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="admin-posts",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(self.staff_user)
        self.post = BlogPost.objects.create(
            title="Original title",
            content_html="<p>Original content</p>",
            seo_description="Original description",
            tags="Health",
            author=self.staff_user,
        )

    def test_post_list_shows_edit_and_delete_actions(self):
        response = self.client.get(reverse("admin_posts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("admin_edit_post", args=[self.post.pk]))
        self.assertContains(response, reverse("admin_delete_post", args=[self.post.pk]))
        self.assertContains(response, "Edit")
        self.assertContains(response, "Delete")

    def test_staff_user_can_edit_post(self):
        response = self.client.post(
            reverse("admin_edit_post", args=[self.post.pk]),
            {
                "title": "Updated title",
                "content_html": "<p>Updated content</p><script>alert('x')</script>",
                "seo_description": "Updated description",
                "tags": "Health, health, Nutrition",
                "is_published": "on",
            },
        )

        self.assertRedirects(response, reverse("admin_posts"))
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated title")
        self.assertEqual(self.post.content_html, "<p>Updated content</p>")
        self.assertEqual(self.post.tags, "Health, Nutrition")
        self.assertTrue(self.post.is_published)

    def test_delete_endpoint_only_accepts_post(self):
        response = self.client.get(reverse("admin_delete_post", args=[self.post.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_staff_user_can_delete_post(self):
        response = self.client.post(reverse("admin_delete_post", args=[self.post.pk]))

        self.assertRedirects(response, reverse("admin_posts"))
        self.assertFalse(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_staff_user_can_search_posts_by_title(self):
        BlogPost.objects.create(
            title="Nutrition guide",
            content_html="<p>Nutrition content</p>",
            author=self.staff_user,
        )

        response = self.client.get(reverse("admin_posts"), {"q": "nutrition"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nutrition guide")
        self.assertNotContains(response, self.post.title)
        self.assertEqual(response.context["result_count"], 1)

    def test_staff_user_can_filter_posts_by_category(self):
        category = FeaturedPostGroup.objects.create(name="Nutrition")
        categorized_post = BlogPost.objects.create(
            title="Healthy meals",
            content_html="<p>Healthy meal content</p>",
            author=self.staff_user,
            featured_group=category,
        )

        response = self.client.get(
            reverse("admin_posts"),
            {"category": str(category.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, categorized_post.title)
        self.assertNotContains(response, self.post.title)
        self.assertEqual(response.context["category_filter"], str(category.pk))

    def test_category_filter_is_carried_to_create_post_page(self):
        category = FeaturedPostGroup.objects.create(name="Cardiology")

        list_response = self.client.get(
            reverse("admin_posts"),
            {"category": str(category.pk)},
        )
        create_url = f'{reverse("admin_create_post")}?category={category.pk}'

        self.assertContains(list_response, create_url)

        create_response = self.client.get(create_url)
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(
            create_response.context["form_values"]["featured_group_id"],
            str(category.pk),
        )
        self.assertContains(
            create_response,
            f'<option value="{category.pk}" selected>{category.name}</option>',
            html=True,
        )

    def test_staff_user_can_create_post_in_selected_category(self):
        category = FeaturedPostGroup.objects.create(name="Dermatology")

        response = self.client.post(
            reverse("admin_create_post"),
            {
                "title": "Skin care guide",
                "content_html": "<p>Skin care content</p>",
                "seo_description": "Skin care description",
                "tags": "Skin",
                "featured_group_id": str(category.pk),
                "is_published": "on",
            },
        )

        self.assertRedirects(response, reverse("admin_posts"))
        created_post = BlogPost.objects.get(title="Skin care guide")
        self.assertEqual(created_post.featured_group, category)
        self.assertTrue(created_post.is_featured)

    def test_editor_toolbar_contains_image_button(self):
        image_tools = [
            tool for tool in build_post_editor_toolbar()
            if tool["id"] == "image"
        ]

        self.assertEqual(len(image_tools), 1)
        self.assertTrue(image_tools[0]["image_upload"])
        self.assertEqual(
            image_tools[0]["upload_url"],
            reverse("admin_post_image_upload"),
        )

    def test_staff_user_can_upload_post_image(self):
        image_bytes = BytesIO()
        Image.new("RGB", (32, 24), color="teal").save(image_bytes, format="PNG")
        image_bytes.seek(0)

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("admin_post_image_upload"),
                {
                    "image": SimpleUploadedFile(
                        "post-image.png",
                        image_bytes.read(),
                        content_type="image/png",
                    ),
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.json()["url"], r"^/media/posts/\d{4}/\d{2}/[a-f0-9]+\.png$")

    def test_post_image_upload_rejects_non_image_file(self):
        response = self.client.post(
            reverse("admin_post_image_upload"),
            {
                "image": SimpleUploadedFile(
                    "not-an-image.png",
                    b"<script>alert(1)</script>",
                    content_type="image/png",
                ),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "The selected file is not a valid image.")

    def test_post_sanitizer_allows_safe_images_and_rejects_unsafe_sources(self):
        sanitized = sanitize_post_html(
            '<p><img src="https://cdn.example.com/health.jpg" '
            'alt="Health" onerror="alert(1)"></p>'
            '<img src="javascript:alert(1)" onerror="alert(1)">'
        )

        self.assertEqual(
            sanitized,
            '<p><img src="https://cdn.example.com/health.jpg" '
            'alt="Health" loading="lazy"></p>',
        )
