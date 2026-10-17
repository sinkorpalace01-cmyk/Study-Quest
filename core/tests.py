import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .emailing import branded_email
from .models import ContactMessage, HeroSlide, SiteSettings


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="hello@example.com", EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
class PublicHomeAndContactTests(TestCase):
    def test_home_has_three_seeded_slides_and_carousel_controls(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["slides"].count(), 3)
        self.assertTrue(all(slide.media_type == "image" and slide.media_url.startswith("/static/images/hero-") for slide in response.context["slides"]))
        self.assertContains(response, "data-hero-slider")
        self.assertContains(response, "Show slide 3")
        self.assertContains(response, "home-hero.js")

    def test_contact_message_is_saved_and_notifies_site_contact(self):
        SiteSettings.objects.create(pk=1, contact_email="team@example.com")
        response = self.client.post(reverse("contact"), {
            "name": "A Learner", "email": "learner@example.com", "subject": "A question",
            "message": "Could you help me?", "website": "",
        }, follow=True)
        self.assertRedirects(response, reverse("contact"))
        self.assertContains(response, 'class="feedback-toast success"')
        self.assertContains(response, 'data-feedback-close')
        self.assertContains(response, 'Thanks for reaching out.')
        record = ContactMessage.objects.get()
        self.assertEqual(record.email, "learner@example.com")
        self.assertTrue(record.email_sent)
        self.assertEqual(mail.outbox[0].to, ["team@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["learner@example.com"])
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn("StudyQuest", html)
        self.assertIn("NEW CONTACT MESSAGE", html)

    def test_branded_email_uses_site_name_logo_and_contact_details(self):
        SiteSettings.objects.create(pk=1, name="BrightPath", tagline="Learn one thing today.", logo_url="https://cdn.example/logo.png", contact_email="help@example.com")
        branded_email("Welcome to BrightPath", "welcome", "learner@example.com", {"user": type("User", (), {"first_name": "Ari", "username": "ari"})()})
        email = mail.outbox[0]
        self.assertIn("BrightPath", email.subject)
        html = email.alternatives[0][0]
        self.assertIn("BrightPath", html)
        self.assertIn("https://cdn.example/logo.png", html)
        self.assertIn("help@example.com", html)
        self.assertIn("Learn one thing today.", html)

    def test_password_reset_sends_branded_html_and_plain_text(self):
        SiteSettings.objects.create(pk=1, name="BrightPath", logo_url="https://cdn.example/logo.png", contact_email="help@example.com")
        get_user_model().objects.create_user(username="ari", email="ari@example.com", password="ValidPass123!x")
        response = self.client.post(reverse("password_reset"), {"email": "ari@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("BrightPath", email.subject)
        self.assertEqual(email.content_subtype, "plain")
        self.assertIn("Choose a new password", email.body)
        html = email.alternatives[0][0]
        self.assertIn("https://cdn.example/logo.png", html)
        self.assertIn("BrightPath", html)
        self.assertIn("Reset my password", html)
        reset_link = re.search(r"http://testserver(/accounts/reset/[^\s]+)", email.body)
        self.assertIsNotNone(reset_link)
        confirm = self.client.get(reset_link.group(1))
        self.assertEqual(confirm.status_code, 302)
        updated = self.client.post(confirm["Location"], {"new_password1": "AnotherValidPass123!", "new_password2": "AnotherValidPass123!"})
        self.assertRedirects(updated, reverse("password_reset_complete"))
        self.assertTrue(get_user_model().objects.get(username="ari").check_password("AnotherValidPass123!"))

    def test_contact_honeypot_does_not_store_or_send_message(self):
        response = self.client.post(reverse("contact"), {
            "name": "Bot", "email": "bot@example.com", "subject": "Spam",
            "message": "Please buy", "website": "http://spam.test",
        })
        self.assertRedirects(response, reverse("contact"))
        self.assertFalse(ContactMessage.objects.exists())
        self.assertEqual(len(mail.outbox), 0)


class HeroSlideAdminTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(username="editor", password="ValidPass123!x", is_staff=True)
        self.client.force_login(self.staff)

    def test_staff_can_edit_hero_slide_with_media_url(self):
        slide = HeroSlide.objects.first()
        response = self.client.post(reverse("admin_hero_slide_edit", args=[slide.pk]), {
            "position": slide.position, "is_active": "on", "eyebrow": "A new adventure",
            "title": "Explore the stars", "body": "Start with one small question and grow your knowledge.",
            "media_type": "image", "media_url": "https://example.com/hero.jpg",
            "cta_text": "Start learning", "cta_url": "/accounts/signup/",
            "media_upload": "",
        })
        self.assertRedirects(response, reverse("admin_hero_slides"))
        slide.refresh_from_db()
        self.assertEqual(slide.title, "Explore the stars")
        self.assertEqual(slide.media_url, "https://example.com/hero.jpg")

    @patch("core.views.media_value", return_value="https://res.cloudinary.com/example/image/upload/hero.jpg")
    def test_staff_can_upload_hero_image(self, uploader):
        slide = HeroSlide.objects.first()
        image = SimpleUploadedFile("hero.jpg", b"small image", content_type="image/jpeg")
        response = self.client.post(reverse("admin_hero_slide_edit", args=[slide.pk]), {
            "position": slide.position, "is_active": "on", "eyebrow": "A new adventure",
            "title": "Explore the stars", "body": "Start with one small question.",
            "media_type": "image", "media_url": slide.media_url,
            "cta_text": "Start learning", "cta_url": "/accounts/signup/", "media_upload": image,
        })
        self.assertRedirects(response, reverse("admin_hero_slides"))
        slide.refresh_from_db()
        self.assertEqual(slide.media_url, "https://res.cloudinary.com/example/image/upload/hero.jpg")
        self.assertEqual(uploader.call_args.kwargs["kind"], "visual")

    def test_staff_can_publish_a_video_slide(self):
        slide = HeroSlide.objects.first()
        response = self.client.post(reverse("admin_hero_slide_edit", args=[slide.pk]), {
            "position": slide.position, "is_active": "on", "eyebrow": "Watch and learn",
            "title": "Learning in motion", "body": "See how a focused quest can help you grow.",
            "media_type": "video", "media_url": "https://example.com/learning.mp4",
            "cta_text": "Create a quest", "cta_url": "/accounts/signup/",
        })
        self.assertRedirects(response, reverse("admin_hero_slides"))
        landing = self.client.get(reverse("landing"))
        self.assertContains(landing, "<video")
        self.assertContains(landing, "https://example.com/learning.mp4")

    def test_slide_editor_shows_one_media_url_field(self):
        slide = HeroSlide.objects.first()
        response = self.client.get(reverse("admin_hero_slide_edit", args=[slide.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode().count('id="id_media_url"'), 1)

    def test_staff_can_process_contact_message(self):
        message = ContactMessage.objects.create(name="Ari", email="ari@example.com", subject="Help", message="A question")
        response = self.client.post(reverse("admin_contact_status", args=[message.pk]), {"status": "resolved"})
        self.assertRedirects(response, reverse("admin_contact_messages"))
        message.refresh_from_db()
        self.assertEqual(message.status, "resolved")

    def test_ordinary_learner_cannot_open_hero_editor(self):
        self.client.force_login(get_user_model().objects.create_user(username="learner", email="learner@example.net", password="ValidPass123!x"))
        self.assertEqual(self.client.get(reverse("admin_hero_slides")).status_code, 302)

