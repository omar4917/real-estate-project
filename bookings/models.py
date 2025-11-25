from django.conf import settings
from django.db import models
from django.utils import timezone


class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELED, "Canceled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bookings", on_delete=models.CASCADE)
    property = models.ForeignKey("properties.Property", related_name="bookings", on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["property", "start_at", "end_at"]),
        ]

    def __str__(self):
        return f"Booking #{self.id} - {self.property}"

    def overlaps(self, start_at, end_at):
        return (
            self.start_at < end_at
            and self.end_at > start_at
        )

    @staticmethod
    def has_overlap(property, start_at, end_at):
        return Booking.objects.filter(
            property=property,
            status__in=[Booking.STATUS_PENDING, Booking.STATUS_PAID],
            start_at__lt=end_at,
            end_at__gt=start_at,
        ).exists()

    def cancel(self):
        self.status = Booking.STATUS_CANCELED
        self.save(update_fields=["status", "updated_at"])
