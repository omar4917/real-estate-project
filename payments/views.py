from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking
from .models import Payment
from .services import BkashPaymentStrategy, StripePaymentStrategy, get_payment_strategy

# API endpoints (payments)


class PaymentInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        provider = str(request.data.get("provider", "")).lower()
        booking_id = request.data.get("booking_id")

        if provider not in (Payment.PROVIDER_STRIPE, Payment.PROVIDER_BKASH):
            return Response({"detail": "Invalid provider."}, status=status.HTTP_400_BAD_REQUEST)
        if not booking_id:
            return Response({"detail": "booking_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            booking = get_object_or_404(
                Booking.objects.select_for_update(),
                id=booking_id,
                user=request.user,
            )
            if booking.status == Booking.STATUS_PAID:
                return Response({"detail": "Booking already paid."}, status=status.HTTP_400_BAD_REQUEST)

            # Guard against duplicate payments for the same booking/provider.
            existing_success = Payment.objects.filter(booking=booking, status=Payment.STATUS_SUCCESS).exists()
            if existing_success:
                return Response({"detail": "Payment already completed for this booking."}, status=status.HTTP_400_BAD_REQUEST)

            existing_pending = (
                Payment.objects.filter(booking=booking, provider=provider, status=Payment.STATUS_PENDING)
                .order_by("-created_at")
                .first()
            )
            if existing_pending:
                data = {
                    "payment_id": existing_pending.id,
                    "provider": existing_pending.provider,
                    "transaction_id": existing_pending.transaction_id,
                    "status": existing_pending.status,
                }
                if provider == Payment.PROVIDER_STRIPE:
                    client_secret = existing_pending.raw_response.get("client_secret") if isinstance(
                        existing_pending.raw_response, dict
                    ) else None
                    data["client_secret"] = client_secret
                if provider == Payment.PROVIDER_BKASH:
                    data["bkash_payment_id"] = existing_pending.transaction_id
                return Response(data, status=status.HTTP_200_OK)

            strategy = get_payment_strategy(provider)
            try:
                data = strategy.initiate(booking, request)
            except Exception as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_201_CREATED)


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body.decode("utf-8")
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        strategy = StripePaymentStrategy()
        try:
            data = strategy.handle_webhook(payload, sig_header)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)


class BkashWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body.decode("utf-8")
        strategy = BkashPaymentStrategy()
        try:
            data = strategy.handle_webhook(payload, request.META.get("HTTP_X_SIGNATURE", ""))
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)


class BkashExecuteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get("payment_id")
        if not payment_id:
            return Response({"detail": "payment_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        payment = get_object_or_404(
            Payment.objects.select_related("booking"),
            id=payment_id,
            provider=Payment.PROVIDER_BKASH,
            booking__user=request.user,
        )
        strategy = BkashPaymentStrategy()
        try:
            data, status_flag = strategy.execute_payment(payment.transaction_id)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": status_flag, "raw": data}, status=status.HTTP_200_OK)


class BkashQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_id = request.query_params.get("payment_id")
        if not payment_id:
            return Response({"detail": "payment_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        payment = get_object_or_404(
            Payment.objects.select_related("booking"),
            id=payment_id,
            provider=Payment.PROVIDER_BKASH,
            booking__user=request.user,
        )
        strategy = BkashPaymentStrategy()
        try:
            data = strategy.query_payment(payment.transaction_id)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)
