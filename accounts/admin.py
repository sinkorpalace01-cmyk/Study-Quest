from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class StudyQuestUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "xp", "streak", "best_streak", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (("StudyQuest", {"fields": ("bio", "avatar_url", "location", "school", "website", "xp", "streak", "best_streak", "last_activity", "email_notifications")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Email", {"fields": ("email",)}),)
