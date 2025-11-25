from typing import List

from core.mongo import get_media_collection


def list_media(property_id: int) -> List[dict]:
    """
    Fetch media metadata for a property from MongoDB.
    Each document expected to contain: property_id, url, title(optional), type(optional).
    """
    collection = get_media_collection()
    if collection is None:
        return []
    try:
        cursor = collection.find({"property_id": property_id})
        return [{"url": doc.get("url"), "title": doc.get("title"), "type": doc.get("type")} for doc in cursor]
    except Exception:
        return []


def add_media(property_id: int, url: str, title: str = "", media_type: str = "") -> bool:
    """Insert a media record for a property. Returns True if inserted."""
    collection = get_media_collection()
    if collection is None:
        return False
    try:
        collection.insert_one({"property_id": property_id, "url": url, "title": title, "type": media_type})
        return True
    except Exception:
        return False
