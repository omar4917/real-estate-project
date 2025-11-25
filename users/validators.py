import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexityValidator:
    """
    Enforce at least one uppercase, one lowercase, one digit, and minimum length handled separately.
    """

    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password or ""):
            raise ValidationError(_("Password must contain at least one uppercase letter."))
        if not re.search(r"[a-z]", password or ""):
            raise ValidationError(_("Password must contain at least one lowercase letter."))
        if not re.search(r"\d", password or ""):
            raise ValidationError(_("Password must contain at least one digit."))

    def get_help_text(self):
        return _("Password must include uppercase, lowercase letters and a digit.")
