from typing import List, Optional, Dict, Any
from pydantic import BaseModel

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
    style: Optional[str] = "structured"
    micro_type: Optional[str] = "refine"

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

class SessionsPayload(BaseModel):
    sessions: List[Dict[str, Any]] = []
    active_id: Optional[str] = None
