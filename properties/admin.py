from django.contrib import admin

from .models import Category, Property


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "price", "category", "created_at")
    list_filter = ("status", "category")
    search_fields = ("name", "slug", "location")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("category",)
