from django.urls import path

from .views import (
    CategoryListView,
    HomePageView,
    PropertyPageView,
    PropertyDetailView,
    PropertyListView,
    PropertyRecommendationsView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("p/<slug:slug>/", PropertyPageView.as_view(), name="property-page"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("properties/", PropertyListView.as_view(), name="property-list"),
    path("properties/<slug:slug>/", PropertyDetailView.as_view(), name="property-detail"),
    path(
        "properties/<slug:slug>/recommendations/",
        PropertyRecommendationsView.as_view(),
        name="property-recommendations",
    ),
]
