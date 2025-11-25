from django import forms
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


class EmailAdminAuthenticationForm(AdminAuthenticationForm):
    """Use email for the admin login form field label/input type."""

    username = forms.EmailField(
        label=_("Email or username"),
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "admin_username", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("email", "admin_username", "password")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "admin_username", "password1", "password2", "is_staff", "is_superuser", "is_active"),
            },
        ),
    )
    search_fields = ("email", "admin_username")
    filter_horizontal = ("groups", "user_permissions")


# Make admin login form show an email field
admin.site.login_form = EmailAdminAuthenticationForm
