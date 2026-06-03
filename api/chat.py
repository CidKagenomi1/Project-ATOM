"""
A.T.O.M. - Chat API Endpoint (Vercel Serverless Function)
POST /api/chat
Body: { "prompt": str, "history": list, "files": list }
Response: { "response": str, "model": str, "thinking": list }

This is a cloud-only wrapper around cortex.py logic.
Ollama (local model) is intentionally skipped for Vercel compatibility.
"""

import os
import json
import time
from http.server import BaseHTTPRequestHandler

# Try Groq
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = bool(os.environ.get("GROQ_API_KEY"))
except ImportError:
    GROQ_AVAILABLE = False

# Try Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = bool(os.environ.get("GOOGLE_API_KEY"))
except ImportError:
    GEMINI_AVAILABLE = False

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


# --- System Prompt (sama dengan cortex.py) ---
SYSTEM_PROMPT = """IDENTITY: Kamu adalah ATOM (Autonomous Task Orchestration Machine).
STYLE: Cerdas, efisien, sedikit witty seperti Jarvis. Percaya diri tapi tetap helpful.
LANGUAGE: Bahasa Indonesia. Mix English untuk istilah teknis.
RULES:
- Jawab to the point, tidak bertele-tele
- Kalau ada kode, format dengan markdown code blocks
- Kalau ditanya hal teknis, berikan contoh konkret"""


def get_route(text: str) -> str:
    """Simple keyword router."""
    txt = text.lower()
    crew_kw = ["riset", "research", "analisis mendalam", "investigasi", "pelajari secara mendalam"]
    if any(kw in txt for kw in crew_kw):
        return "CREW"
    return "AI"


def build_messages(system: str, history: list, prompt: str) -> list:
    """Build LangChain message list from history."""
    messages = [SystemMessage(content=system)]
    for msg in history[-6:]:  # Last 3 exchanges = 6 messages
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=prompt))
    return messages


def call_ai(messages: list) -> tuple[str, str]:
    """
    Try Groq first (faster), fallback to Gemini.
    Returns (response_text, model_name)
    """
    # Try Groq
    if GROQ_AVAILABLE:
        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=os.environ.get("GROQ_API_KEY"),
                temperature=0.7,
                max_tokens=2048
            )
            response = llm.invoke(messages)
            return response.content, "Groq-Llama-70B"
        except Exception as e:
            print(f"[GROQ ERROR] {e}")

    # Fallback to Gemini
    if GEMINI_AVAILABLE:
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.environ.get("GOOGLE_API_KEY"),
                temperature=0.7
            )
            response = llm.invoke(messages)
            content = response.content
            if isinstance(content, list):
                content = content[0].get("text", str(content[0])) if content else ""
            return str(content), "Gemini-Flash"
        except Exception as e:
            print(f"[GEMINI ERROR] {e}")

    return "Semua AI server sedang tidak tersedia. Cek API keys di Vercel Environment Variables.", "OFFLINE"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        start_time = time.time()

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
        except Exception as e:
            self._send_json({"error": f"Invalid request body: {e}"}, 400)
            return

        prompt = data.get("prompt", "").strip()
        history = data.get("history", [])
        files = data.get("files", [])  # [{"name": str, "content": str}]

        if not prompt:
            self._send_json({"error": "prompt is required"}, 400)
            return

        # Prepend file context to prompt if any
        if files:
            file_context_parts = []
            for f in files:
                file_context_parts.append(f"[FILE: {f['name']}]\n{f['content']}\n[END FILE]")
            prompt = "\n\n".join(file_context_parts) + f"\n\nQuery: {prompt}"

        thinking = []

        # Route
        route = get_route(prompt)
        thinking.append({"step": "[ROUTER]", "detail": f"Route: **{route}**"})

        if route == "CREW":
            thinking.append({"step": "[CREW]", "detail": "CrewAI tidak tersedia di versi web. Melanjutkan dengan AI standar..."})

        # Always use AI (no Ollama, no system actions in web)
        thinking.append({"step": "[AI]", "detail": "Cloud mode aktif (Groq → Gemini failover)"})

        messages = build_messages(SYSTEM_PROMPT, history, prompt)
        response_text, model_name = call_ai(messages)

        duration = round(time.time() - start_time, 2)
        thinking.append({"step": "[LOG]", "detail": f"Time: {duration}s | Model: {model_name}"})

        self._send_json({
            "response": response_text,
            "model": model_name,
            "thinking": thinking,
            "duration": duration
        })

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
        pass  # Suppress default logging
