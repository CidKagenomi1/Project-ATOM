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

try:
    from modules.core.database import db, MONGODB_CONNECTED
except Exception as e:
    db = None
    MONGODB_CONNECTED = False
    print(f"[WARN] Database import fallback: {e}")

try:
    from api.notes_ai import refine_text, auto_tag, chat_with_context, generate_title, generate_metadata_pydantic, invoke_llm_safely
except ImportError:
    try:
        from notes_ai import refine_text, auto_tag, chat_with_context, generate_title, generate_metadata_pydantic, invoke_llm_safely
    except Exception as e:
        print(f"[WARN] notes_ai import fallback: {e}")

# Helper for read-only filesystem environments (e.g. Vercel)
def safe_save_json(filepath: str, data: Any) -> bool:
    """Safely save JSON file with fallback to /tmp if filesystem is read-only (e.g. Vercel)."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[WARN] Local save failed for {filepath}: {e}. Trying /tmp fallback...")
        try:
            tmp_path = os.path.join("/tmp", os.path.basename(filepath))
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as tmp_e:
            print(f"[WARN] /tmp fallback save also failed: {tmp_e}")
            return False

def safe_load_json(filepath: str, default: Any = None) -> Any:
    """Safely load JSON file with /tmp fallback."""
    candidates = [filepath, os.path.join("/tmp", os.path.basename(filepath))]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return default if default is not None else {}

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
        try:
            from modules.core.cortex import ATOMCortex
            cortex_instance = ATOMCortex()
        except Exception as e:
            print(f"[CORTEX INIT ERROR] {e}. Using resilient FallbackCortex.")
            class FallbackCortex:
                class Librarian:
                    def __init__(self):
                        self.raw_history = []
                    def clear(self):
                        self.raw_history = []
                def __init__(self):
                    self.librarian = self.Librarian()
                def process(self, user_input, model_preference="auto", image_files=None, status_callback=None):
                    google_key = os.getenv("GOOGLE_API_KEY")
                    if google_key:
                        try:
                            from langchain_google_genai import ChatGoogleGenerativeAI
                            llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), google_api_key=google_key, temperature=0.7)
                            res = llm.invoke(user_input).content
                            if isinstance(res, list):
                                res = res[0].get('text', str(res[0])) if res else ""
                            return str(res), [{"step": "[ROUTER]", "detail": "Fallback Gemini"}, {"step": "[LOG]", "detail": "Model: Gemini-Flash"}]
                        except Exception as ge:
                            return f"Cortex error: {ge}", [{"step": "[ERROR]", "detail": str(ge)}]
                    return "Sistem AI sedang offline. Silakan tambahkan API key di environment.", [{"step": "[ERROR]", "detail": "No API key"}]
            cortex_instance = FallbackCortex()
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

class SessionsPayload(BaseModel):
    sessions: List[Dict[str, Any]] = []
    active_id: Optional[str] = None


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

    # --- ANCESTOR ECHO (Deterministic Zero-LLM) for Quick Actions ---
    if not image_files:
        try:
            from modules.core.ancestor import get_ancestor
            ancestor = get_ancestor()
            echo_match = ancestor.match_echo(prompt)
            if echo_match:
                return ChatResponse(
                    response=echo_match["response"],
                    model=echo_match["model"],
                    thinking=echo_match["thinking"],
                    duration=echo_match["duration"]
                )
        except Exception as ae:
            print(f"[WARN] Ancestor Echo check skipped: {ae}")

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
        if isinstance(step, dict) and "[LOG]" in step.get("step", ""):
            parts = step.get("detail", "").split("|")
            for p in parts:
                if "Model:" in p:
                    model_name = p.split(":", 1)[1].strip()
                    break

    # Sanitize thinking steps so every field is guaranteed to be a string
    sanitized_thinking = []
    for step in thinking:
        if isinstance(step, dict):
            sanitized_thinking.append({
                "step": str(step.get("step", "")),
                "detail": str(step.get("detail", ""))
            })
        else:
            sanitized_thinking.append({"step": "[INFO]", "detail": str(step)})

    return ChatResponse(
        response=response_text,
        model=model_name,
        thinking=sanitized_thinking,
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
    return safe_load_json(BUBBLES_FILE, {"bubbles": [], "last_id": 0})

def save_bubbles(data: dict) -> None:
    safe_save_json(BUBBLES_FILE, data)


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
                doc_id = str(b.get("_id"))
                b.pop("_id", None)
                if "id" not in b or b["id"] is None:
                    b["id"] = doc_id
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
            new_id = (max_bubble["id"] + 1) if (max_bubble and isinstance(max_bubble.get("id"), int)) else 1
            bubble = {
                "id": new_id,
                "text": request.text,
                "color": random.choice(colors),
                "created_at": datetime.now().isoformat(),
                "expanded": False
            }
            db["bubbles"].insert_one(bubble)
            bubble.pop("_id", None)
            try:
                data = load_bubbles()
                data["bubbles"] = [b for b in data.get("bubbles", []) if str(b.get("id")) != str(new_id)]
                data["bubbles"].insert(0, dict(bubble))
                data["last_id"] = max(data.get("last_id", 0), new_id)
                save_bubbles(data)
            except Exception:
                pass
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
async def delete_existing_bubble(id: str):
    parsed_id = int(id) if str(id).isdigit() else id
    if MONGODB_CONNECTED:
        try:
            from bson import ObjectId
            query_conds = [{"id": parsed_id}, {"id": str(id)}]
            if ObjectId.is_valid(id):
                query_conds.append({"_id": ObjectId(id)})
            res = db["bubbles"].delete_one({"$or": query_conds})
            try:
                data = load_bubbles()
                data["bubbles"] = [b for b in data.get("bubbles", []) if str(b.get("id")) != str(id)]
                save_bubbles(data)
            except Exception:
                pass
            return {"status": "success", "deleted": res.deleted_count}
        except Exception as e:
            print(f"[DB ERROR] delete_bubble failed: {e}. Using local.")
            
    # Local fallback
    data = load_bubbles()
    data["bubbles"] = [b for b in data.get("bubbles", []) if str(b.get("id")) != str(id)]
    save_bubbles(data)
    return {"status": "success"}

@app.post("/api/bubbles/{id}/expand")
async def expand_bubble(id: str):
    parsed_id = int(id) if str(id).isdigit() else id
    bubble = None
    if MONGODB_CONNECTED:
        try:
            from bson import ObjectId
            query_conds = [{"id": parsed_id}, {"id": str(id)}]
            if ObjectId.is_valid(id):
                query_conds.append({"_id": ObjectId(id)})
            bubble = db["bubbles"].find_one({"$or": query_conds})
            if bubble:
                bubble.pop("_id", None)
        except Exception as e:
            print(f"[DB ERROR] expand_bubble load failed: {e}. Using local.")
            
    if not bubble:
        # Local fallback search
        data = load_bubbles()
        for b in data.get("bubbles", []):
            if str(b.get("id")) == str(id):
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
        try:
            from api.notes_ai import invoke_llm_safely
            prompt = f"Tulis sebuah artikel terstruktur dan mendalam dalam bahasa Indonesia (menggunakan format Markdown) berdasarkan ide singkat berikut: '{bubble['text']}'"
            response = invoke_llm_safely(prompt, 0.3)
            content = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            content = f"# {bubble['text']}\n\nIde singkat: {bubble['text']}\n\n*(Catatan: Ekspansi AI otomatis dialihkan: {e})*"
    else:
        try:
            content = run_research_crew(f"Research and write about: {bubble['text']}")
        except Exception as e:
            try:
                from api.notes_ai import invoke_llm_safely
                prompt = f"Tulis sebuah artikel terstruktur dan mendalam dalam bahasa Indonesia (menggunakan format Markdown) berdasarkan ide singkat berikut: '{bubble['text']}'"
                response = invoke_llm_safely(prompt, 0.3)
                content = response.content if hasattr(response, 'content') else str(response)
            except Exception as fe:
                content = f"# {bubble['text']}\n\nIde singkat: {bubble['text']}\n\n*(Catatan: Riset otomatis dialihkan: {fe})*"

            
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

# --- Bulletin Endpoints ---

class MarkedNews(BaseModel):
    id: str
    title: str
    content: str
    source: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None

class UnmarkRequest(BaseModel):
    id: str

class SummarizeNewsRequest(BaseModel):
    title: str
    content: str
    source: Optional[str] = "News Source"

@app.get("/api/bulletin/fetch")
async def fetch_bulletin(category: Optional[str] = "technology", q: Optional[str] = None, scope: Optional[str] = "international"):
    import requests
    news_api_key = os.environ.get("NEWS_API_KEY", "")
    is_national = (scope or "").lower() in ["national", "nasional", "id", "indonesia"]
    
    # If no key is set, we return mock data for testing UI
    if not news_api_key:
        if is_national:
            return {
                "status": "success",
                "scope": "national",
                "articles": [
                    {
                        "id": "mock-nat-1",
                        "title": "Inovasi Ekosistem Kecerdasan Buatan Nasional di Sektor Industri 2026",
                        "description": "Kementerian dan universitas terkemuka di Indonesia memamerkan terobosan AI lokal untuk manufaktur dan logistik maritim.",
                        "content": "Indonesia resmi meluncurkan inisiatif percepatan kecerdasan buatan nasional dengan konsorsium riset teknologi terpadu. Model neural buatan anak bangsa diarahkan untuk otomatisasi rantai pasok dan pemantauan maritim terdistribusi.",
                        "source": "Antara News / ATOM",
                        "url": "#",
                        "image_url": "",
                        "author": "Biro Nasional",
                        "published_at": "2026-10-14T08:00:00Z",
                        "scope": "national"
                    },
                    {
                        "id": "mock-nat-2",
                        "title": "Pusat Riset Komputasi Kuantum & Keamanan Siber Resmi Dibuka di Jakarta",
                        "description": "Lembaga riset nasional membangun laboratorium enkripsi pos-kuantum guna memproteksi infrastruktur data kritis.",
                        "content": "Laboratorium keamanan siber pos-kuantum perdana di Indonesia mulai beroperasi hari ini. Lembaga ini difokuskan pada mitigasi risiko serangan komputasi kuantum serta penguatan kedaulatan data nasional.",
                        "source": "Tempo Tekno",
                        "url": "#",
                        "image_url": "",
                        "author": "Desk Sains Nasional",
                        "published_at": "2026-10-14T07:30:00Z",
                        "scope": "national"
                    }
                ]
            }
        return {
            "status": "success",
            "scope": "international",
            "articles": [
                {
                    "id": "mock-1",
                    "title": "Quantum Computing Breakthrough in Neural Network Simulation",
                    "description": "Scientists achieve room temperature quantum coherence.",
                    "content": "Scientists have achieved a new level of quantum coherence at room temperature, paving the way for advanced neural network simulations and instant model inference.",
                    "source": "Science Journal",
                    "url": "#",
                    "image_url": "",
                    "author": "Science Desk",
                    "published_at": "2026-10-14T07:30:00Z",
                    "scope": "international"
                }
            ]
        }
    
    headers = {"User-Agent": "ATOM-System/1.0"}
    try:
        if is_national:
            # 1. National (Indonesian) Feed - Broad coverage, strictly non-criminal
            crime_negatives = "-pembunuhan -narkoba -curanmor -pencurian -begal -mutilasi -tawuran"
            if q and q.strip():
                safe_q = requests.utils.quote(f"({q.strip()}) {crime_negatives}")
                newsapi_url = f"https://newsapi.org/v2/everything?q={safe_q}&language=id&sortBy=publishedAt&apiKey={news_api_key}"
            else:
                id_cat_queries = {
                    "general": f"(indonesia OR nasional OR pembangunan OR ikn OR presiden OR masyarakat OR infrastruktur) {crime_negatives}",
                    "politics": f"(politik OR dpr OR mpr OR kementerian OR pemilu OR pilkada OR menteri OR presiden OR kebijakan) {crime_negatives}",
                    "business": f"(bisnis OR ekonomi OR saham OR investasi OR perbankan OR industri OR bumn OR rupiah) {crime_negatives}",
                    "culture": f"(pendidikan OR kampus OR sekolah OR kebudayaan OR pariwisata OR seni OR tradisi) {crime_negatives}",
                    "technology": f"(teknologi OR 'kecerdasan buatan' OR AI OR startup OR gadget OR digital) {crime_negatives}"
                }
                cat_key = (category or "general").lower()
                cat_query = id_cat_queries.get(cat_key, id_cat_queries["general"])
                safe_cat_q = requests.utils.quote(cat_query)
                newsapi_url = f"https://newsapi.org/v2/everything?q={safe_cat_q}&language=id&sortBy=publishedAt&apiKey={news_api_key}"
        else:
            # 2. International (Global) Feed - Diverse science branches (biology, geography, astronomy, discoveries) & tech
            if q and q.strip():
                safe_q = requests.utils.quote(q.strip())
                newsapi_url = f"https://newsapi.org/v2/everything?q={safe_q}&sortBy=publishedAt&language=en&apiKey={news_api_key}"
            else:
                intl_cat_queries = {
                    "technology": "technology OR 'artificial intelligence' OR software OR computing OR gadget",
                    "biology": "biology OR wildlife OR genetics OR evolution OR biodiversity OR 'marine life'",
                    "geography": "geography OR geology OR volcano OR oceanography OR climate OR 'earth science'",
                    "astronomy": "astronomy OR astrophysics OR telescope OR 'deep space' OR cosmology OR quantum",
                    "discoveries": "archaeology OR discovery OR 'ancient civilization' OR fossil OR paleontology",
                    "business": "global economy OR markets OR 'stock market' OR inflation OR trade"
                }
                cat_key = (category or "technology").lower()
                if cat_key in intl_cat_queries:
                    safe_cat_q = requests.utils.quote(intl_cat_queries[cat_key])
                    newsapi_url = f"https://newsapi.org/v2/everything?q={safe_cat_q}&sortBy=publishedAt&language=en&apiKey={news_api_key}"
                else:
                    newsapi_url = f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={news_api_key}"
            
        response = requests.get(newsapi_url, headers=headers, timeout=10)
        
        # 2. Fallback to GNews if NewsAPI fails
        if response.status_code != 200:
            lang_param = "lang=id&country=id&" if is_national else "lang=en&"
            query_param = f"&q={requests.utils.quote(q.strip())}" if (q and q.strip()) else ""
            cat_param = f"category={category}&" if (category and not q) else ""
            gnews_url = f"https://gnews.io/api/v4/top-headlines?{cat_param}{lang_param}{query_param}&apikey={news_api_key}"
            response = requests.get(gnews_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            articles = []
            crime_bad_words = [
                "pembunuhan", "dibunuh", "tewas dibunuh", "mutilasi", "mayat", "jenazah",
                "narkoba", "sabu", "ganja", "ekstasi", "miras", "razia thm", "diskotek",
                "pemerkosaan", "pencabulan", "pelecehan seksual", "rudapaksa",
                "pencurian", "mencuri", "curanmor", "maling", "perampokan", "rampok", "begal",
                "tawuran", "pengeroyokan", "bacok", "senjata tajam", "penikaman",
                "judi online", "judol", "slot online", "slot gacor", "taruhan",
                "penipuan", "penggelapan", "penganiayaan"
            ]
            for art in data.get("articles", []):
                title = art.get("title", "Untitled Transmission")
                desc = art.get("description", "") or ""
                body = art.get("content", "") or ""

                # Explicitly exclude crime news on national scope
                if is_national:
                    haystack = (title + " " + desc).lower()
                    if any(bad in haystack for bad in crime_bad_words):
                        continue

                articles.append({
                    "id": art.get("url") or title,
                    "title": title,
                    "description": desc,
                    "content": (desc + "\n\n" + body).strip() or desc or "Konten artikel lengkap dapat dibaca langsung pada tautan sumber asli.",
                    "source": art.get("source", {}).get("name", "Unknown Source"),
                    "url": art.get("url", "#"),
                    "image_url": art.get("urlToImage") or art.get("image", ""),
                    "author": art.get("author", "Editorial Desk"),
                    "published_at": art.get("publishedAt", ""),
                    "scope": "national" if is_national else "international"
                })
            return {"status": "success", "scope": "national" if is_national else "international", "articles": articles}
        else:
            return {"status": "error", "message": f"API Error: {response.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

MARKED_NEWS_FILE = "data/atom_bulletin_marked.json"

@app.get("/api/bulletin/marked")
async def get_marked_bulletin():
    if MONGODB_CONNECTED:
        try:
            items = list(db["marked_news"].find({}, {"_id": 0}))
            return {"status": "success", "articles": items}
        except Exception as e:
            print(f"[DB ERROR] get_marked_bulletin failed: {e}")
    data = safe_load_json(MARKED_NEWS_FILE, {"marked_news": []})
    if not isinstance(data, dict):
        data = {"marked_news": []}
    return {"status": "success", "articles": data.get("marked_news", [])}

@app.post("/api/bulletin/mark")
async def mark_bulletin(news: MarkedNews):
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    news_entry = news.model_dump()
    news_entry["marked_at"] = timestamp
    
    if MONGODB_CONNECTED:
        try:
            db["marked_news"].update_one(
                {"id": news.id},
                {"$set": news_entry},
                upsert=True
            )
            return {"status": "success"}
        except Exception as e:
            print(f"[DB ERROR] mark_bulletin failed: {e}. Writing locally.")
            
    data = safe_load_json(MARKED_NEWS_FILE, {"marked_news": []})
    if not isinstance(data, dict):
        data = {"marked_news": []}
    if "marked_news" not in data:
        data["marked_news"] = []
    
    # Check if already marked
    if not any(item.get("id") == news.id for item in data["marked_news"]):
        data["marked_news"].append(news_entry)
        safe_save_json(MARKED_NEWS_FILE, data)
    
    return {"status": "success"}

@app.post("/api/bulletin/unmark")
async def unmark_bulletin(req: UnmarkRequest):
    if MONGODB_CONNECTED:
        try:
            db["marked_news"].delete_one({"id": req.id})
        except Exception as e:
            print(f"[DB ERROR] unmark_bulletin failed: {e}")
            
    data = safe_load_json(MARKED_NEWS_FILE, {"marked_news": []})
    if isinstance(data, dict) and "marked_news" in data:
        data["marked_news"] = [item for item in data["marked_news"] if item.get("id") != req.id]
        safe_save_json(MARKED_NEWS_FILE, data)
    return {"status": "success"}

@app.post("/api/bulletin/summarize")
async def summarize_news_endpoint(req: SummarizeNewsRequest):
    try:
        from api.notes_ai import get_llm
    except ImportError:
        from notes_ai import get_llm
    
    prompt = f"""Sebagai asisten cerdas A.T.O.M., berikan ringkasan eksekutif yang bernas, informatif, dan mudah dipahami dari berita berikut:

