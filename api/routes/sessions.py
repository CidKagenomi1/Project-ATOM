import os
from fastapi import APIRouter
from api.schemas import SessionsPayload
from api.utils import safe_load_json, safe_save_json, safe_print

try:
    from modules.core.database import db, MONGODB_CONNECTED
except Exception as e:
    db = None
    MONGODB_CONNECTED = False

CHAT_SESSIONS_FILE = "data/atom_chat_sessions.json"

router = APIRouter()

@router.get("/sessions/chat")
async def get_chat_sessions():
    """Retrieve chat history and sessions from database or local project file."""
    if MONGODB_CONNECTED:
        try:
            doc = db["sessions"].find_one({"type": "chat"}, {"_id": 0})
            if doc:
                return doc
        except Exception as e:
            safe_print(f"[DB ERROR] get_chat_sessions failed: {e}")
            
    return safe_load_json(CHAT_SESSIONS_FILE, {"sessions": [], "active_id": None})

@router.post("/sessions/chat")
async def save_chat_sessions(payload: SessionsPayload):
    """Persist chat sessions to local file (and MongoDB if configured) so Git tracks it."""
    data = payload.model_dump()
    data["type"] = "chat"
    if MONGODB_CONNECTED:
        try:
            db["sessions"].update_one({"type": "chat"}, {"$set": data}, upsert=True)
        except Exception as e:
            safe_print(f"[DB ERROR] save_chat_sessions failed: {e}")

    safe_save_json(CHAT_SESSIONS_FILE, data)
    return {"status": "success", "count": len(payload.sessions)}
