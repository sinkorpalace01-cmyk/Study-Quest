from django import forms
from .models import HeroSlide, SiteSettings


class SettingsForm(forms.ModelForm):
    logo_upload = forms.ImageField(required=False)
    auth_image_upload = forms.ImageField(required=False, label="Authentication and contact image upload")

    class Meta:
        model = SiteSettings
        fields = ("name", "tagline", "description", "logo_url", "auth_image_url", "contact_email", "contact_phone", "contact_address", "support_url", "accent_color", "footer_text", "allow_registration")
        widgets = {"description": forms.Textarea(attrs={"rows": 4}), "accent_color": forms.TextInput(attrs={"type": "color"})}
        labels = {"auth_image_url": "Authentication and contact image URL"}
        help_texts = {"auth_image_url": "Use an image URL, or upload a replacement below. This appears on login, signup, password reset, invitation, and contact pages."}

    def clean_auth_image_url(self):
        value = self.cleaned_data["auth_image_url"]
        if value and not value.startswith(("https://", "http://", "/static/images/")):
            raise forms.ValidationError("Use an http(s) image URL or the provided /static/images/ image.")
        return value


class IntegrationForm(forms.Form):
    cloudinary_cloud_name = forms.CharField(required=False, max_length=100)
    cloudinary_api_key = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False))
    cloudinary_api_secret = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False))
    gemini_api_key = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False))
    groq_api_key = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False))
    email_host_user = forms.EmailField(required=False)
    email_host_password = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False))


class HeroSlideForm(forms.ModelForm):
    media_upload = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"accept": "image/*,video/*"}))
    title = forms.CharField(max_length=72)
    body = forms.CharField(max_length=150, widget=forms.Textarea(attrs={"rows": 3}))
    cta_text = forms.CharField(max_length=28)

    class Meta:
        model = HeroSlide
        fields = ("position", "is_active", "eyebrow", "title", "body", "media_type", "media_url", "cta_text", "cta_url")
        widgets = {"cta_url": forms.TextInput(attrs={"placeholder": "/accounts/signup/ or https://…"})}

    def clean(self):
        data = super().clean()
        media_type = data.get("media_type")
        upload = data.get("media_upload")
        media_url = data.get("media_url")
        if media_type in ("image", "video") and not (upload or media_url):
            self.add_error("media_upload", "Choose a file to upload or provide a media URL.")
        if upload:
            if media_type not in ("image", "video"):
                self.add_error("media_upload", "Choose Image or Video as the media type for an upload.")
            else:
                expected = "image/" if media_type == "image" else "video/"
                if not (upload.content_type or "").startswith(expected):
                    self.add_error("media_upload", f"Upload a {media_type} file for this slide.")
            if upload.size > 10 * 1024 * 1024:
                self.add_error("media_upload", "Files must be 10 MB or smaller.")
        media_url = data.get("media_url", "")
        if media_url and not media_url.startswith(("https://", "http://", "/static/images/")):
            self.add_error("media_url", "Use a complete http(s) URL or an existing /static/images/ path.")
        position = data.get("position")
        if position and not 1 <= position <= 3:
            self.add_error("position", "Hero slides can be placed from 1 to 3.")
        if position and HeroSlide.objects.filter(position=position).exclude(pk=self.instance.pk).exists():
            self.add_error("position", "That slide position is already in use.")
        cta_url = data.get("cta_url", "")
        if cta_url and not cta_url.startswith("/") and not cta_url.startswith(("https://", "http://")):
            self.add_error("cta_url", "Use a site path beginning with / or a complete http(s) URL.")
        return data


class ContactForm(forms.Form):
    name = forms.CharField(max_length=120, label="Your name")
    email = forms.EmailField(label="Email address")
    subject = forms.CharField(max_length=180)
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}), max_length=5000)
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="Leave this field empty")

    def clean_website(self):
        return self.cleaned_data.get("website", "")
