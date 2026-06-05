import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "atom_db"

client = None
db = None
MONGODB_CONNECTED = False

if MONGODB_URI:
    try:
        # Establish connection with 4-second timeout to fail fast if offline
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
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
    print("[INFO] DATABASE: MONGODB_URI not set. Using local file-based storage.")
