from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Invitation


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class InvitationAndOwnerAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.learner = user_model.objects.create_user(username="learner", email="learner@example.com", password="ValidPass123!x")
        self.owner = user_model.objects.create_superuser(username="owner", email="owner@example.com", password="ValidPass123!x")

    def test_public_pages_share_the_brand_header_and_footer(self):
        for path in (reverse("landing"), reverse("login"), reverse("signup"), reverse("password_reset")):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "public-header")
                self.assertContains(response, "site-footer")
                self.assertContains(response, "StudyQuest")

    def test_authenticated_shell_has_fixed_header_sidebar_and_mobile_menu(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="sidebar-toggle"')
        self.assertContains(response, 'id="sidebar"')
        self.assertContains(response, "mobile-nav")
        self.assertContains(response, "site-footer")

    def test_ordinary_user_can_only_invite_learners(self):
        self.client.force_login(self.learner)
        response = self.client.post(reverse("invite"), {"email": "new@example.com", "role": "staff"})
        invitation = Invitation.objects.get(email="new@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(invitation.role, "learner")
        self.assertEqual(invitation.invited_by, self.learner)

    def test_owner_can_invite_an_administrator(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("invite"), {"email": "admin-invite@example.com", "role": "staff"})
        self.assertEqual(response.status_code, 200)
        invitation = Invitation.objects.get()
        self.assertEqual(invitation.role, "staff")
        self.client.post(reverse("invite_accept", args=[invitation.token]), {
            "username": "invited-admin", "first_name": "Invited", "last_name": "Admin",
            "password1": "ValidPass123!x", "password2": "ValidPass123!x",
        })
        self.assertTrue(get_user_model().objects.get(username="invited-admin").is_staff)

    def test_invitation_is_single_use_and_creates_the_account(self):
        invitation = Invitation.objects.create(email="new@example.com", invited_by=self.learner)
        response = self.client.post(reverse("invite_accept", args=[invitation.token]), {
            "username": "newlearner", "first_name": "New", "last_name": "Learner",
            "password1": "ValidPass123!x", "password2": "ValidPass123!x",
        })
        self.assertRedirects(response, reverse("dashboard"))
        created = get_user_model().objects.get(email="new@example.com")
        self.assertTrue(created.check_password("ValidPass123!x"))
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.accepted_at)
        self.assertEqual(self.client.get(reverse("invite_accept", args=[invitation.token])).status_code, 410)

    def test_owner_can_delete_another_user_but_not_self(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("admin_user_delete", args=[self.learner.pk]))
        self.assertRedirects(response, reverse("admin_users"))
        self.assertFalse(get_user_model().objects.filter(pk=self.learner.pk).exists())
        response = self.client.post(reverse("admin_user_delete", args=[self.owner.pk]))
        self.assertTrue(get_user_model().objects.filter(pk=self.owner.pk).exists())

    def test_expired_invitation_cannot_be_accepted(self):
        invitation = Invitation.objects.create(email="expired@example.com", invited_by=self.learner, expires_at=timezone.now() - timedelta(seconds=1))
        response = self.client.get(reverse("invite_accept", args=[invitation.token]))
        self.assertEqual(response.status_code, 410)
