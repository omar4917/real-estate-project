from django.urls import path

from .views import BookingCancelView, BookingCreateView, BookingListView

urlpatterns = [
    path("bookings/", BookingListView.as_view(), name="booking-list"),
    path("bookings/create/", BookingCreateView.as_view(), name="booking-create"),
    path("bookings/<int:booking_id>/cancel/", BookingCancelView.as_view(), name="booking-cancel"),
]
