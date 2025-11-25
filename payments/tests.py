import json
from decimal import Decimal
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from bookings.models import Booking
from payments.models import Payment
from properties.models import Category, Property
from users.models import User


class StripeWebhookTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(email="stripe@example.com", password="StrongPass123")
        self.token = RefreshToken.for_user(user).access_token
        category = Category.objects.create(name="Residential", slug="stripe-res")
        property_obj = Property.objects.create(
            name="Penthouse",
            slug="penthouse",
            description="Top floor",
            location="City",
            price=Decimal("750000.00"),
            bedrooms=4,
            bathrooms=4,
            amenities=[],
            status=Property.STATUS_ACTIVE,
            category=category,
        )
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(hours=1)
        self.booking = Booking.objects.create(
            user=user,
            property=property_obj,
            total_amount=property_obj.price,
            start_at=start,
            end_at=end,
            status=Booking.STATUS_PENDING,
        )
        self.payment = Payment.objects.create(
            booking=self.booking,
            provider=Payment.PROVIDER_STRIPE,
            transaction_id="pi_test_123",
            status=Payment.STATUS_PENDING,
            raw_response={},
        )

    def test_stripe_webhook_marks_payment_and_booking_paid(self):
        url = reverse("stripe-webhook")
        payload = json.dumps(
            {
                "type": "payment_intent.succeeded",
                "data": {"object": {"id": self.payment.transaction_id, "object": "payment_intent"}},
            }
        )
        resp = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(self.booking.status, Booking.STATUS_PAID)

    def test_initiate_reuses_pending_payment(self):
        # Seed a pending payment with client_secret
        self.payment.raw_response = {"client_secret": "secret_123"}
        self.payment.save(update_fields=["raw_response"])

        url = reverse("payment-initiate")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        resp = self.client.post(
            url,
            {"provider": Payment.PROVIDER_STRIPE, "booking_id": self.booking.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["payment_id"], self.payment.id)
        self.assertEqual(resp.data["client_secret"], "secret_123")
