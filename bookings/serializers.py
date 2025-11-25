from rest_framework import serializers

from properties.serializers import PropertySummarySerializer

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    property = PropertySummarySerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ("id", "property", "total_amount", "start_at", "end_at", "status", "created_at", "updated_at")
        read_only_fields = fields
