"""
ATOM Smart Notes - Storage Module
Handles CRUD operations for knowledge base notes, supporting MongoDB with a local file fallback.
"""

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import re
from modules.core.database import db, MONGODB_CONNECTED

# Local file database fallback
NOTES_DB = "data/atom_smart_notes.json"


def _load_local_db() -> Dict[str, Any]:
    """Load notes database from local file."""
    if os.path.exists(NOTES_DB):
        try:
            with open(NOTES_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"notes": [], "last_id": 0}


def _save_local_db(data: Dict[str, Any]) -> None:
    """Save notes database to local file."""
    try:
        os.makedirs(os.path.dirname(NOTES_DB), exist_ok=True)
        with open(NOTES_DB, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SAVE LOCAL ERROR] {e}")


# === AUTO-MIGRATION TO MONGODB ===
if MONGODB_CONNECTED:
    try:
        if db["notes"].count_documents({}) == 0:
            local_data = _load_local_db()
            local_notes = local_data.get("notes", [])
            if local_notes:
                print(f"[INFO] DATABASE: Migrating {len(local_notes)} notes from local JSON to MongoDB...")
                # Insert notes to MongoDB, removing any _id field from previous insertions
                for note in local_notes:
                    note.pop("_id", None)
                db["notes"].insert_many(local_notes)
                print("[OK] DATABASE: Migration completed successfully.")
    except Exception as e:
        print(f"[WARN] DATABASE: Auto-migration failed: {e}")


# === CRUD OPERATIONS ===

