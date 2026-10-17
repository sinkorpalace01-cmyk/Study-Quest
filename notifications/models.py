from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=250, blank=True)
    kind = models.CharField(max_length=24, default="info")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


def notify(user, title, body="", link="", kind="info"):
    return Notification.objects.create(user=user, title=title, body=body, link=link, kind=kind)
