from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    LoginPageView,
    LoginView,
    MeView,
    MyBookingsView,
    MyPaymentsView,
    UserPanelView,
    RegisterPageView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("me/bookings/", MyBookingsView.as_view(), name="auth-me-bookings"),
    path("me/payments/", MyPaymentsView.as_view(), name="auth-me-payments"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("login-page/", LoginPageView.as_view(), name="login-page"),
    path("register-page/", RegisterPageView.as_view(), name="register-page"),
    path("panel/", UserPanelView.as_view(), name="user-panel"),
]
