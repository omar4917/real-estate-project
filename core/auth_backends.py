from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrAdminUsernameBackend(ModelBackend):
    """Authenticate using email (primary) or admin_username as a secondary key."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identifier = username or kwargs.get(User.USERNAME_FIELD)
        if not identifier:
            return None
        user = None
        try:
            user = User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(admin_username__iexact=identifier)
            except User.DoesNotExist:
                return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
