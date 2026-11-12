import time
from fastapi import APIRouter, HTTPException
from api.schemas import ChatRequest, ChatResponse
from api.utils import get_cortex, safe_print

router = APIRouter()

@router.get("/status")
async def status_endpoint():
    """Retrieve dynamic status of AI systems (Local, Cloud, Crew, OpenRouter)."""
    try:
        from modules.core.cortex import (
            OLLAMA_AVAILABLE,
            GROQ_AVAILABLE,
            OPENROUTER_AVAILABLE,
            CREW_AVAILABLE,
            HUGGINGFACE_AVAILABLE,
        )
        from modules.core.database import get_database, MONGODB_ERROR
        _db = get_database()
        return {
            "local": "online" if OLLAMA_AVAILABLE else "offline",
            "cloud": "online" if GROQ_AVAILABLE else "offline",
            "crew": "online" if CREW_AVAILABLE else "offline",
            "openrouter": "online" if OPENROUTER_AVAILABLE else "offline",
            "huggingface": "online" if HUGGINGFACE_AVAILABLE else "offline",
            "mongodb": "online" if _db is not None else "offline",
            "mongodb_error": MONGODB_ERROR,
        }
    except Exception as e:
        return {
            "local": "offline",
            "cloud": "offline",
            "crew": "offline",
            "openrouter": "offline",
            "huggingface": "offline",
            "error": str(e)
        }

@router.post("/chat", response_model=ChatResponse)
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
            safe_print(f"[WARN] Ancestor Echo check skipped: {ae}")

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
