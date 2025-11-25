from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from properties.models import Property

from .models import Booking
from .serializers import BookingSerializer

# API endpoints (JWT-protected)


class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        property_id = request.data.get("property_id")
        start_at_raw = request.data.get("start_at")
        end_at_raw = request.data.get("end_at")

        start_at = parse_datetime(start_at_raw) if start_at_raw else None
        end_at = parse_datetime(end_at_raw) if end_at_raw else None
        if not start_at or not end_at:
            return Response({"detail": "start_at and end_at are required ISO datetimes."}, status=status.HTTP_400_BAD_REQUEST)
        if timezone.is_naive(start_at):
            start_at = timezone.make_aware(start_at, timezone.get_current_timezone())
        if timezone.is_naive(end_at):
            end_at = timezone.make_aware(end_at, timezone.get_current_timezone())
        if end_at <= start_at:
            return Response({"detail": "end_at must be after start_at."}, status=status.HTTP_400_BAD_REQUEST)

        property_obj = get_object_or_404(
            Property.objects.select_for_update().filter(status=Property.STATUS_ACTIVE),
            id=property_id,
        )
        with transaction.atomic():
            if not property_obj.is_available(start_at, end_at):
                return Response({"detail": "Property is not available for that slot."}, status=status.HTTP_400_BAD_REQUEST)
            total_amount = Decimal(property_obj.price)
            booking = Booking.objects.create(
                user=request.user,
                property=property_obj,
                total_amount=total_amount,
                start_at=start_at,
                end_at=end_at,
                status=Booking.STATUS_PENDING,
            )
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user).select_related("property", "property__category")
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        if booking.status == Booking.STATUS_CANCELED:
            return Response({"detail": "Booking already canceled."}, status=status.HTTP_400_BAD_REQUEST)
        if booking.status == Booking.STATUS_PAID:
            return Response({"detail": "Cannot cancel a paid booking."}, status=status.HTTP_400_BAD_REQUEST)
        booking.cancel()
        return Response({"detail": "Booking canceled."}, status=status.HTTP_200_OK)
