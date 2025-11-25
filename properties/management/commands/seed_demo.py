from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from properties.models import Category, Property


class Command(BaseCommand):
    help = "Seed demo data: admin user, categories, and properties."

    def handle(self, *args, **options):
        User = get_user_model()
        admin_email = "admin@example.com"
        admin_password = "Admin123!"
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(email=admin_email, password=admin_password)
            self.stdout.write(self.style.SUCCESS(f"Created admin user {admin_email}/{admin_password}"))
        else:
            self.stdout.write("Admin user already exists.")

        categories = [
            ("Residential", "residential"),
            ("Commercial", "commercial"),
            ("Luxury Villas", "luxury-villas", "residential"),
        ]

        slug_to_obj = {}
        for entry in categories:
            name, slug = entry[0], entry[1]
            parent_slug = entry[2] if len(entry) > 2 else None
            parent = slug_to_obj.get(parent_slug)
            obj, created = Category.objects.get_or_create(name=name, slug=slug, defaults={"parent": parent})
            if created and parent:
                obj.parent = parent
                obj.save(update_fields=["parent"])
            slug_to_obj[slug] = obj
            self.stdout.write(f"{'Created' if created else 'Existing'} category: {name}")

        properties = [
            {
                "name": "Glass Sky Villa",
                "slug": "glass-sky-villa",
                "description": "Panoramic skyline views with infinity pool.",
                "location": "Dubai Marina",
                "price": Decimal("2500000.00"),
                "bedrooms": 6,
                "bathrooms": 7,
                "amenities": ["infinity pool", "private cinema", "smart home"],
                "category_slug": "luxury-villas",
            },
            {
                "name": "Penthouse Central",
                "slug": "penthouse-central",
                "description": "Top floor penthouse with concierge service.",
                "location": "New York",
                "price": Decimal("3200000.00"),
                "bedrooms": 4,
                "bathrooms": 5,
                "amenities": ["concierge", "rooftop deck"],
                "category_slug": "residential",
            },
        ]

        for prop in properties:
            category = slug_to_obj.get(prop["category_slug"])
            if not category:
                self.stdout.write(self.style.WARNING(f"Skipping property {prop['name']}: category missing"))
                continue
            obj, created = Property.objects.get_or_create(
                slug=prop["slug"],
                defaults={
                    "name": prop["name"],
                    "description": prop["description"],
                    "location": prop["location"],
                    "price": prop["price"],
                    "bedrooms": prop["bedrooms"],
                    "bathrooms": prop["bathrooms"],
                    "amenities": prop["amenities"],
                    "status": Property.STATUS_ACTIVE,
                    "category": category,
                },
            )
            self.stdout.write(f"{'Created' if created else 'Existing'} property: {obj.name}")

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
