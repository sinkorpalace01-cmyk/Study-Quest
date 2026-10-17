import io
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from pypdf import PdfReader
from PIL import Image

from accounts.forms import ProfileForm, SignupForm
from certificates.models import Certificate
from core.models import SiteSettings
from notifications.models import Notification
from quests.models import Quest


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class UpdatedWorkflowsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="learner", email="Learner@Example.com", password="GoodPass123!xyz")
        self.other = get_user_model().objects.create_user(username="other", email="other@example.com", password="GoodPass123!xyz")

    def test_email_login_is_case_insensitive_and_duplicate_signup_is_rejected(self):
        self.assertEqual(self.user.email, "learner@example.com")
        response = self.client.post(reverse("login"), {"username": "LEARNER@EXAMPLE.COM", "password": "GoodPass123!xyz"})
        self.assertRedirects(response, reverse("dashboard"))
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "learner", "password": "GoodPass123!xyz"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please check your email and password")
        form = SignupForm({"username": "fresh", "email": "LEARNER@example.com", "password1": "GoodPass123!xyz", "password2": "GoodPass123!xyz"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        profile = ProfileForm({"email": "OTHER@example.com"}, instance=self.user)
        self.assertFalse(profile.is_valid())
        self.assertIn("email", profile.errors)

    def test_contact_page_renders_for_signed_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("contact"))
        self.assertContains(response, 'class="contact-shell"')
        self.assertContains(response, 'class="site-header public-header"')

    def test_admin_auth_image_updates_public_pages(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_login(self.user)
        site = SiteSettings.current()
        response = self.client.post(reverse("admin_settings"), {
            "name": site.name, "tagline": site.tagline, "description": site.description,
            "logo_url": site.logo_url, "auth_image_url": "https://example.com/new-learning.jpg",
            "contact_email": site.contact_email, "contact_phone": site.contact_phone,
            "contact_address": site.contact_address, "support_url": site.support_url,
            "accent_color": site.accent_color, "footer_text": site.footer_text,
            "allow_registration": "on",
        })
        self.assertRedirects(response, reverse("admin_settings"))
        site.refresh_from_db()
        self.assertEqual(site.auth_image_url, "https://example.com/new-learning.jpg")
        for path in (reverse("login"), reverse("password_reset"), reverse("contact")):
            with self.subTest(path=path):
                self.assertContains(self.client.get(path), 'src="https://example.com/new-learning.jpg"')
        self.assertContains(self.client.get(reverse("landing")), "Certificate template preview")

    def test_notification_open_marks_one_read_and_clear_actions_are_owned(self):
        self.client.force_login(self.user)
        mine = Notification.objects.create(user=self.user, title="First", link="/quests/")
        second = Notification.objects.create(user=self.user, title="Second")
        foreign = Notification.objects.create(user=self.other, title="Private")
        response = self.client.post(reverse("notification_open", args=[mine.pk]))
        self.assertRedirects(response, reverse("quest_list"))
        mine.refresh_from_db()
        self.assertTrue(mine.is_read)
        self.assertNotContains(self.client.get(reverse("notification_list"), {"status": "unread"}), "First")
        self.client.post(reverse("notification_clear_selected"), {"selected": [str(second.pk), str(foreign.pk)]})
        self.assertFalse(Notification.objects.filter(pk=second.pk).exists())
        self.assertTrue(Notification.objects.filter(pk=foreign.pk).exists())
        self.client.post(reverse("notification_delete", args=[mine.pk]))
        self.assertFalse(Notification.objects.filter(pk=mine.pk).exists())
        Notification.objects.create(user=self.user, title="Third")
        self.client.post(reverse("notification_clear_all"))
        self.assertEqual(self.user.notifications.count(), 0)
        self.assertTrue(Notification.objects.filter(pk=foreign.pk).exists())

    def test_quest_filters_and_delete_only_affect_owner(self):
        self.client.force_login(self.user)
        mine = Quest.objects.create(user=self.user, title="Solar System", topic="Astronomy", difficulty="beginner")
        foreign = Quest.objects.create(user=self.other, title="Private Quest", topic="Astronomy")
        response = self.client.get(reverse("quest_list"), {"q": "solar", "difficulty": "beginner"})
        self.assertContains(response, "Solar System")
        self.assertNotContains(response, "Private Quest")
        self.assertEqual(self.client.post(reverse("quest_delete", args=[foreign.pk])).status_code, 404)
        self.client.post(reverse("quest_delete", args=[mine.pk]))
        self.assertFalse(Quest.objects.filter(pk=mine.pk).exists())
        self.assertTrue(Quest.objects.filter(pk=foreign.pk).exists())

    def test_certificate_preview_filters_and_pdf_use_site_brand(self):
        SiteSettings.objects.create(pk=1, name="BrightPath", logo_url="https://example.com/brand.png")
        self.user.avatar_url = "https://example.com/avatar.png"
        self.user.save(update_fields=["avatar_url"])
        quest = Quest.objects.create(user=self.user, title="Astronomy Essentials", topic="Astronomy", difficulty="beginner")
        cert = Certificate.objects.create(user=self.user, quest=quest, average_score=92)
        self.client.force_login(self.user)
        response = self.client.get(reverse("certificate_list"), {"q": "Astronomy", "score": "90"})
        self.assertContains(response, "BrightPath")
        self.assertContains(response, 'aria-label="Loading BrightPath"')
        self.assertContains(response, 'class="quest-loader-emblem"><img src="https://example.com/brand.png"')
        self.assertContains(response, "Beginner level")
        self.assertContains(response, "SCAN TO VERIFY")
        self.assertContains(response, "data:image/png;base64,")
        self.assertContains(response, "92%")
        self.assertNotContains(self.client.get(reverse("certificate_list"), {"score": "90", "q": "Missing"}), "Astronomy Essentials")
        logo = io.BytesIO()
        avatar = io.BytesIO()
        Image.new("RGB", (24, 24), "#7258e8").save(logo, format="PNG")
        Image.new("RGB", (24, 24), "#f4c95d").save(avatar, format="PNG")
        with patch("certificates.services.safe_image_bytes", side_effect=[logo.getvalue(), avatar.getvalue()]) as loader:
            pdf = self.client.get(reverse("certificate_download", args=[cert.code]))
        self.assertEqual(loader.call_count, 2)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        page = PdfReader(io.BytesIO(pdf.content)).pages[0]
        text = page.extract_text()
        self.assertIn("BrightPath", text)
        self.assertIn("Astronomy Essentials", text)
        self.assertIn("Beginner level", text)
        self.assertGreaterEqual(len(page["/Resources"]["/XObject"]), 3)
        self.assertContains(self.client.get(reverse("certificate_verify", args=[cert.code])), "Beginner")
