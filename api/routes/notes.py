from typing import Optional
from fastapi import APIRouter, HTTPException
from api.schemas import NotesAIRequest, NotesAIResponse, NoteCreate, NoteUpdate, FileImportRequest
from api.utils import safe_print

try:
    from api.notes_ai import (
        refine_text,
        process_micro_ai,
        auto_tag,
        chat_with_context,
        generate_title,
        generate_metadata_pydantic,
        smart_insert_into_note,
        generate_study_note,
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
            smart_insert_into_note,
            generate_study_note,
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
        if not question or not str(question).strip():
            raise HTTPException(status_code=400, detail="question is required for chat")
        ctx_content = content if (content and content.strip()) else "(Catatan masih kosong)"
        result = chat_with_context(
            ctx_content,
            question,
            history=request.history,
            web_search=bool(request.web_search),
        )
    elif action == "smart_insert":
        if not request.insert_content or not str(request.insert_content).strip():
            raise HTTPException(status_code=400, detail="insert_content is required for smart_insert")
        result = smart_insert_into_note(
            note_content=content or "",
            insert_content=request.insert_content,
            mode=request.insert_mode or "contextual",
            target_heading=request.target_heading or "",
        )
    elif action == "study_note":
        if not content or not str(content).strip():
            raise HTTPException(status_code=400, detail="content is required for study_note")
        result = generate_study_note(
            content,
            source_name=request.source_name or "",
            style=request.style or "comprehensive",
        )
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

@router.post("/notes/import_file")
async def import_document_file(request: FileImportRequest):
    if not request.filename or not request.content:
        raise HTTPException(status_code=400, detail="filename and content are required")
    from modules.notes.file_importer import parse_uploaded_document
    from modules.notes.note_storage import create_note
    try:
        parsed = parse_uploaded_document(request.filename, request.content, request.mime_type or "")
        created_note = None
        if request.create_note:
            created_note = create_note(
                title=parsed["title"],
                content=parsed["markdown"],
                tags=parsed["tags"]
            )
        return {"parsed": parsed, "note": created_note}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mengurai dokumen: {e}")

@router.get("/notes/{id}")
async def retrieve_note(id: str):
    if not id or id in ("undefined", "null", "[object Object]"):
        raise HTTPException(status_code=400, detail="Invalid note ID")
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
async def update_existing_note(id: str, request: NoteUpdate):
    if not id or id in ("undefined", "null", "[object Object]"):
        raise HTTPException(status_code=400, detail="Invalid note ID")
    from modules.notes.note_storage import update_note
    try:
        note = update_note(note_id=id, title=request.title, content=request.content, tags=request.tags)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update note: {e}")

@router.delete("/notes/{id}")
async def delete_existing_note(id: str):
    if not id or id in ("undefined", "null", "[object Object]"):
        raise HTTPException(status_code=400, detail="Invalid note ID")
    from modules.notes.note_storage import delete_note
    try:
        success = delete_note(id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {e}")
