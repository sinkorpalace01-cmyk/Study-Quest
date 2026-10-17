from django.urls import path
from . import views

urlpatterns = [
    path("", views.notification_list, name="notification_list"),
    path("read/", views.mark_read, name="notification_read"),
    path("clear/", views.notification_clear_all, name="notification_clear_all"),
    path("clear-selected/", views.notification_clear_selected, name="notification_clear_selected"),
    path("<int:pk>/open/", views.notification_open, name="notification_open"),
    path("<int:pk>/delete/", views.notification_delete, name="notification_delete"),
    path("api/", views.notification_api, name="notification_api"),
]
