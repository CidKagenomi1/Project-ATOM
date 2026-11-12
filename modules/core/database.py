import os
import sys

try:
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False
    MongoClient = None

from dotenv import load_dotenv

load_dotenv()

DB_NAME = "atom_db"

_client = None
_db = None
_mongodb_connected = False
MONGODB_ERROR = None


def get_database():
    """Lazily and dynamically establish and return MongoDB connection."""
    global _client, _db, _mongodb_connected, MONGODB_ERROR
    
    if _db is not None and _mongodb_connected:
        return _db
        
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        MONGODB_ERROR = "MONGODB_URI environment variable is not set."
        _mongodb_connected = False
        return None
        
    if not HAS_PYMONGO:
        MONGODB_ERROR = "pymongo is not installed."
        _mongodb_connected = False
        return None
        
    try:
        if _client is None:
            _client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=10
            )
        # Verify connection
        _client.admin.command('ping')
        _db = _client[DB_NAME]
        _mongodb_connected = True
        MONGODB_ERROR = None
        print("[OK] DATABASE: Connected to MongoDB Cluster successfully.")
        return _db
    except Exception as e:
        _client = None
        _db = None
        _mongodb_connected = False
        MONGODB_ERROR = str(e)
        print(f"[WARN] DATABASE: MongoDB connection failed: {e}. Falling back to local files.")
        return None


class DatabaseProxy:
    """Dynamic proxy for database so imports don't freeze on connection failure."""
    def __getitem__(self, collection_name):
        d = get_database()
        if d is None:
            raise RuntimeError(f"MongoDB not connected: {MONGODB_ERROR}")
        return d[collection_name]
    
    def __getattr__(self, name):
        d = get_database()
        if d is None:
            raise RuntimeError(f"MongoDB not connected: {MONGODB_ERROR}")
        return getattr(d, name)


class ConnectedProxy:
    """Dynamic proxy for MONGODB_CONNECTED boolean check."""
    def __bool__(self):
        return get_database() is not None

    def __repr__(self):
        return str(get_database() is not None)


db = DatabaseProxy()
MONGODB_CONNECTED = ConnectedProxy()
MONGODB_URI = os.getenv("MONGODB_URI")

# Trigger initial lazy attempt
get_database()

