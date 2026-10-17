from django.contrib import admin
from .models import Attempt, Badge, Level, Question, Quest, UserBadge

for model in (Quest, Level, Question, Attempt, Badge, UserBadge):
    admin.site.register(model)
