from rest_framework import serializers

from .models import Category, Property
from .media_service import list_media


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent")
        read_only_fields = fields


class PropertySummarySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Property
        fields = ("id", "name", "slug", "location", "price", "status", "category")
        read_only_fields = fields


class PropertyDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    media = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "location",
            "price",
            "bedrooms",
            "bathrooms",
            "amenities",
            "status",
            "category",
            "media",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_media(self, obj):
        return list_media(obj.id)
