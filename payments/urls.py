from django.urls import path

from .views import BkashExecuteView, BkashQueryView, BkashWebhookView, PaymentInitiateView, StripeWebhookView

urlpatterns = [
    path("payments/initiate/", PaymentInitiateView.as_view(), name="payment-initiate"),
    path("payments/webhook/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("payments/webhook/bkash/", BkashWebhookView.as_view(), name="bkash-webhook"),
    path("payments/bkash/execute/", BkashExecuteView.as_view(), name="bkash-execute"),
    path("payments/bkash/query/", BkashQueryView.as_view(), name="bkash-query"),
]
