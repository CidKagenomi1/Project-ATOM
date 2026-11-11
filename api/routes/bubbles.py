import random
from datetime import datetime
from fastapi import APIRouter, HTTPException
from api.schemas import BubbleCreate
from api.utils import safe_load_json, safe_save_json, safe_print

try:
    from modules.core.database import db, MONGODB_CONNECTED
except Exception as e:
    db = None
    MONGODB_CONNECTED = False

BUBBLES_FILE = "data/atom_bubbles.json"

def load_bubbles() -> dict:
    return safe_load_json(BUBBLES_FILE, {"bubbles": [], "last_id": 0})

def save_bubbles(data: dict) -> None:
    safe_save_json(BUBBLES_FILE, data)

router = APIRouter()

@router.get("/bubbles")
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
            safe_print(f"[DB ERROR] list_bubbles failed: {e}. Using local.")
    data = load_bubbles()
    return data.get("bubbles", [])

@router.post("/bubbles")
async def create_bubble(request: BubbleCreate):
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
            safe_print(f"[DB ERROR] create_bubble failed: {e}. Using local.")
            
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

@router.delete("/bubbles/{id}")
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
            safe_print(f"[DB ERROR] delete_bubble failed: {e}. Using local.")
            
    # Local fallback
    data = load_bubbles()
    data["bubbles"] = [b for b in data.get("bubbles", []) if str(b.get("id")) != str(id)]
    save_bubbles(data)
    return {"status": "success"}

@router.post("/bubbles/{id}/expand")
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
            safe_print(f"[DB ERROR] expand_bubble load failed: {e}. Using local.")
            
    if not bubble:
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
                safe_print(f"[DB ERROR] expand_bubble mark failed: {e}. Saving locally.")
                
        # Local fallback mark too
        data = load_bubbles()
        for b in data["bubbles"]:
            if b["id"] == id:
                b["expanded"] = True
                break
        save_bubbles(data)
        
        return {"status": "success", "note": note}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to expand bubble: {e}")
