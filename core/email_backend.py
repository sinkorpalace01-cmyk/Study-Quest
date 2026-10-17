from django.core.mail.backends.smtp import EmailBackend
from .integrations import integration_value


class DynamicSMTPBackend(EmailBackend):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("username", integration_value("EMAIL_HOST_USER"))
        kwargs.setdefault("password", integration_value("EMAIL_HOST_PASSWORD"))
        super().__init__(*args, **kwargs)
