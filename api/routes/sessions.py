from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request

from api.routes.accounts import extract_user_from_request
from api.schemas import SessionsPayload
from api.utils import safe_load_json, safe_print, safe_save_json

try:
    from modules.core.database import MONGODB_CONNECTED, db
except Exception:
    db = None
    MONGODB_CONNECTED = False

CHAT_SESSIONS_FILE = "data/atom_chat_sessions.json"

router = APIRouter()


def _has_any_messages(sessions_list: Optional[List[Dict[str, Any]]]) -> bool:
    """Return True if at least one session contains one or more chat messages."""
    if not isinstance(sessions_list, list):
        return False
    return any(
        isinstance(s, dict) and len(s.get("messages") or []) > 0
        for s in sessions_list
    )


def _load_local_account_doc(username: str) -> Optional[Dict[str, Any]]:
    """Load per-account chat session document from local JSON fallback."""
    raw = safe_load_json(CHAT_SESSIONS_FILE, {})
    if isinstance(raw, dict):
        accounts_map = raw.get("accounts")
        if isinstance(accounts_map, dict):
            doc = accounts_map.get(username)
            if isinstance(doc, dict):
                return doc
    return None


@router.get("/sessions/chat")
async def get_chat_sessions(request: Request):
    """Retrieve per-account chat history; Guest users stay strictly local."""
    user = extract_user_from_request(request)
    if not user:
        return {"sessions": [], "active_id": None, "guest": True}

    username = user["username"]
    if MONGODB_CONNECTED:
        try:
            doc = db["sessions"].find_one(
                {"type": "chat", "username": username}, {"_id": 0}
            )
            if doc:
                return doc
        except Exception as e:
            safe_print(f"[DB ERROR] get_chat_sessions failed: {e}")

    local_doc = _load_local_account_doc(username)
    if local_doc:
        return local_doc

    return {"sessions": [], "active_id": None, "username": username}


@router.post("/sessions/chat")
async def save_chat_sessions(request: Request, payload: SessionsPayload):
    """Persist per-account chat sessions; Guest users stay strictly local."""
    user = extract_user_from_request(request, payload.token)
    if not user:
        return {"status": "guest_local_only", "count": 0}

    username = user["username"]

    # Anti-data-loss guard: never let an unforced empty client overwrite saved messages
    if not _has_any_messages(payload.sessions) and not payload.force_overwrite:
        existing_sessions: List[Dict[str, Any]] = []
        if MONGODB_CONNECTED:
            try:
                existing_doc = db["sessions"].find_one(
                    {"type": "chat", "username": username}, {"_id": 0, "sessions": 1}
                )
                if existing_doc and isinstance(existing_doc.get("sessions"), list):
                    existing_sessions = existing_doc["sessions"]
            except Exception as e:
                safe_print(f"[DB ERROR] existing session guard failed: {e}")

        if not existing_sessions:
            local_doc = _load_local_account_doc(username)
            if local_doc and isinstance(local_doc.get("sessions"), list):
                existing_sessions = local_doc["sessions"]

        if _has_any_messages(existing_sessions):
            return {
                "status": "skipped_empty_overwrite",
                "count": len(existing_sessions),
            }

    doc_data = {
        "type": "chat",
        "username": username,
        "sessions": payload.sessions,
        "active_id": payload.active_id,
        "updated_at": datetime.now().isoformat(),
    }

    if MONGODB_CONNECTED:
        try:
            db["sessions"].update_one(
                {"type": "chat", "username": username},
                {"$set": dict(doc_data)},
                upsert=True,
            )
        except Exception as e:
            safe_print(f"[DB ERROR] save_chat_sessions failed: {e}")

    all_data = safe_load_json(CHAT_SESSIONS_FILE, {})
    if not isinstance(all_data, dict):
        all_data = {}
    if not isinstance(all_data.get("accounts"), dict):
        all_data["accounts"] = {}
    all_data["accounts"][username] = doc_data
    safe_save_json(CHAT_SESSIONS_FILE, all_data)

    return {
        "status": "success",
        "count": len(payload.sessions),
        "username": username,
    }
