from django.db import models


class Payment(models.Model):
    PROVIDER_STRIPE = "stripe"
    PROVIDER_BKASH = "bkash"
    PROVIDER_CHOICES = [
        (PROVIDER_STRIPE, "Stripe"),
        (PROVIDER_BKASH, "bKash"),
    ]

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    booking = models.ForeignKey("bookings.Booking", related_name="payments", on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["provider"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Payment #{self.id} - {self.provider}"
