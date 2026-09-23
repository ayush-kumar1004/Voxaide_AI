import os
from typing import Optional, Any
from app.core.logging import logger

_firestore_client = None

def get_firestore_client():
    """Returns the initialized Firebase Firestore client if available."""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    if os.environ.get("APP_ENV") == "testing":
        return None

    try:
        from firebase_admin import firestore
        _firestore_client = firestore.client()
        return _firestore_client
    except Exception as e:
        logger.warning("Could not initialize live Firestore client", error=str(e))
        return None
