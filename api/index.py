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
    AccountRegisterRequest,
    AccountLoginRequest,
)

# Import modular route handlers
from api.routes import chat, notes, bubbles, telemetry, bulletin, sessions, accounts

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
app.include_router(accounts.router, prefix="/api", tags=["Accounts"])

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
except Exception as db_e:
    safe_print(f"[WARN] DATABASE init/migration warning: {db_e}")
