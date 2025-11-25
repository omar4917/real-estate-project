from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthTests(APITestCase):
    def test_register_returns_tokens_and_user(self):
        payload = {
            "email": "newuser@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "mobile_number": "+1234567890",
        }
        url = reverse("auth-register")
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["email"], payload["email"])

    def test_login_returns_tokens(self):
        user = User.objects.create_user(email="login@example.com", password="StrongPass123")
        url = reverse("auth-login")
        resp = self.client.post(url, {"identifier": user.email, "password": "StrongPass123"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertEqual(resp.data["user"]["email"], user.email)

    def test_me_requires_auth(self):
        User.objects.create_user(email="me@example.com", password="StrongPass123")
        url = reverse("auth-me")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
