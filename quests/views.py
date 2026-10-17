from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count, Q
from datetime import timedelta
from django.utils import timezone
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from core.media import media_value
from .models import Attempt, Level, Quest, Question
from .services import award_activity, create_quest, read_source_url


@login_required
def dashboard(request):
    quests = request.user.quests.prefetch_related("levels")[:4]
    attempts = request.user.attempts.select_related("level", "level__quest")[:5]
    today = timezone.localdate()
    all_attempts = request.user.attempts.all()
    weekly = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        count = all_attempts.filter(created_at__date=day).count()
        weekly.append({"label": day.strftime("%a"), "count": count, "height": min(100, max(6, count * 22))})
    recent_days = []
    for offset in range(27, -1, -1):
        day = today - timedelta(days=offset)
        recent_days.append({"date": day.strftime("%b %d"), "active": all_attempts.filter(created_at__date=day).exists()})
    accuracy = round(all_attempts.aggregate(value=Avg("score"))["value"] or 0)
    return render(request, "quests/dashboard.html", {"quests": quests, "attempts": attempts, "quest_count": request.user.quests.count(), "level_count": all_attempts.filter(passed=True).values("level_id").distinct().count(), "cert_count": request.user.certificates.count(), "badges": request.user.earned_badges.select_related("badge")[:4], "weekly": weekly, "recent_days": recent_days, "accuracy": accuracy})


@login_required
def quest_list(request):
    quests = request.user.quests.prefetch_related("levels")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    difficulty = request.GET.get("difficulty", "")
    sort = request.GET.get("sort", "newest")
    if query:
        quests = quests.filter(Q(title__icontains=query) | Q(topic__icontains=query) | Q(description__icontains=query))
    if status in dict(Quest.STATUS):
        quests = quests.filter(status=status)
    if difficulty in {"beginner", "intermediate", "advanced", "mixed"}:
        quests = quests.filter(difficulty=difficulty)
    quests = quests.order_by("title" if sort == "title" else "created_at" if sort == "oldest" else "-created_at")
    return render(request, "quests/list.html", {"quests": quests, "query": query, "status": status, "difficulty": difficulty, "sort": sort})


@login_required
def quest_new(request):
    if request.method == "POST":
        topic = request.POST.get("topic", "").strip()[:180]
        source = request.POST.get("source_text", "").strip()
        difficulty = request.POST.get("difficulty", "mixed")
        count = min(5, max(1, int(request.POST.get("level_count", "3"))))
        if not topic:
            messages.error(request, "Enter a topic for your quest.")
        else:
            try:
                image_url = media_value(request.FILES.get("image_upload"), request.POST.get("image_url", ""), "studyquest/quests", "image")
                source_url = media_value(request.FILES.get("source_upload"), request.POST.get("source_url", ""), "studyquest/sources", "source")
                if request.POST.get("source_url") and not request.FILES.get("source_upload"):
                    source += "\n" + read_source_url(source_url)
                if request.FILES.get("source_upload"):
                    upload = request.FILES["source_upload"]
                    upload.seek(0)
                    if upload.content_type == "application/pdf":
                        from pypdf import PdfReader
                        source += "\n" + "\n".join(page.extract_text() or "" for page in PdfReader(upload).pages[:20])[:20000]
                    elif upload.content_type == "text/plain":
                        source += "\n" + upload.read().decode("utf-8", "replace")[:20000]
                quest = create_quest(request.user, topic, source, difficulty, count, image_url, source_url)
                messages.success(request, "Your quest is ready.")
                return redirect("quest_detail", pk=quest.pk)
            except Exception as exc:
                messages.error(request, str(exc))
    return render(request, "quests/new.html")


@login_required
def quest_detail(request, pk):
    quest = get_object_or_404(Quest.objects.prefetch_related("levels__questions"), pk=pk, user=request.user)
    completed = set(request.user.attempts.filter(level__quest=quest, passed=True).values_list("level_id", flat=True))
    levels = [(level, level.pk in completed, level.number == 1 or quest.levels.filter(number=level.number - 1, pk__in=completed).exists()) for level in quest.levels.all()]
    return render(request, "quests/detail.html", {"quest": quest, "level_rows": levels})


