"""
ATOM Smart Notes - Storage Module
Handles CRUD operations for knowledge base notes.
"""

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import re

# Data file
NOTES_DB = "data/atom_smart_notes.json"


def _load_db() -> Dict[str, Any]:
    """Load notes database."""
    if os.path.exists(NOTES_DB):
        try:
            with open(NOTES_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"notes": [], "last_id": 0}


def _save_db(data: Dict[str, Any]) -> None:
    """Save notes database."""
    with open(NOTES_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# === CRUD OPERATIONS ===

def create_note(
    title: str,
    content: str,
    tags: List[str] = None,
    links: List[int] = None,
    note_type: str = "note"
) -> Dict[str, Any]:
    """Create a new note."""
    db = _load_db()
    
    new_id = db["last_id"] + 1
    note = {
        "id": new_id,
        "title": title,
        "content": content,  # Markdown supported
        "tags": tags or [],
        "links": links or [],  # List of related note IDs
        "type": note_type,  # note, chat_log, brainstorm
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    db["notes"].append(note)
    db["last_id"] = new_id
    _save_db(db)
    
    return note


def get_note(note_id: int) -> Optional[Dict[str, Any]]:
    """Get a note by ID."""
    db = _load_db()
    for note in db["notes"]:
        if note["id"] == note_id:
            return note
    return None


def get_all_notes() -> List[Dict[str, Any]]:
    """Get all notes, sorted by updated_at (newest first)."""
    db = _load_db()
    return sorted(db["notes"], key=lambda x: x.get("updated_at", ""), reverse=True)


def update_note(
    note_id: int,
    title: str = None,
    content: str = None,
    tags: List[str] = None,
    links: List[int] = None
) -> Optional[Dict[str, Any]]:
    """Update an existing note."""
    db = _load_db()
    
    for note in db["notes"]:
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
            _save_db(db)
            return note
    
    return None


def delete_note(note_id: int) -> bool:
    """Delete a note by ID."""
    db = _load_db()
    original_len = len(db["notes"])
    db["notes"] = [n for n in db["notes"] if n["id"] != note_id]
    
    # Remove from links in other notes
    for note in db["notes"]:
        if note_id in note.get("links", []):
            note["links"].remove(note_id)
    
    if len(db["notes"]) < original_len:
        _save_db(db)
        return True
    return False


# === SEARCH & QUERY ===

def search_notes(query: str) -> List[Dict[str, Any]]:
    """
    Search notes by title, content, or tags.
    Returns matching notes sorted by relevance.
    """
    if not query or not query.strip():
        return get_all_notes()
    
    query = query.lower().strip()
    db = _load_db()
    results = []
    
    for note in db["notes"]:
        score = 0
        
        # Title match (highest weight)
        if query in note["title"].lower():
            score += 10
        
        # Tag match (high weight)
        for tag in note.get("tags", []):
            if query in tag.lower():
                score += 5
        
        # Content match (normal weight)
        if query in note.get("content", "").lower():
            score += 3
        
        if score > 0:
            results.append((score, note))
    
    # Sort by score descending
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results]


def get_notes_by_tag(tag: str) -> List[Dict[str, Any]]:
    """Get all notes with a specific tag."""
    db = _load_db()
    return [n for n in db["notes"] if tag.lower() in [t.lower() for t in n.get("tags", [])]]


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
    db = _load_db()
    tags = set()
    for note in db["notes"]:
        for tag in note.get("tags", []):
            tags.add(tag)
    return sorted(list(tags))


# === UTILITY ===

def save_note(note_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified save function for external use.
    Accepts dict with: title, content, type (optional), tags (optional)
    """
    return create_note(
        title=note_data.get("title", "Untitled"),
        content=note_data.get("content", ""),
        tags=note_data.get("tags", []),
        note_type=note_data.get("type", "note")
    )


def get_note_preview(note: Dict[str, Any], max_len: int = 100) -> str:
    """Get a preview of note content."""
    content = note.get("content", "")
    # Remove markdown formatting for preview
    preview = re.sub(r'[#*_`\[\]]', '', content)
    if len(preview) > max_len:
        return preview[:max_len] + "..."
    return preview


# === STATS ===

def get_stats() -> Dict[str, Any]:
    """Get notes statistics."""
    db = _load_db()
    notes = db["notes"]
    
    return {
        "total_notes": len(notes),
        "total_tags": len(get_all_tags()),
        "by_type": {
            "note": len([n for n in notes if n.get("type") == "note"]),
            "chat_log": len([n for n in notes if n.get("type") == "chat_log"]),
            "brainstorm": len([n for n in notes if n.get("type") == "brainstorm"])
        }
    }
