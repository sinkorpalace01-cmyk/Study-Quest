import uuid
from django.conf import settings
from django.db import models


class Quest(models.Model):
    STATUS = [("draft", "Draft"), ("published", "Published"), ("completed", "Completed")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quests")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    topic = models.CharField(max_length=180)
    source_text = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    difficulty = models.CharField(max_length=24, default="mixed")
    status = models.CharField(max_length=12, choices=STATUS, default="published")
    provider = models.CharField(max_length=24, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def progress(self):
        total = self.levels.count()
        return round(self.levels.filter(attempts__user=self.user, attempts__passed=True).distinct().count() * 100 / total) if total else 0


class Level(models.Model):
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name="levels")
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=160)
    summary = models.TextField(blank=True)
    xp_reward = models.PositiveIntegerField(default=100)
    pass_percent = models.PositiveSmallIntegerField(default=70)

    class Meta:
        ordering = ["number"]
        unique_together = [("quest", "number")]

    def __str__(self):
        return f"{self.quest.title} · {self.title}"


class Question(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    options = models.JSONField(default=list)
    correct_index = models.PositiveSmallIntegerField()
    explanation = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveSmallIntegerField(default=0)
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default=list)
    xp_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Badge(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=240)
    icon = models.CharField(max_length=8, default="✦")
    threshold = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="earned_badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "badge")]
