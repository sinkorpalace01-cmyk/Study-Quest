from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordResetCompleteView,
    PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView,
)
from django.contrib.auth.forms import PasswordResetForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from notifications.models import notify
from core.media import media_value
from core.models import SiteSettings
from core.emailing import branded_email
from .forms import AcceptInvitationForm, EmailAuthenticationForm, InviteForm, ProfileForm, SignupForm
from .models import Invitation


class BrandedPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        context = {**context, "site": SiteSettings.current()}
        return super().send_mail(subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name)


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = SiteSettings.current()
        return context


class BrandedPasswordResetView(PasswordResetView):
    html_email_template_name = "emails/password_reset.html"
    form_class = BrandedPasswordResetForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = SiteSettings.current()
        return context



class BrandedPasswordResetDoneView(PasswordResetDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = SiteSettings.current()
        return context


class BrandedPasswordResetConfirmView(PasswordResetConfirmView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = SiteSettings.current()
        return context


class BrandedPasswordResetCompleteView(PasswordResetCompleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = SiteSettings.current()
        return context


class BrandedPasswordChangeView(PasswordChangeView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = SiteSettings.current()
        return context


class SignOutView(LogoutView):
    pass


def signup(request):
    if not SiteSettings.current().allow_registration:
        messages.error(request, "Registration is currently closed.")
        return redirect("landing")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        notify(user, "Welcome to StudyQuest!", "Create your first quest and begin learning.", "/quests/new/", "welcome")
        if user.email and user.email_notifications:
            try:
                branded_email(f"Welcome to {SiteSettings.current().name}", "welcome", user.email, {"user": user})
            except Exception:
                pass
        messages.success(request, "Welcome to StudyQuest!")
        return redirect("dashboard")
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        try:
            user.avatar_url = media_value(form.cleaned_data.get("avatar_upload"), form.cleaned_data.get("avatar_url"), f"studyquest/avatars/{user.pk}")
        except Exception as exc:
            form.add_error("avatar_upload", str(exc))
        else:
            user.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def delete_account(request):
    if request.method == "POST":
        if request.user.check_password(request.POST.get("password", "")):
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Your account and learning data were deleted.")
            return redirect("landing")
        messages.error(request, "Password did not match.")
    return render(request, "accounts/delete_account.html")


@login_required
def invite(request):
    form = InviteForm(request.POST or None, initial={"role": "learner"})
    if not request.user.is_superuser:
        form.fields.pop("role")
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            form.add_error("email", "An account already uses this email.")
        elif Invitation.objects.filter(email__iexact=email, accepted_at__isnull=True, expires_at__gt=timezone.now()).exists():
            form.add_error("email", "There is already an active invitation for this email.")
        else:
            invitation = form.save(commit=False)
            invitation.email = email
            invitation.invited_by = request.user
            if not request.user.is_superuser:
                invitation.role = "learner"
            invitation.save()
            invite_url = request.build_absolute_uri(reverse("invite_accept", args=[invitation.token]))
            try:
                branded_email(f"You're invited to {SiteSettings.current().name}", "invitation", email, {"invite_url": invite_url, "inviter_name": request.user.get_full_name() or request.user.username})
            except Exception:
                pass
            messages.success(request, "Invitation created. Copy the link below or ask the invitee to check their email.")
            return render(request, "accounts/invite.html", {"form": InviteForm(), "invite_url": invite_url})
    return render(request, "accounts/invite.html", {"form": form})


@require_http_methods(["GET", "POST"])
def invite_accept(request, token):
    invitation = get_object_or_404(Invitation, token=token)
    if not invitation.is_valid:
        return render(request, "accounts/invite_invalid.html", {"invitation": invitation}, status=410)
    form = AcceptInvitationForm(request.POST or None, invitation=invitation)
    if request.method == "POST" and form.is_valid():
        user = get_user_model()(
            username=form.cleaned_data["username"], email=invitation.email,
            first_name=form.cleaned_data["first_name"], last_name=form.cleaned_data["last_name"],
            is_staff=invitation.role == "staff",
        )
        user.set_password(form.cleaned_data["password1"])
        user.save()
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_at"])
        login(request, user)
        notify(user, "Welcome to StudyQuest!", "Your invited account is ready. Start your first quest.", "/quests/new/", "welcome")
        messages.success(request, "Your account is ready. Welcome!")
        return redirect("dashboard")
    return render(request, "accounts/invite_accept.html", {"form": form, "invitation": invitation})
