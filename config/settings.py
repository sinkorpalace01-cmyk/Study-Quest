import os
from pathlib import Path

import certifi
import pymysql
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-local-development-only")
DEBUG = os.getenv("DEBUG", "0") == "1"
if not DEBUG and SECRET_KEY == "insecure-local-development-only":
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production")
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,.vercel.app").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "https://*.vercel.app").split(",") if origin.strip()]
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000").rstrip("/")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "core.apps.CoreConfig",
    "quests.apps.QuestsConfig",
    "certificates.apps.CertificatesConfig",
    "notifications.apps.NotificationsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.site",
        "notifications.context_processors.unread_count",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"

if all(os.getenv(name) for name in ("TIDB_HOST", "TIDB_USER", "TIDB_PASSWORD", "TIDB_DATABASE")):
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["TIDB_DATABASE"],
        "USER": os.environ["TIDB_USER"],
        "PASSWORD": os.environ["TIDB_PASSWORD"],
        "HOST": os.environ["TIDB_HOST"],
        "PORT": os.getenv("TIDB_PORT", "4000"),
        "OPTIONS": {
            "ssl": {"ca": certifi.where()},
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "charset": "utf8mb4",
        },
        "CONN_MAX_AGE": 0,
    }}
else:
    if not DEBUG:
        raise ImproperlyConfigured("TiDB credentials are required in production")
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_USER_MODEL = "studyquest_accounts.User"
AUTHENTICATION_BACKENDS = ["accounts.backends.EmailBackend"]
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "landing"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Monrovia"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_BACKEND = (
    "core.email_backend.DynamicSMTPBackend"
    if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
    else "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = f"StudyQuest <{EMAIL_HOST_USER or 'noreply@localhost'}>"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
