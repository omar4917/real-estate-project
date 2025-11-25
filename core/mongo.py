from functools import lru_cache

from django.conf import settings

try:
    from pymongo import MongoClient
except Exception:  # pragma: no cover - pymongo import guard
    MongoClient = None


@lru_cache
def get_mongo_client():
    if not MongoClient:
        return None
    if not settings.MONGO_URI:
        return None
    try:
        return MongoClient(settings.MONGO_URI)
    except Exception:
        return None


def get_media_collection():
    client = get_mongo_client()
    if not client:
        return None
    db_name = settings.MONGO_DB_NAME or "realestate_media"
    return client[db_name]["property_media"]
