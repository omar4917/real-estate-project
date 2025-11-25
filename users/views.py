from django.views.generic import TemplateView
from django.contrib.auth import login as auth_login
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from bookings.models import Booking
from bookings.serializers import BookingSerializer
from payments.models import Payment
from payments.serializers import PaymentSerializer
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

# API endpoints


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = RefreshToken.for_user(user)
        data = {
            "user": UserSerializer(user).data,
            "refresh": str(token),
            "access": str(token.access_token),
        }
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        # Create session for admin/staff so redirect to /admin works after API login.
        try:
            if not hasattr(user, "backend"):
                user.backend = "core.auth_backends.EmailOrAdminUsernameBackend"
            auth_login(request, user)
        except Exception:
            pass
        token = RefreshToken.for_user(user)
        data = {
            "user": UserSerializer(user).data,
            "refresh": str(token),
            "access": str(token.access_token),
        }
        return Response(data, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class MyBookingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user).select_related("property", "property__category")
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class MyPaymentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(booking__user=request.user).select_related("booking")
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class LoginPageView(TemplateView):
    template_name = "login.html"
    permission_classes = []  # TemplateView; DRF permissions not applied


class RegisterPageView(TemplateView):
    template_name = "register.html"
    permission_classes = []  # TemplateView; DRF permissions not applied


class UserPanelView(TemplateView):
    template_name = "panel.html"
    permission_classes = []
