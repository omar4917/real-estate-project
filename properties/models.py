from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name


class Property(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    amenities = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    category = models.ForeignKey(Category, related_name="properties", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["slug", "status"])]

    def __str__(self):
        return self.name

    def is_available(self, start_at, end_at):
        """Available when no overlapping pending/paid booking exists for the slot."""
        return not self.bookings.filter(
            status__in=["pending", "paid"],
            start_at__lt=end_at,
            end_at__gt=start_at,
        ).exists()
