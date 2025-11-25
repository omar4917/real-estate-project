from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "property", "status", "total_amount", "start_at", "end_at", "created_at")
    list_filter = ("status",)
    search_fields = ("id", "user__email", "property__name")
    raw_id_fields = ("user", "property")
