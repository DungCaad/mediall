from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import BlogPost


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
