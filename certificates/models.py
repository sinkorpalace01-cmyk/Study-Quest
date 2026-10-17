import uuid
from django.conf import settings
from django.db import models


class Certificate(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    quest = models.OneToOneField("studyquest_quests.Quest", on_delete=models.CASCADE, related_name="certificate")
    average_score = models.PositiveSmallIntegerField(default=0)
    pdf_url = models.URLField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} · {self.quest.title}"
