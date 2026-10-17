import base64
import hashlib
import os
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

SECRET_FIELDS = {"CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET", "GEMINI_API_KEY", "GROQ_API_KEY", "EMAIL_HOST_PASSWORD"}
FIELD_MAP = {
    "CLOUDINARY_CLOUD_NAME": "cloudinary_cloud_name",
    "CLOUDINARY_API_KEY": "cloudinary_api_key",
    "CLOUDINARY_API_SECRET": "cloudinary_api_secret",
    "GEMINI_API_KEY": "gemini_api_key",
    "GROQ_API_KEY": "groq_api_key",
    "EMAIL_HOST_USER": "email_host_user",
    "EMAIL_HOST_PASSWORD": "email_host_password",
}


def _cipher():
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt(value):
    return _cipher().encrypt(value.encode()).decode()


def decrypt(value):
    try:
        return _cipher().decrypt(value.encode()).decode()
    except InvalidToken:
        return ""


def integration_value(name):
    field = FIELD_MAP.get(name)
    if field:
        try:
            from .models import IntegrationSettings
            stored = getattr(IntegrationSettings.current(), field)
            if stored:
                return decrypt(stored) if name in SECRET_FIELDS else stored
        except Exception:
            pass
    return os.getenv(name, "")
