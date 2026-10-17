from django.urls import path
from . import views

urlpatterns = [
    path("", views.certificate_list, name="certificate_list"),
    path("<uuid:code>/download/", views.download, name="certificate_download"),
]
