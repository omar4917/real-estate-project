from decimal import Decimal
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase

from properties.models import Category, Property
from users.models import User


class BookingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="booker@example.com", password="StrongPass123")
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        category = Category.objects.create(name="Residential", slug="res-cat")
        self.property = Property.objects.create(
            name="Ocean View",
            slug="ocean-view",
            description="Nice view",
            location="Beach",
            price=Decimal("500000.00"),
            bedrooms=3,
            bathrooms=3,
            amenities=["balcony"],
            status=Property.STATUS_ACTIVE,
            category=category,
        )
        self.start = timezone.now() + timedelta(days=1)
        self.end = self.start + timedelta(hours=2)

    def test_create_booking(self):
        url = reverse("booking-create")
        resp = self.client.post(
            url,
            {
                "property_id": self.property.id,
                "start_at": self.start.isoformat(),
                "end_at": self.end.isoformat(),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "pending")

    def test_property_unavailable_blocks_booking(self):
        # Create an existing pending booking
        self.client.post(
            reverse("booking-create"),
            {
                "property_id": self.property.id,
                "start_at": self.start.isoformat(),
                "end_at": self.end.isoformat(),
            },
            format="json",
        )
        resp = self.client.post(
            reverse("booking-create"),
            {
                "property_id": self.property.id,
                "start_at": self.start.isoformat(),
                "end_at": self.end.isoformat(),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not available", resp.data["detail"].lower())
