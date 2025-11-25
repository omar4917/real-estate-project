from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "booking_id",
            "provider",
            "transaction_id",
            "status",
            "raw_response",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
