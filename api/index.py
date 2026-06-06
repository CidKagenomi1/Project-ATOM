import os
import sys
import time
import json
import csv

def safe_print(*args, **kwargs):
    import sys
    import builtins
    try:
        enc = sys.stdout.encoding or 'cp1252' if (sys.stdout and hasattr(sys.stdout, 'encoding')) else 'cp1252'
        new_args = []
        for arg in args:
            if isinstance(arg, str):
                new_args.append(arg.encode(enc, errors='replace').decode(enc))
            else:
                new_args.append(arg)
        builtins.print(*new_args, **kwargs)
    except Exception:
        try:
            new_args = [str(arg).encode('ascii', errors='replace').decode('ascii') for arg in args]
            builtins.print(*new_args, **kwargs)
        except Exception:
            pass

print = safe_print

from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure api directory and project root are in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))

from modules.core.database import db, MONGODB_CONNECTED

try:
    from api.notes_ai import refine_text, auto_tag, chat_with_context, generate_title, generate_metadata_pydantic
except ImportError:
    from notes_ai import refine_text, auto_tag, chat_with_context, generate_title, generate_metadata_pydantic

app = FastAPI(
    title="A.T.O.M. API",
    description="Backend API for Autonomous Task Orchestration Machine",
    version="4.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Shared Cortex Instance ---
cortex_instance = None

def get_cortex():
    global cortex_instance
    if cortex_instance is None:
        from modules.core.cortex import ATOMCortex
        cortex_instance = ATOMCortex()
    return cortex_instance


# --- Pydantic Models ---
class ChatFile(BaseModel):
    name: str
    content: str

class ChatRequest(BaseModel):
    prompt: str = ""
    history: List[Dict[str, Any]] = []
    files: List[ChatFile] = []
    model_preference: str = "auto"

class ChatResponse(BaseModel):
    response: str
    model: str
    thinking: List[Dict[str, str]]
    duration: float

class NotesAIRequest(BaseModel):
    action: str
    content: str = ""
    question: str = ""

class NotesAIResponse(BaseModel):
    result: Any

class NoteCreate(BaseModel):
    title: str = "Untitled Note"
    content: str = ""
    tags: List[str] = []

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class BubbleCreate(BaseModel):
    text: str

class TelemetryEntry(BaseModel):
    user_input: str
    model_used: str
    response_time: float
    status: str
    ai_response: Optional[str] = ""


# --- Core Endpoints ---

@app.get("/")
async def root():
    return {"status": "online", "service": "A.T.O.M. API (FastAPI)"}


@app.get("/api/status")
async def status_endpoint():
    """Retrieve dynamic status of AI systems (Local, Cloud, Crew, Gemini)."""
    try:
        from modules.core.cortex import OLLAMA_AVAILABLE, GROQ_AVAILABLE, GEMINI_AVAILABLE, CREW_AVAILABLE
        return {
            "local": "online" if OLLAMA_AVAILABLE else "offline",
            "cloud": "online" if GROQ_AVAILABLE else "offline",
            "crew": "online" if CREW_AVAILABLE else "offline",
            "gemini": "online" if GEMINI_AVAILABLE else "offline",
        }
    except Exception as e:
        return {
            "local": "offline",
            "cloud": "offline",
            "crew": "offline",
            "gemini": "offline",
            "error": str(e)
        }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time = time.time()
    prompt = request.prompt.strip()
    history = request.history
    files = [f.model_dump() for f in request.files]
    model_preference = request.model_preference

    if not prompt and not files:
        raise HTTPException(status_code=400, detail="prompt is required")

    if not prompt and files:
        has_image = any(f.get("content", "").startswith("data:image/") for f in files)
        if has_image:
            prompt = "Jelaskan gambar ini."
        else:
            prompt = "Review file yang terlampir."

    # Separate text files and base64 images
    text_files = []
    image_files = []
    for f in files:
        content_str = f.get("content", "")
        if content_str.startswith("data:image/"):
            image_files.append(f)
        else:
            text_files.append(f)

    # Prepend file context to prompt if any
    if text_files:
        file_context_parts = []
        for f in text_files:
            file_context_parts.append(f"[FILE: {f['name']}]\n{f['content']}\n[END FILE]")
        prompt = "\n\n".join(file_context_parts) + f"\n\nQuery: {prompt}"

    # Process using shared ATOMCortex
    cortex = get_cortex()
    
    # Synchronize raw history in cortex Librarian with client-provided history
    cortex.librarian.clear()
    for msg in history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            cortex.librarian.raw_history.append(f"User: {content}")
        else:
            cortex.librarian.raw_history.append(f"ATOM: {content}")

    try:
        response_text, thinking = cortex.process(
            user_input=prompt,
            model_preference=model_preference,
            image_files=image_files
        )
    except Exception as e:
        response_text = f"Cortex processing error: {e}"
        thinking = [{"step": "[ERROR]", "detail": str(e)}]

    duration = round(time.time() - start_time, 2)

    # Find resulting model name from thinking logs
    model_name = "Cortex Route"
    for step in reversed(thinking):
        if "[LOG]" in step.get("step", ""):
            parts = step.get("detail", "").split("|")
            for p in parts:
                if "Model:" in p:
                    model_name = p.split(":", 1)[1].strip()
                    break

    return ChatResponse(
        response=response_text,
        model=model_name,
        thinking=thinking,
        duration=duration
    )


@app.post("/api/notes_ai", response_model=NotesAIResponse)
async def notes_ai_endpoint(request: NotesAIRequest):
    action = request.action
    content = request.content
    question = request.question

    if not action:
        raise HTTPException(status_code=400, detail="action is required")

    result = None

    if action == "refine":
        if not content:
            raise HTTPException(status_code=400, detail="content is required for refine")
        result = refine_text(content)
    elif action == "autotag":
        if not content:
            raise HTTPException(status_code=400, detail="content is required for autotag")
        result = auto_tag(content)
    elif action == "chat":
        if not content or not question:
            raise HTTPException(status_code=400, detail="content and question are required for chat")
        result = chat_with_context(content, question)
    elif action == "title":
        if not content:
            raise HTTPException(status_code=400, detail="content is required for title")
        result = generate_title(content)
    elif action == "metadata":
        if not content:
            raise HTTPException(status_code=400, detail="content is required for metadata")
        result = generate_metadata_pydantic(content)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    return NotesAIResponse(result=result)


# --- Notes CRUD Endpoints ---

@app.get("/api/notes")
async def list_notes(query: Optional[str] = None):
    from modules.notes.note_storage import get_all_notes, search_notes
    if query:
        return search_notes(query)
    return get_all_notes()


@app.get("/api/notes/tags")
async def list_tags():
    from modules.notes.note_storage import get_all_tags
    return get_all_tags()


@app.get("/api/notes/{id}")
async def retrieve_note(id: int):
    from modules.notes.note_storage import get_note
    note = get_note(id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.post("/api/notes")
async def create_new_note(request: NoteCreate):
    from modules.notes.note_storage import create_note
    try:
        return create_note(title=request.title, content=request.content, tags=request.tags)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create note: {e}")


@app.put("/api/notes/{id}")
async def update_existing_note(id: int, request: NoteUpdate):
    from modules.notes.note_storage import update_note
    try:
        note = update_note(note_id=id, title=request.title, content=request.content, tags=request.tags)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update note: {e}")


@app.delete("/api/notes/{id}")
async def delete_existing_note(id: int):
    from modules.notes.note_storage import delete_note
    try:
        success = delete_note(id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {e}")


# --- Bubbles CRUD Endpoints ---
BUBBLES_FILE = "data/atom_bubbles.json"

def load_bubbles() -> dict:
    if os.path.exists(BUBBLES_FILE):
        try:
            with open(BUBBLES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"bubbles": [], "last_id": 0}

def save_bubbles(data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(BUBBLES_FILE), exist_ok=True)
        with open(BUBBLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SAVE BUBBLES ERROR] {e}")

# === BUBBLES AUTO-MIGRATION TO MONGODB ===
if MONGODB_CONNECTED:
    try:
        if db["bubbles"].count_documents({}) == 0:
            local_bubbles = load_bubbles().get("bubbles", [])
            if local_bubbles:
                print(f"[INFO] DATABASE: Migrating {len(local_bubbles)} bubbles to MongoDB...")
                for b in local_bubbles:
                    b.pop("_id", None)
                db["bubbles"].insert_many(local_bubbles)
                print("[OK] DATABASE: Bubbles migration completed.")
    except Exception as e:
        print(f"[WARN] DATABASE: Bubbles auto-migration failed: {e}")

@app.get("/api/bubbles")
async def list_bubbles():
    if MONGODB_CONNECTED:
        try:
            cursor = db["bubbles"].find().sort("created_at", -1)
            bubbles_list = []
            for b in cursor:
                b.pop("_id", None)
                bubbles_list.append(b)
            return bubbles_list
        except Exception as e:
            print(f"[DB ERROR] list_bubbles failed: {e}. Using local.")
    data = load_bubbles()
    return data.get("bubbles", [])

@app.post("/api/bubbles")
async def create_bubble(request: BubbleCreate):
    import random
    from datetime import datetime
    colors = ["#9333EA", "#3B82F6", "#14B8A6", "#F59E0B", "#F43F5E", "#10B981"]
    
    if MONGODB_CONNECTED:
        try:
            max_bubble = db["bubbles"].find_one(sort=[("id", -1)])
            new_id = (max_bubble["id"] + 1) if max_bubble else 1
            bubble = {
                "id": new_id,
                "text": request.text,
                "color": random.choice(colors),
                "created_at": datetime.now().isoformat(),
                "expanded": False
            }
            db["bubbles"].insert_one(bubble)
            bubble.pop("_id", None)
            return bubble
        except Exception as e:
            print(f"[DB ERROR] create_bubble failed: {e}. Using local.")
            
    # Local fallback
    data = load_bubbles()
    new_id = data.get("last_id", 0) + 1
    bubble = {
        "id": new_id,
        "text": request.text,
        "color": random.choice(colors),
        "created_at": datetime.now().isoformat(),
        "expanded": False
    }
    data["bubbles"].insert(0, bubble)
    data["last_id"] = new_id
    save_bubbles(data)
    return bubble

@app.delete("/api/bubbles/{id}")
async def delete_existing_bubble(id: int):
    if MONGODB_CONNECTED:
        try:
            res = db["bubbles"].delete_one({"id": id})
            if res.deleted_count > 0:
                return {"status": "success"}
            raise HTTPException(status_code=404, detail="Bubble not found")
        except HTTPException:
            raise
        except Exception as e:
            print(f"[DB ERROR] delete_bubble failed: {e}. Using local.")
            
    # Local fallback
    data = load_bubbles()
    original_len = len(data["bubbles"])
    data["bubbles"] = [b for b in data["bubbles"] if b["id"] != id]
    if len(data["bubbles"]) < original_len:
        save_bubbles(data)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Bubble not found")

@app.post("/api/bubbles/{id}/expand")
async def expand_bubble(id: int):
    bubble = None
    if MONGODB_CONNECTED:
        try:
            bubble = db["bubbles"].find_one({"id": id})
            if bubble:
                bubble.pop("_id", None)
        except Exception as e:
            print(f"[DB ERROR] expand_bubble load failed: {e}. Using local.")
            
    if not bubble:
        # Local fallback search
        data = load_bubbles()
        for b in data["bubbles"]:
            if b["id"] == id:
                bubble = b
                break
                
    if not bubble:
        raise HTTPException(status_code=404, detail="Bubble not found")
        
    try:
        from modules.core.crew import run_research_crew
        CREW_AVAILABLE = True
    except ImportError:
        CREW_AVAILABLE = False
        
    content = ""
    if not CREW_AVAILABLE:
        from api.notes_ai import get_llm
        llm = get_llm(0.3)
        if not llm:
            raise HTTPException(status_code=500, detail="No AI provider configured for bubble expansion")
        prompt = f"Tulis sebuah artikel terstruktur dan mendalam dalam bahasa Indonesia (menggunakan format Markdown) berdasarkan ide singkat berikut: '{bubble['text']}'"
        try:
            response = llm.invoke(prompt)
            content = response.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI expansion failed: {e}")
    else:
        try:
            content = run_research_crew(f"Research and write about: {bubble['text']}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CrewAI research failed: {e}")
            
    from modules.notes.note_storage import create_note
    try:
        note = create_note(
            title=f"📝 {bubble['text'][:30]}...",
            content=content,
            tags=["bubble-expanded"],
            note_type="note"
        )
        
        # Mark bubble as expanded
        if MONGODB_CONNECTED:
            try:
                db["bubbles"].update_one({"id": id}, {"$set": {"expanded": True}})
            except Exception as e:
                print(f"[DB ERROR] expand_bubble mark failed: {e}. Saving locally.")
                
        # Local fallback mark too to keep in sync if local is used
        data = load_bubbles()
        for b in data["bubbles"]:
            if b["id"] == id:
                b["expanded"] = True
                break
        save_bubbles(data)
        
        return {"status": "success", "note": note}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to expand bubble: {e}")


# --- Telemetry Endpoints ---
TELEMETRY_FILE = "data/atom_telemetry.csv"

# === TELEMETRY AUTO-MIGRATION TO MONGODB ===
if MONGODB_CONNECTED:
    try:
        if db["telemetry"].count_documents({}) == 0 and os.path.exists(TELEMETRY_FILE):
            print("[INFO] DATABASE: Migrating local telemetry CSV to MongoDB...")
            import csv as local_csv
            with open(TELEMETRY_FILE, mode="r", encoding="utf-8") as f:
                reader = local_csv.DictReader(f)
                rows = list(reader)
                if rows:
                    db["telemetry"].insert_many(rows)
                    print("[OK] DATABASE: Telemetry migration completed.")
    except Exception as e:
        print(f"[WARN] DATABASE: Telemetry auto-migration failed: {e}")

@app.get("/api/telemetry")
async def get_telemetry_endpoint():
    if MONGODB_CONNECTED:
        try:
            cursor = db["telemetry"].find().sort("timestamp", -1)
            telemetry_list = []
            for row in cursor:
                row.pop("_id", None)
                telemetry_list.append(row)
            return telemetry_list
        except Exception as e:
            print(f"[DB ERROR] get_telemetry failed: {e}. Using local.")
            
    if not os.path.exists(TELEMETRY_FILE):
        return []
    try:
        with open(TELEMETRY_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading telemetry: {e}")

@app.post("/api/telemetry")
async def post_telemetry_endpoint(entry: TelemetryEntry):
    from datetime import datetime
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if MONGODB_CONNECTED:
        try:
            db["telemetry"].insert_one({
                "timestamp": timestamp_str,
                "user_input": entry.user_input,
                "model_used": entry.model_used,
                "response_time": entry.response_time,
                "status": entry.status,
                "ai_response": entry.ai_response
            })
            return {"status": "success"}
        except Exception as e:
            print(f"[DB ERROR] post_telemetry failed: {e}. Writing locally.")
            
    # Local fallback
    try:
        os.makedirs(os.path.dirname(TELEMETRY_FILE), exist_ok=True)
        write_header = not os.path.exists(TELEMETRY_FILE)
        with open(TELEMETRY_FILE, mode="a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp", "user_input", "model_used", "response_time", "status", "ai_response"])
            writer.writerow([
                timestamp_str,
                entry.user_input,
                entry.model_used,
                entry.response_time,
                entry.status,
                entry.ai_response
            ])
        return {"status": "success"}
    except Exception as e:
        print(f"[WARN] Local telemetry write failed (expected on read-only environments like Vercel): {e}")
        return {"status": "success", "info": "read_only_fallback"}

@app.delete("/api/telemetry")
async def delete_telemetry_endpoint():
    if MONGODB_CONNECTED:
        try:
            db["telemetry"].delete_many({})
            return {"status": "success"}
        except Exception as e:
            print(f"[DB ERROR] delete_telemetry failed: {e}. Clearing locally.")
            
    try:
        os.makedirs(os.path.dirname(TELEMETRY_FILE), exist_ok=True)
        with open(TELEMETRY_FILE, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "user_input", "model_used", "response_time", "status"])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing telemetry: {e}")
