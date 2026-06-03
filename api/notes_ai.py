"""
A.T.O.M. - Notes AI API Endpoint (Vercel Serverless)
POST /api/notes_ai
Body: { "action": "refine"|"autotag"|"chat"|"title", "content": str, "question": str }
Response: { "result": str|list }
"""

import os
import json
from http.server import BaseHTTPRequestHandler

# Try Groq first (primary for notes AI)
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = bool(os.environ.get("GROQ_API_KEY"))
except ImportError:
    GROQ_AVAILABLE = False

# Gemini fallback
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = bool(os.environ.get("GOOGLE_API_KEY"))
except ImportError:
    GEMINI_AVAILABLE = False

from langchain_core.messages import HumanMessage, SystemMessage


def get_llm(temperature: float = 0.3):
    """Get best available LLM."""
    if GROQ_AVAILABLE:
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=temperature
        )
    if GEMINI_AVAILABLE:
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=temperature
        )
    return None


def refine_text(raw_text: str) -> str:
    """Clean up messy text into structured markdown article."""
    llm = get_llm(0.3)
    if not llm:
        return raw_text

    system = SystemMessage(content="""Kamu adalah Editor Artikel Profesional.
Tugasmu: terima teks mentah → susun ulang menjadi Artikel Markdown rapi (Heading, Bullet points).
ATURAN:
1. Gunakan heading (##, ###) untuk struktur
2. Gunakan bullet points untuk list  
3. Perbaiki typo dan tata bahasa
4. Pertahankan semua informasi penting
5. Buat paragraf yang rapi
6. Jangan tambahkan informasi baru""")

    user = HumanMessage(content=f"TEKS MENTAH:\n---\n{raw_text[:4000]}\n---\nRapihkan menjadi artikel Markdown terstruktur:")
    
    try:
        response = llm.invoke([system, user])
        return response.content
    except Exception as e:
        return f"[ERROR] Gagal merapihkan: {str(e)}"


def auto_tag(text: str) -> list:
    """Generate 3-5 relevant tags from text."""
    llm = get_llm(0.1)
    if not llm:
        return []
    
    prompt = f"""Analyze this text and generate 3-5 relevant tags/keywords.
TEXT: {text[:2000]}
RULES:
- Tags should be single words or short phrases (max 2 words)
- Use lowercase
- Return ONLY the tags, one per line, no numbering
TAGS:"""
    
    try:
        response = llm.invoke(prompt)
        tags = []
        for line in response.content.strip().split('\n'):
            tag = line.strip().strip('-').strip('•').strip()
            if tag and len(tag) < 30:
                tags.append(tag.lower())
        return tags[:5]
    except Exception as e:
        print(f"[AUTOTAG ERROR] {e}")
        return []


def chat_with_context(context_text: str, question: str) -> str:
    """Answer question based ONLY on provided note content."""
    llm = get_llm(0.2)
    if not llm:
        return "AI tidak tersedia saat ini."
    
    system = SystemMessage(content="""Kamu adalah ATOM Knowledge Assistant.
RULES:
1. Jawab pertanyaan HANYA berdasarkan CONTEXT yang diberikan
2. Kalau jawabannya tidak ada di context, katakan "Informasi tersebut tidak ada dalam catatan ini."
3. Be concise and direct
4. Gunakan Bahasa Indonesia
5. Quote bagian relevan dari context kalau helpful""")
    
    user = HumanMessage(content=f"""CONTEXT (Isi Catatan):
---
{context_text}
---
PERTANYAAN: {question}
Jawab berdasarkan CONTEXT di atas:""")
    
    try:
        response = llm.invoke([system, user])
        return response.content
    except Exception as e:
        return f"[ERROR] Gagal memproses: {str(e)}"


def generate_title(content: str) -> str:
    """Generate concise title for note content."""
    llm = get_llm(0.2)
    if not llm:
        return "Untitled Note"
    
    prompt = f"""Generate a short, descriptive title (max 6 words) for this content:
{content[:500]}
Return ONLY the title, no quotes or extra formatting.
Use Indonesian if content is in Indonesian.
TITLE:"""
    
    try:
        response = llm.invoke(prompt)
        title = response.content.strip().strip('"').strip("'")
        return title[:60] if title else "Untitled Note"
    except:
        return "Untitled Note"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
        except Exception as e:
            self._send_json({"error": f"Invalid body: {e}"}, 400)
            return

        action = data.get("action", "")
        content = data.get("content", "")
        question = data.get("question", "")

        if not action:
            self._send_json({"error": "action is required"}, 400)
            return

        result = None

        if action == "refine":
            if not content:
                self._send_json({"error": "content is required for refine"}, 400)
                return
            result = refine_text(content)

        elif action == "autotag":
            if not content:
                self._send_json({"error": "content is required for autotag"}, 400)
                return
            result = auto_tag(content)

        elif action == "chat":
            if not content or not question:
                self._send_json({"error": "content and question are required for chat"}, 400)
                return
            result = chat_with_context(content, question)

        elif action == "title":
            if not content:
                self._send_json({"error": "content is required for title"}, 400)
                return
            result = generate_title(content)

        else:
            self._send_json({"error": f"Unknown action: {action}"}, 400)
            return

        self._send_json({"result": result})

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
