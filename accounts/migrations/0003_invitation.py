import uuid

import accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("studyquest_accounts", "0002_user_best_streak"),
    ]

    operations = [
        migrations.CreateModel(
            name="Invitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("email", models.EmailField(max_length=254)),
                ("role", models.CharField(choices=[("learner", "Learner"), ("staff", "Administrator")], default="learner", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(default=accounts.models.invitation_expiry)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("invited_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sent_invitations", to="studyquest_accounts.user")),
            ],
        ),
    ]
