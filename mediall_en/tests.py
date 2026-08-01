from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import BlogPost, FeaturedPostGroup


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
