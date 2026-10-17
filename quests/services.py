from datetime import timedelta
import io
import ipaddress
import socket
from urllib.parse import urlparse
import requests
from pypdf import PdfReader
from django.db import transaction
from django.utils import timezone
from core.ai_client import generate_quest
from notifications.models import notify
from .models import Badge, Level, Question, Quest, UserBadge


def read_source_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Source URLs must use HTTP or HTTPS.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443 if parsed.scheme == "https" else 80, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError("Source URL must point to a public website.")
    except socket.gaierror as exc:
        raise ValueError("Could not resolve the source URL.") from exc
    response = requests.get(url, timeout=12, allow_redirects=False, stream=True)
    response.raise_for_status()
    if response.is_redirect:
        raise ValueError("Redirecting source URLs are not supported.")
    kind = response.headers.get("Content-Type", "").lower()
    if kind.startswith(("image/", "audio/", "video/")):
        return ""
    data = b""
    for chunk in response.iter_content(65536):
        data += chunk
        if len(data) > 3 * 1024 * 1024:
            raise ValueError("Source URL content is too large.")
    if "pdf" in kind or parsed.path.lower().endswith(".pdf"):
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages[:20])[:20000]
    if kind.startswith("text/") or parsed.path.lower().endswith(".txt"):
        return data.decode("utf-8", "replace")[:20000]
    raise ValueError("Source URL must point to text, PDF or media.")


@transaction.atomic
def create_quest(user, topic, source, difficulty, count, image_url="", source_url=""):
    data, provider = generate_quest(topic, source, difficulty, count)
    quest = Quest.objects.create(user=user, title=str(data.get("title") or topic)[:180], description=str(data.get("description") or ""), topic=topic, source_text=source[:30000], source_url=source_url, image_url=image_url, difficulty=difficulty, provider=provider)
    for number, item in enumerate(data["levels"], 1):
        level = Level.objects.create(quest=quest, number=number, title=str(item.get("title") or f"Level {number}")[:160], summary=str(item.get("summary") or ""), xp_reward=150 if number == count else 50, pass_percent=70 if number == count else 60)
        for order, question in enumerate(item["questions"], 1):
            Question.objects.create(level=level, prompt=str(question["prompt"]), options=[str(x) for x in question["options"]], correct_index=question["correct_index"], explanation=str(question.get("explanation") or ""), order=order)
    notify(user, "Your quest is ready", f"{quest.title} has {count} levels to explore.", f"/quests/{quest.pk}/", "quest")
    badge, _ = Badge.objects.get_or_create(code="first-quest", defaults={"name": "First Quest", "description": "Created your first quest", "icon": "🌱"})
    _, earned = UserBadge.objects.get_or_create(user=user, badge=badge)
    if earned:
        notify(user, "Badge unlocked: First Quest", "Your learning adventure has begun.", "/accounts/profile/", "badge")
    return quest


def award_activity(user, xp):
    old_rank = user.rank
    today = timezone.localdate()
    if user.last_activity == today - timedelta(days=1):
        user.streak += 1
    elif user.last_activity != today:
        user.streak = 1
    user.last_activity = today
    user.best_streak = max(user.best_streak, user.streak)
    user.xp += xp
    user.save(update_fields=["xp", "streak", "best_streak", "last_activity"])
    if user.rank != old_rank:
        notify(user, f"Level up: {user.rank}!", f"You reached {user.rank} with {user.xp} XP.", "/dashboard/", "level")
    for code, name, description, icon, threshold, metric in [
        ("first-step", "First Step", "Complete your first level", "🚀", 1, "levels"),
        ("quest-master", "Quest Master", "Complete three quests", "🏆", 3, "quests"),
        ("on-fire", "On Fire", "Reach a three day streak", "🔥", 3, "streak"),
        ("knowledge-seeker", "Knowledge Seeker", "Earn 1000 XP", "✨", 1000, "xp"),
    ]:
        value = {"levels": user.attempts.filter(passed=True).values("level_id").distinct().count(), "quests": user.certificates.count(), "streak": user.streak, "xp": user.xp}[metric]
        if value >= threshold:
            badge, _ = Badge.objects.get_or_create(code=code, defaults={"name": name, "description": description, "icon": icon, "threshold": threshold})
            _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
            if created:
                notify(user, f"Badge unlocked: {name}", description, "/accounts/profile/", "badge")