def create_note(
    title: str,
    content: str,
    tags: List[str] = None,
    links: List[int] = None,
    note_type: str = "note"
) -> Dict[str, Any]:
    """Create a new note."""
    if MONGODB_CONNECTED:
        try:
            # Generate new integer ID by finding max current ID
            max_note = db["notes"].find_one(sort=[("id", -1)])
            new_id = (max_note["id"] + 1) if max_note else 1
            
            note = {
                "id": new_id,
                "title": title,
                "content": content,
                "tags": tags or [],
                "links": links or [],
                "type": note_type,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            db["notes"].insert_one(note)
            note.pop("_id", None)
            return note
        except Exception as e:
            print(f"[DB ERROR] create_note failed: {e}. Falling back to local.")
            
    # Local Fallback
    db_local = _load_local_db()
    new_id = db_local["last_id"] + 1
    note = {
        "id": new_id,
        "title": title,
        "content": content,
        "tags": tags or [],
        "links": links or [],
        "type": note_type,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    db_local["notes"].append(note)
    db_local["last_id"] = new_id
    _save_local_db(db_local)
    return note


def get_note(note_id: int) -> Optional[Dict[str, Any]]:
    """Get a note by ID."""
    if MONGODB_CONNECTED:
        try:
            note = db["notes"].find_one({"id": note_id})
            if note:
                note.pop("_id", None)
                return note
            return None
        except Exception as e:
            print(f"[DB ERROR] get_note failed: {e}. Falling back to local.")
            
    # Local Fallback
    db_local = _load_local_db()
    for note in db_local["notes"]:
        if note["id"] == note_id:
            return note
    return None


def get_all_notes() -> List[Dict[str, Any]]:
    """Get all notes, sorted by updated_at (newest first)."""
    if MONGODB_CONNECTED:
        try:
            cursor = db["notes"].find().sort("updated_at", -1)
            notes_list = []
            for note in cursor:
                note.pop("_id", None)
                notes_list.append(note)
            return notes_list
        except Exception as e:
            print(f"[DB ERROR] get_all_notes failed: {e}. Falling back to local.")
            
    # Local Fallback
    db_local = _load_local_db()
    return sorted(db_local["notes"], key=lambda x: x.get("updated_at", ""), reverse=True)


def update_note(
    note_id: int,
    title: str = None,
    content: str = None,
    tags: List[str] = None,
    links: List[int] = None
) -> Optional[Dict[str, Any]]:
    """Update an existing note."""
    if MONGODB_CONNECTED:
        try:
            update_fields = {"updated_at": datetime.now().isoformat()}
            if title is not None:
                update_fields["title"] = title
            if content is not None:
                update_fields["content"] = content
            if tags is not None:
                update_fields["tags"] = tags
            if links is not None:
                update_fields["links"] = links
                
            res = db["notes"].find_one_and_update(
                {"id": note_id},
                {"$set": update_fields},
                return_document=True
            )
            if res:
                res.pop("_id", None)
                return res
            return None
        except Exception as e:
            print(f"[DB ERROR] update_note failed: {e}. Falling back to local.")
            
    # Local Fallback
    db_local = _load_local_db()
    for note in db_local["notes"]:
        if note["id"] == note_id:
            if title is not None:
                note["title"] = title
            if content is not None:
                note["content"] = content
            if tags is not None:
                note["tags"] = tags
            if links is not None:
                note["links"] = links
            note["updated_at"] = datetime.now().isoformat()
            _save_local_db(db_local)
            return note
    return None


def delete_note(note_id: int) -> bool:
    """Delete a note by ID."""
    if MONGODB_CONNECTED:
        try:
            res = db["notes"].delete_one({"id": note_id})
            # Remove from links in other notes
            db["notes"].update_many(
                {"links": note_id},
                {"$pull": {"links": note_id}}
            )
            return res.deleted_count > 0
        except Exception as e:
            print(f"[DB ERROR] delete_note failed: {e}. Falling back to local.")
            
    # Local Fallback
    db_local = _load_local_db()
    original_len = len(db_local["notes"])
    db_local["notes"] = [n for n in db_local["notes"] if n["id"] != note_id]
    
    # Remove from links in other notes
    for note in db_local["notes"]:
        if note_id in note.get("links", []):
            note["links"].remove(note_id)
            
    if len(db_local["notes"]) < original_len:
        _save_local_db(db_local)
        return True
    return False


# === SEARCH & QUERY ===

def search_notes(query: str) -> List[Dict[str, Any]]:
    """Search notes by title, content, or tags."""
    if not query or not query.strip():
        return get_all_notes()
        
    query = query.lower().strip()
    notes = get_all_notes()
    results = []
    
    for note in notes:
        score = 0
        if query in note["title"].lower():
            score += 10
        for tag in note.get("tags", []):
            if query in tag.lower():
                score += 5
        if query in note.get("content", "").lower():
            score += 3
            
        if score > 0:
            results.append((score, note))
            
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results]


def get_notes_by_tag(tag: str) -> List[Dict[str, Any]]:
    """Get all notes with a specific tag."""
    if MONGODB_CONNECTED:
        try:
            cursor = db["notes"].find({"tags": {"$regex": f"^{re.escape(tag)}$", "$options": "i"}})
            notes_list = []
            for note in cursor:
                note.pop("_id", None)
                notes_list.append(note)
            return notes_list
        except Exception as e:
            print(f"[DB ERROR] get_notes_by_tag failed: {e}. Falling back to local.")
            
    # Local Fallback
    db_local = _load_local_db()
    return [n for n in db_local["notes"] if tag.lower() in [t.lower() for t in n.get("tags", [])]]


def get_linked_notes(note_id: int) -> List[Dict[str, Any]]:
    """Get all notes linked to a specific note."""
    note = get_note(note_id)
    if not note:
        return []
        
    linked = []
    for link_id in note.get("links", []):
        linked_note = get_note(link_id)
        if linked_note:
            linked.append(linked_note)
    return linked


def get_all_tags() -> List[str]:
    """Get all unique tags across all notes."""
    if MONGODB_CONNECTED:
        try:
            tags = db["notes"].distinct("tags")
            return sorted(list(set(t for t in tags if t)))
        except Exception as e:
            print(f"[DB ERROR] get_all_tags failed: {e}. Falling back to local.")
            
    # Local Fallback
    db_local = _load_local_db()
    tags = set()
    for note in db_local["notes"]:
        for tag in note.get("tags", []):
            tags.add(tag)
    return sorted(list(tags))


# === UTILITY ===

def save_note(note_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simplified save function for external use."""
    return create_note(
        title=note_data.get("title", "Untitled"),
        content=note_data.get("content", ""),
        tags=note_data.get("tags", []),
        note_type=note_data.get("type", "note")
    )


def get_note_preview(note: Dict[str, Any], max_len: int = 100) -> str:
    """Get a preview of note content."""
    content = note.get("content", "")
    preview = re.sub(r'[#*_`\[\]]', '', content)
    if len(preview) > max_len:
        return preview[:max_len] + "..."
    return preview


# === STATS ===

def get_stats() -> Dict[str, Any]:
    """Get notes statistics."""
    notes = get_all_notes()
    return {
        "total_notes": len(notes),
        "total_tags": len(get_all_tags()),
        "by_type": {
            "note": len([n for n in notes if n.get("type") == "note"]),
            "chat_log": len([n for n in notes if n.get("type") == "chat_log"]),
            "brainstorm": len([n for n in notes if n.get("type") == "brainstorm"])
        }
    }
