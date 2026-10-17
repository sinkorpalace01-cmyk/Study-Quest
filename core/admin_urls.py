from django.urls import path
from . import views

urlpatterns = [
    path("", views.admin_home, name="admin_home"),
    path("users/", views.admin_users, name="admin_users"),
    path("users/<int:pk>/", views.admin_user_edit, name="admin_user_edit"),
    path("users/<int:pk>/delete/", views.admin_user_delete, name="admin_user_delete"),
    path("settings/", views.admin_settings, name="admin_settings"),
    path("integrations/", views.admin_integrations, name="admin_integrations"),
    path("hero/", views.admin_hero_slides, name="admin_hero_slides"),
    path("hero/new/", views.admin_hero_slide_form, name="admin_hero_slide_new"),
    path("hero/<int:pk>/", views.admin_hero_slide_form, name="admin_hero_slide_edit"),
    path("hero/<int:pk>/delete/", views.admin_hero_slide_delete, name="admin_hero_slide_delete"),
    path("contact/", views.admin_contact_messages, name="admin_contact_messages"),
    path("contact/<int:pk>/status/", views.admin_contact_status, name="admin_contact_status"),
]
