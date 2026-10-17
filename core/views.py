import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from accounts.forms import AdminUserForm
from certificates.models import Certificate
from quests.models import Quest
from .forms import ContactForm, HeroSlideForm, SettingsForm, IntegrationForm
from .emailing import branded_email
from .integrations import FIELD_MAP, SECRET_FIELDS, encrypt, integration_value
from .media import media_value
from .models import ContactMessage, HeroSlide, SiteSettings, IntegrationSettings


def landing(request):
    slides = HeroSlide.objects.filter(is_active=True).order_by("position", "pk")[:3]
    return render(request, "core/landing.html", {"slides": slides, "learner_count": get_user_model().objects.filter(is_active=True).count(), "quest_count": Quest.objects.count(), "certificate_count": Certificate.objects.count()})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if not data["website"]:
            record = ContactMessage.objects.create(name=data["name"], email=data["email"], subject=data["subject"], message=data["message"])
            destination = SiteSettings.current().contact_email or settings.DEFAULT_FROM_EMAIL
            try:
                email = branded_email(
                    f"New contact message: {record.subject}", "contact_notification", destination,
                    {"subject": record.subject, "sender_name": record.name, "sender_email": record.email, "message": record.message},
                    reply_to=[record.email], fail_silently=False,
                )
                sent = email
                record.email_sent = bool(sent)
                record.save(update_fields=["email_sent", "updated_at"])
            except Exception:
                logging.getLogger(__name__).exception("Contact notification could not be sent for message %s", record.pk)
        messages.success(request, "Thanks for reaching out. Your message has been received, and our team will follow up by email.")
        return redirect("contact")
    return render(request, "core/contact.html", {"form": form})


@staff_member_required(login_url="login")
def admin_home(request):
    users = get_user_model().objects.annotate(quest_total=Count("quests", distinct=True)).order_by("-date_joined")[:8]
    return render(request, "core/admin_home.html", {"users": users, "user_count": get_user_model().objects.count(), "quest_count": Quest.objects.count(), "certificate_count": Certificate.objects.count()})


@staff_member_required(login_url="login")
def admin_users(request):
    users = get_user_model().objects.annotate(quest_total=Count("quests", distinct=True)).order_by("-date_joined")
    query = request.GET.get("q", "").strip()
    if query:
        from django.db.models import Q
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    return render(request, "core/admin_users.html", {"users": users[:100], "query": query})


@staff_member_required(login_url="login")
def admin_user_edit(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    user = get_object_or_404(get_user_model(), pk=pk)
    form = AdminUserForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        if user.pk == request.user.pk and (not user.is_staff or not user.is_superuser or not user.is_active):
            form.add_error(None, "You cannot remove your own admin access.")
        else:
            try:
                user.avatar_url = media_value(form.cleaned_data.get("avatar_upload"), form.cleaned_data.get("avatar_url"), f"studyquest/avatars/{user.pk}")
            except Exception as exc:
                form.add_error("avatar_upload", str(exc))
            else:
                if form.cleaned_data.get("new_password"):
                    user.set_password(form.cleaned_data["new_password"])
                user.save()
                messages.success(request, "User updated.")
                return redirect("admin_users")
    return render(request, "core/admin_user_edit.html", {"form": form, "edited_user": user})


@staff_member_required(login_url="login")
@require_POST
def admin_user_delete(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    user = get_object_or_404(get_user_model(), pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, "You cannot delete your own owner account.")
    else:
        username = user.username
        user.delete()
        messages.success(request, f"User {username} and their associated learning data were deleted.")
    return redirect("admin_users")


@staff_member_required(login_url="login")
def admin_settings(request):
    settings_obj = SiteSettings.current()
    form = SettingsForm(request.POST or None, request.FILES or None, instance=settings_obj)
    if request.method == "POST" and form.is_valid():
        settings_obj = form.save(commit=False)
        try:
            settings_obj.logo_url = media_value(form.cleaned_data.get("logo_upload"), form.cleaned_data.get("logo_url"), "studyquest/branding")
            if form.cleaned_data.get("auth_image_upload"):
                settings_obj.auth_image_url = media_value(form.cleaned_data["auth_image_upload"], "", "studyquest/branding/auth")
        except Exception as exc:
            form.add_error(None, str(exc))
        else:
            settings_obj.save()
            messages.success(request, "Site settings updated.")
            return redirect("admin_settings")
    return render(request, "core/admin_settings.html", {"form": form})


@staff_member_required(login_url="login")
def admin_integrations(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    current = IntegrationSettings.current()
    initial = {"cloudinary_cloud_name": current.cloudinary_cloud_name or integration_value("CLOUDINARY_CLOUD_NAME"), "email_host_user": current.email_host_user or integration_value("EMAIL_HOST_USER")}
    form = IntegrationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        for field in form.fields:
            value = form.cleaned_data.get(field)
            if value:
                setattr(current, field, encrypt(value) if field.upper() in SECRET_FIELDS else value)
        current.save()
        messages.success(request, "Service credentials updated. Blank fields kept their existing values.")
        return redirect("admin_integrations")
    statuses = [(name.replace("_", " ").title(), bool(integration_value(name))) for name in FIELD_MAP]
    return render(request, "core/admin_integrations.html", {"form": form, "statuses": statuses})


@staff_member_required(login_url="login")
def admin_hero_slides(request):
    slides = HeroSlide.objects.all()
    return render(request, "core/admin_hero_slides.html", {"slides": slides, "can_add": slides.count() < 3})


@staff_member_required(login_url="login")
def admin_hero_slide_form(request, pk=None):
    if pk is None and HeroSlide.objects.count() >= 3:
        messages.error(request, "The home hero supports up to three slides. Edit or remove a slide first.")
        return redirect("admin_hero_slides")
    slide = get_object_or_404(HeroSlide, pk=pk) if pk is not None else None
    form = HeroSlideForm(request.POST or None, request.FILES or None, instance=slide)
    if request.method == "POST" and form.is_valid():
        slide = form.save(commit=False)
        upload = form.cleaned_data.get("media_upload")
        try:
            if upload:
                slide.media_url = media_value(upload, "", f"studyquest/hero/slide-{slide.position}", kind="visual")
            elif slide.media_type == "none":
                slide.media_url = ""
        except Exception as exc:
            form.add_error("media_upload", str(exc))
        else:
            slide.save()
            messages.success(request, "Home hero slide saved.")
            return redirect("admin_hero_slides")
    return render(request, "core/admin_hero_slide_form.html", {"form": form, "slide": slide})


@staff_member_required(login_url="login")
@require_POST
def admin_hero_slide_delete(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    slide.delete()
    messages.success(request, "Hero slide removed.")
    return redirect("admin_hero_slides")


@staff_member_required(login_url="login")
def admin_contact_messages(request):
    status = request.GET.get("status", "")
    inbox = ContactMessage.objects.all()
    if status in dict(ContactMessage.STATUS_CHOICES):
        inbox = inbox.filter(status=status)
    return render(request, "core/admin_contact_messages.html", {"inbox": inbox[:100], "status_filter": status, "statuses": ContactMessage.STATUS_CHOICES})


@staff_member_required(login_url="login")
@require_POST
def admin_contact_status(request, pk):
    record = get_object_or_404(ContactMessage, pk=pk)
    status = request.POST.get("status")
    if status in dict(ContactMessage.STATUS_CHOICES):
        record.status = status
        record.save(update_fields=["status", "updated_at"])
        messages.success(request, "Contact message status updated.")
    return redirect("admin_contact_messages")
