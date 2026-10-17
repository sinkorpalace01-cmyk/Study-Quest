from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Invitation, User


class UniqueEmailMixin:
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        matches = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise forms.ValidationError("An account already uses this email address.")
        return email


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email address", widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))


class SignupForm(UniqueEmailMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")


class ProfileForm(UniqueEmailMixin, forms.ModelForm):
    avatar_upload = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "bio", "location", "school", "website", "avatar_url", "email_notifications")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}


class AdminUserForm(UniqueEmailMixin, forms.ModelForm):
    avatar_upload = forms.ImageField(required=False)
    new_password = forms.CharField(required=False, widget=forms.PasswordInput, help_text="Leave blank to keep the current password.")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "bio", "location", "school", "website", "avatar_url", "xp", "streak", "best_streak", "last_activity", "email_notifications", "is_active", "is_staff", "is_superuser")
        widgets = {"bio": forms.Textarea(attrs={"rows": 3}), "last_activity": forms.DateInput(attrs={"type": "date"})}


class InviteForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ("email", "role")


class AcceptInvitationForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, invitation, **kwargs):
        self.invitation = invitation
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean(self):
        data = super().clean()
        if data.get("password1") != data.get("password2"):
            self.add_error("password2", "The passwords do not match.")
        if self.invitation.role == "staff" and not self.invitation.invited_by_id:
            self.add_error(None, "This administrator invitation is invalid.")
        return data
