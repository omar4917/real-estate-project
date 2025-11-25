import json
from abc import ABC, abstractmethod

import requests
import stripe
from django.conf import settings
from django.db import transaction

from bookings.models import Booking
from .models import Payment


class PaymentStrategy(ABC):
    provider: str

    @abstractmethod
    def initiate(self, booking, request=None):
        raise NotImplementedError

    def handle_webhook(self, payload, sig_header):
        raise NotImplementedError


class StripePaymentStrategy(PaymentStrategy):
    provider = Payment.PROVIDER_STRIPE

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def initiate(self, booking, request=None):
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe secret key not configured.")

        intent = stripe.PaymentIntent.create(
            amount=int(booking.total_amount * 100),
            currency="usd",
            metadata={"booking_id": booking.id, "user_id": booking.user_id},
        )
        payment = Payment.objects.create(
            booking=booking,
            provider=self.provider,
            transaction_id=intent.id,
            status=Payment.STATUS_PENDING,
            raw_response=intent.to_dict_recursive(),
        )
        return {
            "payment_id": payment.id,
            "provider": self.provider,
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "status": payment.status,
        }

    def handle_webhook(self, payload, sig_header):
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        try:
            if webhook_secret:
                event = stripe.Webhook.construct_event(
                    payload=payload, sig_header=sig_header, secret=webhook_secret
                )
            else:
                event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
        except Exception as exc:
            raise ValueError(f"Invalid Stripe webhook: {exc}")

        event_type = event["type"]
        data_object = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            self._mark_payment(data_object["id"], Payment.STATUS_SUCCESS, data_object)
        elif event_type == "payment_intent.payment_failed":
            self._mark_payment(data_object["id"], Payment.STATUS_FAILED, data_object)

        return {"received": True}

    def _mark_payment(self, transaction_id, status, raw):
        payment = (
            Payment.objects.select_related("booking")
            .filter(transaction_id=transaction_id, provider=self.provider)
            .first()
        )
        if not payment:
            return

        with transaction.atomic():
            payment.status = status
            payment.raw_response = raw
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            if status == Payment.STATUS_SUCCESS:
                Booking.objects.filter(id=payment.booking_id).update(status=Booking.STATUS_PAID)


class BkashPaymentStrategy(PaymentStrategy):
    provider = Payment.PROVIDER_BKASH

    def __init__(self):
        self.base_url = (settings.BKASH_BASE_URL or "").rstrip("/")
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username = settings.BKASH_USERNAME
        self.password = settings.BKASH_PASSWORD

    def _has_credentials(self):
        return all([self.base_url, self.app_key, self.app_secret, self.username, self.password])

    def _get_token(self):
        url = f"{self.base_url}/token/grant"
        payload = {"app_key": self.app_key, "app_secret": self.app_secret}
        headers = {"username": self.username, "password": self.password, "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        token = data.get("id_token")
        if not token:
            raise ValueError("bKash token missing.")
        return token

    def _headers(self, token):
        return {"authorization": token, "x-app-key": self.app_key, "Content-Type": "application/json"}

    def _post(self, path, token, payload):
        url = f"{self.base_url}{path}"
        resp = requests.post(url, json=payload, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _mock_success(self, booking):
        transaction_id = f"bkash-mock-{booking.id}-{booking.payments.count() + 1}"
        with transaction.atomic():
            payment = Payment.objects.create(
                booking=booking,
                provider=self.provider,
                transaction_id=transaction_id,
                status=Payment.STATUS_SUCCESS,
                raw_response={"message": "Mock bKash payment success"},
            )
            Booking.objects.filter(id=booking.id).update(status=Booking.STATUS_PAID)
        return {
            "payment_id": payment.id,
            "provider": self.provider,
            "transaction_id": transaction_id,
            "status": payment.status,
        }

    def initiate(self, booking, request=None):
        if not self._has_credentials():
            return self._mock_success(booking)

        token = self._get_token()
        payload = {
            "mode": "0011",
            "payerReference": str(booking.user_id),
            "callbackURL": request.build_absolute_uri("/api/payments/webhook/bkash/") if request else "",
            "amount": str(booking.total_amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": f"inv-{booking.id}",
        }
        data = self._post("/checkout/payment/create", token, payload)
        payment_id = data.get("paymentID") or f"bkash-{booking.id}-pending"
        with transaction.atomic():
            payment = Payment.objects.create(
                booking=booking,
                provider=self.provider,
                transaction_id=payment_id,
                status=Payment.STATUS_PENDING,
                raw_response=data,
            )
        return {
            "payment_id": payment.id,
            "provider": self.provider,
            "transaction_id": payment_id,
            "bkash_payment_id": payment_id,
            "redirect_url": data.get("bkashURL"),
            "status": payment.status,
        }

    def execute_payment(self, payment_id):
        if not self._has_credentials():
            raise ValueError("bKash credentials not configured.")
        token = self._get_token()
        data = self._post("/checkout/payment/execute", token, {"paymentID": payment_id})
        status = Payment.STATUS_SUCCESS if data.get("transactionStatus") == "Completed" else Payment.STATUS_FAILED
        self._mark_payment(payment_id, status, data)
        return data, status

    def query_payment(self, payment_id):
        if not self._has_credentials():
            raise ValueError("bKash credentials not configured.")
        token = self._get_token()
        data = self._post("/checkout/payment/query", token, {"paymentID": payment_id})
        return data

    def handle_webhook(self, payload, sig_header):
        body = json.loads(payload or "{}")
        payment_id = body.get("paymentID")
        status_flag = body.get("transactionStatus")
        if not payment_id:
            return {"received": False}
        status = Payment.STATUS_SUCCESS if status_flag == "Completed" else Payment.STATUS_FAILED
        self._mark_payment(payment_id, status, body)
        return {"received": True}

    def _mark_payment(self, payment_id, status, raw):
        payment = (
            Payment.objects.select_related("booking")
            .filter(transaction_id=payment_id, provider=self.provider)
            .first()
        )
        if not payment:
            return
        with transaction.atomic():
            payment.status = status
            payment.raw_response = raw
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            if status == Payment.STATUS_SUCCESS:
                Booking.objects.filter(id=payment.booking_id).update(status=Booking.STATUS_PAID)


def get_payment_strategy(provider: str) -> PaymentStrategy:
    if provider == Payment.PROVIDER_STRIPE:
        return StripePaymentStrategy()
    if provider == Payment.PROVIDER_BKASH:
        return BkashPaymentStrategy()
    raise ValueError("Unsupported payment provider")
