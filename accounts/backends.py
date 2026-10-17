from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Authenticate with the unique email address, ignoring letter case."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = (username or kwargs.get("email") or "").strip()
        if not email or password is None:
            return None
        try:
            user = get_user_model().objects.get(email__iexact=email)
        except (get_user_model().DoesNotExist, get_user_model().MultipleObjectsReturned):
            return None
        return user if user.check_password(password) and self.user_can_authenticate(user) else None
