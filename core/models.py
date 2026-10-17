from django.db import models


class SiteSettings(models.Model):
    name = models.CharField(max_length=100, default="StudyQuest")
    tagline = models.CharField(max_length=180, default="Learn with purpose. Grow with every quest.")
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    auth_image_url = models.CharField(max_length=500, blank=True, default="/static/images/learning-auth.png")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=60, blank=True)
    contact_address = models.CharField(max_length=240, blank=True)
    support_url = models.URLField(blank=True)
    accent_color = models.CharField(max_length=16, default="#7258e8")
    footer_text = models.CharField(max_length=240, blank=True)
    allow_registration = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.name


class IntegrationSettings(models.Model):
    cloudinary_cloud_name = models.CharField(max_length=100, blank=True)
    cloudinary_api_key = models.CharField(max_length=600, blank=True)
    cloudinary_api_secret = models.CharField(max_length=600, blank=True)
    gemini_api_key = models.CharField(max_length=600, blank=True)
    groq_api_key = models.CharField(max_length=600, blank=True)
    email_host_user = models.EmailField(blank=True)
    email_host_password = models.CharField(max_length=600, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Service integrations"


class HeroSlide(models.Model):
    MEDIA_CHOICES = [("none", "Text only"), ("image", "Image"), ("video", "Video")]

    eyebrow = models.CharField(max_length=90, blank=True)
    title = models.CharField(max_length=180)
    body = models.TextField()
    cta_text = models.CharField(max_length=48, default="Start learning free")
    cta_url = models.CharField(max_length=300, default="/accounts/signup/")
    media_type = models.CharField(max_length=12, choices=MEDIA_CHOICES, default="none")
    media_url = models.CharField(max_length=500, blank=True)
    position = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("position", "pk")

    def __str__(self):
        return f"Slide {self.position}: {self.title}"


class ContactMessage(models.Model):
    STATUS_CHOICES = [("new", "New"), ("in_progress", "In progress"), ("resolved", "Resolved")]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=180)
    message = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="new")
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.subject} — {self.name}"