@login_required
@require_POST
def quest_delete(request, pk):
    quest = get_object_or_404(Quest, pk=pk, user=request.user)
    title = quest.title
    quest.delete()
    messages.success(request, f"{title} and its learning records were deleted.")
    return redirect("quest_list")


def _owned_level(request, pk):
    return get_object_or_404(Level.objects.select_related("quest").prefetch_related("questions"), pk=pk, quest__user=request.user)


@login_required
def level_play(request, pk):
    level = _owned_level(request, pk)
    if level.number > 1 and not request.user.attempts.filter(level__quest=level.quest, level__number=level.number - 1, passed=True).exists():
        messages.error(request, "Complete the previous level first.")
        return redirect("quest_detail", pk=level.quest.pk)
    return render(request, "quests/play.html", {"level": level})


@login_required
@require_POST
def level_submit(request, pk):
    level = _owned_level(request, pk)
    if level.number > 1 and not request.user.attempts.filter(level__quest=level.quest, level__number=level.number - 1, passed=True).exists():
        raise Http404
    questions = list(level.questions.all())
    answers = []
    correct = 0
    for question in questions:
        try:
            chosen = int(request.POST.get(f"q_{question.pk}", "-1"))
        except ValueError:
            chosen = -1
        is_correct = chosen == question.correct_index
        correct += is_correct
        answers.append({"id": question.pk, "prompt": question.prompt, "options": question.options, "chosen": chosen, "correct": question.correct_index, "explanation": question.explanation, "is_correct": is_correct})
    score = round(correct * 100 / len(questions)) if questions else 0
    passed = score >= level.pass_percent
    with transaction.atomic():
        previous = Attempt.objects.filter(user=request.user, level=level).count()
        first_pass = passed and not Attempt.objects.filter(user=request.user, level=level, passed=True).exists()
        is_boss = level.number == level.quest.levels.count()
        earned = correct * (10 if previous == 0 else 2 if previous < 3 else 0)
        if first_pass:
            earned += 50 + (100 if is_boss else 0)
        attempt = Attempt.objects.create(user=request.user, level=level, score=score, passed=passed, answers=answers, xp_earned=earned)
        award_activity(request.user, earned)
        if score == 100:
            from .models import Badge, UserBadge
            badge, _ = Badge.objects.get_or_create(code="perfect-score", defaults={"name": "Perfect Score", "description": "Get every question right on a level", "icon": "💯"})
            _, new_badge = UserBadge.objects.get_or_create(user=request.user, badge=badge)
            if new_badge:
                from notifications.models import notify
                notify(request.user, "Badge unlocked: Perfect Score", "A flawless round!", "/accounts/profile/", "badge")
        if passed:
            if first_pass and not level.quest.levels.exclude(pk__in=Attempt.objects.filter(user=request.user, level__quest=level.quest, passed=True).values("level_id")).exists():
                from certificates.services import issue_certificate
                issue_certificate(request.user, level.quest)
                award_activity(request.user, 0)
    return redirect("attempt_result", pk=attempt.pk)


@login_required
def attempt_result(request, pk):
    attempt = get_object_or_404(Attempt.objects.select_related("level__quest"), pk=pk, user=request.user)
    return render(request, "quests/result.html", {"attempt": attempt})


def leaderboard(request):
    users = get_user_model().objects.filter(is_active=True).annotate(quest_total=Count("certificates", distinct=True)).order_by("-xp", "-quest_total")[:50]
    return render(request, "quests/leaderboard.html", {"leaders": users})


@login_required
@require_POST
def explain(request, pk):
    question = get_object_or_404(Question.objects.select_related("level__quest"), pk=pk, level__quest__user=request.user)
    from core.ai_client import explain_answer
    return JsonResponse({"explanation": explain_answer(question)})
