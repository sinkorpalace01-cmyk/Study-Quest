from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("studyquest_core", "0004_alter_heroslide_media_url")]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="auth_image_url",
            field=models.CharField(blank=True, default="/static/images/learning-auth.png", max_length=500),
        ),
    ]
