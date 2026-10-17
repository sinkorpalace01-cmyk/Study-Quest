import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def invitation_expiry():
    return timezone.now() + timedelta(days=7)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    school = models.CharField(max_length=160, blank=True)
    website = models.URLField(blank=True)
    xp = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    last_activity = models.DateField(null=True, blank=True)
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def level(self):
        return self.xp // 500 + 1

    @property
    def rank(self):
        if self.xp >= 1500:
            return "Master"
        if self.xp >= 600:
            return "Scholar"
        if self.xp >= 200:
            return "Explorer"
        return "Rookie"


class Invitation(models.Model):
    ROLE_CHOICES = [("learner", "Learner"), ("staff", "Administrator")]

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField()
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default="learner")
    invited_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="sent_invitations")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=invitation_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_valid(self):
        return self.accepted_at is None and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
