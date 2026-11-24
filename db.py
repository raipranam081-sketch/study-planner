import logging
from pymongo import MongoClient, ASCENDING
from bson import ObjectId
import mongomock
from config import Config

logger = logging.getLogger(__name__)

_db_instance = None
_client_instance = None
_is_mock = False

def get_db():
    """
    Returns the active MongoDB database instance.
    Attempts to connect to the real MongoDB instance defined in MONGO_URI.
    Falls back gracefully to mongomock if MongoDB is unreachable and fallback is allowed.
    """
    global _db_instance, _client_instance, _is_mock
    
    if _db_instance is not None:
        return _db_instance

    try:
        # Attempt connection to real MongoDB with 2000ms timeout
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=2000)
        # Test connection
        client.admin.command('ping')
        _client_instance = client
        _db_instance = client[Config.DB_NAME]
        _is_mock = False
        logger.info(f"Connected successfully to real MongoDB at {Config.MONGO_URI}")
    except Exception as e:
        if Config.USE_MOCK_IF_NO_MONGO:
            logger.warning(
                f"Could not connect to MongoDB server ({e}). "
                f"Falling back to in-memory mongomock database for seamless offline operation."
            )
            _client_instance = mongomock.MongoClient()
            _db_instance = _client_instance[Config.DB_NAME]
            _is_mock = True
        else:
            raise ConnectionError(f"Failed to connect to MongoDB server at {Config.MONGO_URI}: {e}")

    _init_indexes(_db_instance)
    return _db_instance

def is_database_mock():
    """Returns True if running on in-memory mock MongoDB, False if real MongoDB."""
    global _is_mock
    return _is_mock

def _init_indexes(db):
    """Initializes indexes for the collections to ensure high performance and integrity."""
    try:
        # Index users by email (unique)
        db.users.create_index([("email", ASCENDING)], unique=True)
        # Index subjects, tasks, study_sessions, study_plans by user_id
        db.subjects.create_index([("user_id", ASCENDING)])
        db.tasks.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
        db.study_sessions.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
        db.study_plans.create_index([("user_id", ASCENDING)])
    except Exception as e:
        logger.warning(f"Note on index creation: {e}")

def to_object_id(id_str):
    """Safely converts string to BSON ObjectId."""
    try:
        if isinstance(id_str, ObjectId):
            return id_str
        return ObjectId(str(id_str))
    except Exception:
        return None
