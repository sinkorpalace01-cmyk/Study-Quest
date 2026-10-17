from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from accounts import views as account_views
from core import views as core_views
from quests import views as quest_views
from certificates import views as certificate_views

urlpatterns = [
    path("", core_views.landing, name="landing"),
    path("contact/", core_views.contact, name="contact"),
    path("dashboard/", quest_views.dashboard, name="dashboard"),
    path("accounts/", include("accounts.urls")),
    path("quests/", include("quests.urls")),
    path("certificates/", include("certificates.urls")),
    path("notifications/", include("notifications.urls")),
    path("leaderboard/", quest_views.leaderboard, name="leaderboard"),
    path("admin/", include("core.admin_urls")),
    path("verify/<str:code>/", certificate_views.verify, name="certificate_verify"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
