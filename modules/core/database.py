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

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "atom_db"

client = None
db = None
MONGODB_CONNECTED = False

if MONGODB_URI and HAS_PYMONGO:
    try:
        # Establish connection with 5-second timeout suitable for cloud/serverless environments (e.g. Vercel)
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        # Verify connection
        client.admin.command('ping')
        db = client[DB_NAME]
        MONGODB_CONNECTED = True
        print("[OK] DATABASE: Connected to MongoDB Cluster successfully.")
    except Exception as e:
        client = None
        db = None
        MONGODB_CONNECTED = False
        print(f"[WARN] DATABASE: MongoDB connection failed: {e}. Falling back to local files.")
else:
    if not HAS_PYMONGO and MONGODB_URI:
        print("[INFO] DATABASE: pymongo not installed. Using local file-based storage.")
    else:
        print("[INFO] DATABASE: MONGODB_URI not set. Using local file-based storage.")

