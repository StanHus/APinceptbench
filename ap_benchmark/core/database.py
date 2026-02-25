"""
MongoDB Connection - Singleton Client with Connection Pooling

Provides connection to the ap_social_studies MongoDB database for fetching
curriculum facts during evaluation.

Environment Variables:
    MONGODB_URI: MongoDB connection string (mongodb+srv://...)
"""

import atexit
import logging
import os
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

# Singleton client instance
_mongo_client: Optional[MongoClient] = None

# Database and collection names
DATABASE_NAME = "ap_social_studies"
FACTS_COLLECTION = "facts"


def get_mongo_client() -> Optional[MongoClient]:
    """
    Get or create singleton MongoDB client.

    Uses MONGODB_URI environment variable for connection.
    Returns None if MONGODB_URI is not set or connection fails.
    """
    global _mongo_client

    if _mongo_client is not None:
        return _mongo_client

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        logger.warning("MONGODB_URI environment variable not set - MongoDB integration disabled")
        return None

    try:
        _mongo_client = MongoClient(
            uri,
            maxPoolSize=10,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        # Verify connection
        _mongo_client.admin.command('ping')
        logger.info("MongoDB connection established successfully")
        return _mongo_client
    except Exception as e:
        logger.warning(f"Failed to connect to MongoDB: {e}")
        _mongo_client = None
        return None


def get_database() -> Optional[Database]:
    """Get the ap_social_studies database."""
    client = get_mongo_client()
    if client is None:
        return None
    return client[DATABASE_NAME]


def get_facts_collection() -> Optional[Collection]:
    """Get the facts collection from ap_social_studies database."""
    db = get_database()
    if db is None:
        return None
    return db[FACTS_COLLECTION]


def close_connection() -> None:
    """Close the MongoDB connection."""
    global _mongo_client
    if _mongo_client is not None:
        try:
            _mongo_client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.warning(f"Error closing MongoDB connection: {e}")
        finally:
            _mongo_client = None


def is_connected() -> bool:
    """Check if MongoDB is connected and responsive."""
    client = get_mongo_client()
    if client is None:
        return False
    try:
        client.admin.command('ping')
        return True
    except Exception:
        return False


# Register cleanup on exit
atexit.register(close_connection)
