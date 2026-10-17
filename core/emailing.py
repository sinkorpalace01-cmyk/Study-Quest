from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .integrations import integration_value
from .models import SiteSettings


def branded_email(subject, template, recipient, context=None, *, attachments=(), reply_to=(), fail_silently=True):
    """Send a responsive branded email with a readable text alternative."""
    site = SiteSettings.current()
    data = {"site": site, "site_url": settings.SITE_URL, **(context or {})}
    plain = render_to_string(f"emails/{template}.txt", data)
    html = render_to_string(f"emails/{template}.html", data)
    address = integration_value("EMAIL_HOST_USER")
    sender = f"{site.name} <{address}>" if address else settings.DEFAULT_FROM_EMAIL
    message = EmailMultiAlternatives(subject, plain, sender, [recipient])
    message.attach_alternative(html, "text/html")
    message.reply_to = list(reply_to)
    for filename, content, mimetype in attachments:
        message.attach(filename, content, mimetype)
    return message.send(fail_silently=fail_silently)
