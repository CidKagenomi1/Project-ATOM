from typing import Optional
from fastapi import APIRouter, HTTPException
from api.schemas import NotesAIRequest, NotesAIResponse, NoteCreate, NoteUpdate
from api.utils import safe_print

try:
    from api.notes_ai import (
        refine_text,
        process_micro_ai,
        auto_tag,
        chat_with_context,
        generate_title,
        generate_metadata_pydantic,
    )
except ImportError:
    try:
        from notes_ai import (
            refine_text,
            process_micro_ai,
            auto_tag,
            chat_with_context,
            generate_title,
            generate_metadata_pydantic,
        )
    except Exception as e:
        safe_print(f"[WARN] notes_ai import fallback: {e}")

router = APIRouter()

@router.post("/notes_ai", response_model=NotesAIResponse)
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
        style = request.style or "structured"
        result = refine_text(content, style=style)
    elif action == "micro":
        if not content:
            raise HTTPException(status_code=400, detail="content is required for micro AI")
        micro_type = request.micro_type or "refine"
        result = process_micro_ai(content, micro_type=micro_type)
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

@router.get("/notes")
async def list_notes(query: Optional[str] = None):
    from modules.notes.note_storage import get_all_notes, search_notes
    if query:
        return search_notes(query)
    return get_all_notes()

@router.get("/notes/tags")
async def list_tags():
    from modules.notes.note_storage import get_all_tags
    return get_all_tags()

@router.get("/notes/{id}")
async def retrieve_note(id: int):
    from modules.notes.note_storage import get_note
    note = get_note(id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.post("/notes")
async def create_new_note(request: NoteCreate):
    from modules.notes.note_storage import create_note
    try:
        return create_note(title=request.title, content=request.content, tags=request.tags)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create note: {e}")

@router.put("/notes/{id}")
async def update_existing_note(id: int, request: NoteUpdate):
    from modules.notes.note_storage import update_note
    try:
        note = update_note(note_id=id, title=request.title, content=request.content, tags=request.tags)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update note: {e}")

@router.delete("/notes/{id}")
async def delete_existing_note(id: int):
    from modules.notes.note_storage import delete_note
    try:
        success = delete_note(id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {e}")
