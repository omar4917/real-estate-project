"""
URL configuration for realestate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from users.views import LoginPageView, RegisterPageView, UserPanelView
from properties.views import HomePageView, PropertyPageView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('api/', include('properties.urls')),
    path('api/', include('bookings.urls')),
    path('api/', include('payments.urls')),
    path('login/', LoginPageView.as_view(), name='login-page-root'),
    path('register/', RegisterPageView.as_view(), name='register-page-root'),
    path('panel/', UserPanelView.as_view(), name='user-panel-root'),
    path('auth/password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('auth/password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('auth/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('auth/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('', HomePageView.as_view(), name='home-page-root'),
    path('p/<slug:slug>/', PropertyPageView.as_view(), name='property-page-root'),
]
