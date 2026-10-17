from django.urls import path
from . import views

urlpatterns = [
    path("", views.quest_list, name="quest_list"),
    path("new/", views.quest_new, name="quest_new"),
    path("<uuid:pk>/", views.quest_detail, name="quest_detail"),
    path("<uuid:pk>/delete/", views.quest_delete, name="quest_delete"),
    path("level/<int:pk>/", views.level_play, name="level_play"),
    path("level/<int:pk>/submit/", views.level_submit, name="level_submit"),
    path("attempt/<int:pk>/", views.attempt_result, name="attempt_result"),
    path("question/<int:pk>/explain/", views.explain, name="question_explain"),
]