Judul: {req.title}
Sumber: {req.source}
Konten: {req.content}

Instruksi format jawaban:
- **Inti Berita**: 1-2 kalimat ringkas penjelasan utama berita.
- **Poin Penting & Insight**: 3 poin bullet dampak atau informasi kunci.
- Gunakan bahasa Indonesia yang ramah, santai, dan jelas."""
    try:
        llm = get_llm(temperature=0.3)
        if llm:
            res = llm.invoke(prompt)
            return {"status": "success", "summary": res.content}
    except Exception as e:
        print(f"[WARN] summarize_news LLM error: {e}")
    
    # Heuristic fallback if LLM offline
    return {
        "status": "success",
        "summary": f"**Inti Berita:** {req.title}\n\n**Poin Penting:**\n- Informasi diterbitkan oleh {req.source}.\n- {req.content[:240]}..."
    }


# --- Chat & Roleplay Sessions Storage ---
CHAT_SESSIONS_FILE = "data/atom_chat_sessions.json"
RP_SESSIONS_FILE = "data/atom_rp_sessions.json"

@app.get("/api/sessions/chat")
async def get_chat_sessions():
    """Retrieve chat history and sessions from database or local project file."""
    if MONGODB_CONNECTED:
        try:
            doc = db["sessions"].find_one({"type": "chat"}, {"_id": 0})
            if doc:
                return doc
        except Exception as e:
            print(f"[DB ERROR] get_chat_sessions failed: {e}")
            
    return safe_load_json(CHAT_SESSIONS_FILE, {"sessions": [], "active_id": None})


@app.post("/api/sessions/chat")
async def save_chat_sessions(payload: SessionsPayload):
    """Persist chat sessions to local file (and MongoDB if configured) so Git tracks it."""
    data = payload.model_dump()
    data["type"] = "chat"
    if MONGODB_CONNECTED:
        try:
            db["sessions"].update_one({"type": "chat"}, {"$set": data}, upsert=True)
        except Exception as e:
            print(f"[DB ERROR] save_chat_sessions failed: {e}")

    safe_save_json(CHAT_SESSIONS_FILE, data)
    return {"status": "success", "count": len(payload.sessions)}


@app.get("/api/sessions/roleplay")
async def get_rp_sessions():
    """Retrieve roleplay history and sessions from database or local project file."""
    if MONGODB_CONNECTED:
        try:
            doc = db["sessions"].find_one({"type": "roleplay"}, {"_id": 0})
            if doc:
                return doc
        except Exception as e:
            print(f"[DB ERROR] get_rp_sessions failed: {e}")
            
    return safe_load_json(RP_SESSIONS_FILE, {"sessions": [], "active_id": None})


@app.post("/api/sessions/roleplay")
async def save_rp_sessions(payload: SessionsPayload):
    """Persist roleplay sessions to local file (and MongoDB if configured) so Git tracks it."""
    data = payload.model_dump()
    data["type"] = "roleplay"
    if MONGODB_CONNECTED:
        try:
            db["sessions"].update_one({"type": "roleplay"}, {"$set": data}, upsert=True)
        except Exception as e:
            print(f"[DB ERROR] save_rp_sessions failed: {e}")

    safe_save_json(RP_SESSIONS_FILE, data)
    return {"status": "success", "count": len(payload.sessions)}

