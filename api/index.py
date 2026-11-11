import os
import sys

# Ensure api directory and project root are in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Re-export utilities and schemas for 100% backward compatibility
from api.utils import safe_print, safe_save_json, safe_load_json, get_cortex, cortex_instance
from api.schemas import (
    ChatFile,
    ChatRequest,
    ChatResponse,
    NotesAIRequest,
    NotesAIResponse,
    NoteCreate,
    NoteUpdate,
    BubbleCreate,
    TelemetryEntry,
    MarkedNews,
    UnmarkRequest,
    SummarizeNewsRequest,
    SessionsPayload,
)

# Import modular route handlers
from api.routes import chat, notes, bubbles, telemetry, bulletin, sessions

app = FastAPI(
    title="A.T.O.M. API",
    description="Backend API for Autonomous Task Orchestration Machine",
    version="5.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router, prefix="/api", tags=["Chat & Status"])
app.include_router(notes.router, prefix="/api", tags=["Notes & AI"])
app.include_router(bubbles.router, prefix="/api", tags=["Bubbles"])
app.include_router(telemetry.router, prefix="/api", tags=["Telemetry"])
app.include_router(bulletin.router, prefix="/api", tags=["Bulletin"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])

@app.get("/")
async def root():
    index_path = os.path.join(project_root, "public", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "online", "service": "A.T.O.M. API (FastAPI Modular)"}

# Automatic DB initializations / migrations on module load
try:
    from modules.core.database import db, MONGODB_CONNECTED
    if MONGODB_CONNECTED:
        # Bubbles migration
        if db["bubbles"].count_documents({}) == 0:
            local_bubbles = safe_load_json("data/atom_bubbles.json", {}).get("bubbles", [])
            if local_bubbles:
                safe_print(f"[INFO] DATABASE: Migrating {len(local_bubbles)} bubbles to MongoDB...")
                for b in local_bubbles:
                    b.pop("_id", None)
                db["bubbles"].insert_many(local_bubbles)
                safe_print("[OK] DATABASE: Bubbles migration completed.")
        
        # Telemetry migration
        telemetry_file = "data/atom_telemetry.csv"
        if db["telemetry"].count_documents({}) == 0 and os.path.exists(telemetry_file):
            import csv as local_csv
            with open(telemetry_file, mode="r", encoding="utf-8") as f:
                rows = list(local_csv.DictReader(f))
                if rows:
                    db["telemetry"].insert_many(rows)
                    safe_print("[OK] DATABASE: Telemetry migration completed.")
        
        # Sessions migration
        chat_sess_file = "data/atom_chat_sessions.json"
        if db["sessions"].count_documents({"type": "chat"}) == 0 and os.path.exists(chat_sess_file):
            local_chat = safe_load_json(chat_sess_file, None)
            if local_chat and local_chat.get("sessions"):
                local_chat["type"] = "chat"
                db["sessions"].update_one({"type": "chat"}, {"$set": local_chat}, upsert=True)
                safe_print("[OK] DATABASE: Migrated local chat sessions to MongoDB.")

        rp_sess_file = "data/atom_rp_sessions.json"
        if db["sessions"].count_documents({"type": "roleplay"}) == 0 and os.path.exists(rp_sess_file):
            local_rp = safe_load_json(rp_sess_file, None)
            if local_rp and local_rp.get("sessions"):
                local_rp["type"] = "roleplay"
                db["sessions"].update_one({"type": "roleplay"}, {"$set": local_rp}, upsert=True)
                safe_print("[OK] DATABASE: Migrated local roleplay sessions to MongoDB.")
except Exception as db_e:
    safe_print(f"[WARN] DATABASE init/migration warning: {db_e}")
