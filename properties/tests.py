from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Property


class PropertyPublicTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Residential", slug="residential")
        self.property = Property.objects.create(
            name="Skyline Villa",
            slug="skyline-villa",
            description="Luxury villa",
            location="Downtown",
            price=Decimal("1000000.00"),
            bedrooms=5,
            bathrooms=6,
            amenities=["pool", "gym"],
            status=Property.STATUS_ACTIVE,
            category=self.category,
        )

    def test_list_properties(self):
        url = reverse("property-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["slug"], self.property.slug)

    def test_property_detail(self):
        url = reverse("property-detail", kwargs={"slug": self.property.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], self.property.name)
