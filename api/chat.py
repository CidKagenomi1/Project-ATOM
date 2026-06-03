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

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Try Groq
try:
    from langchain_groq import ChatGroq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# Try Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

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


def call_openai_compatible(url: str, api_key: str, model: str, messages: list) -> str:
    import urllib.request
    import json
    
    formatted_messages = []
    for msg in messages:
        role = "user"
        if msg.__class__.__name__ == "SystemMessage":
            role = "system"
        elif msg.__class__.__name__ == "AIMessage":
            role = "assistant"
        formatted_messages.append({"role": role, "content": msg.content})
        
    data = json.dumps({
        "model": model,
        "messages": formatted_messages
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=15) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res["choices"][0]["message"]["content"]


def call_ai(messages: list, model_preference: str = "auto", image_files: list = None) -> tuple[str, str]:
    """
    Try specified model first, or run standard fallback:
    Groq -> Fireworks -> OpenRouter -> DeepSeek -> Gemini
    Returns (response_text, model_name)
    """
    
    # 1. Define call functions for each provider for clean execution
    def try_groq():
        if HAS_GROQ and os.environ.get("GROQ_API_KEY"):
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=os.environ.get("GROQ_API_KEY"),
                temperature=0.7,
                max_tokens=2048
            )
            response = llm.invoke(messages)
            return response.content, "Groq-Llama-70B"
        raise ValueError("Groq not configured")

    def try_fireworks(pref_model=None):
        if os.environ.get("FIREWORKS_API_KEY"):
            if pref_model:
                model = pref_model
            else:
                models = [m.strip() for m in os.environ.get("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p1-70b-instruct").split(",") if m.strip()]
                model = models[0] if models else "accounts/fireworks/models/llama-v3p1-70b-instruct"
            content = call_openai_compatible(
                "https://api.fireworks.ai/inference/v1/chat/completions",
                os.environ.get("FIREWORKS_API_KEY"),
                model,
                messages
            )
            return content, f"Fireworks-{model.split('/')[-1]}"
        raise ValueError("Fireworks not configured")

    def try_openrouter(pref_model=None):
        if os.environ.get("OPENROUTER_API_KEY"):
            if pref_model:
                models = [pref_model]
            else:
                models_str = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
                models = [m.strip() for m in models_str.split(",") if m.strip()]
            
            import urllib.request
            import json
            
            formatted_messages = []
            for i, msg in enumerate(messages):
                role = "user"
                if msg.__class__.__name__ == "SystemMessage":
                    role = "system"
                elif msg.__class__.__name__ == "AIMessage":
                    role = "assistant"
                
                # For OpenRouter, if it's the last human message and we have images, construct a multimodal payload
                if i == len(messages) - 1 and msg.__class__.__name__ == "HumanMessage" and image_files:
                    content_list = [{"type": "text", "text": msg.content}]
                    for img in image_files:
                        content_list.append({
                            "type": "image_url",
                            "image_url": {"url": img["content"]}
                        })
                    formatted_messages.append({"role": role, "content": content_list})
                else:
                    formatted_messages.append({"role": role, "content": msg.content})
                
            payload = {"messages": formatted_messages}
            if len(models) > 1:
                payload["models"] = models
                display_name = f"OpenRouter-{models[0].split('/')[-1]}-Multi"
            else:
                payload["model"] = models[0] if models else "meta-llama/llama-3.1-8b-instruct"
                display_name = f"OpenRouter-{payload['model'].split('/')[-1]}"
                
            data = json.dumps(payload).encode("utf-8")
            
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=data,
                headers={
                    "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                res = json.loads(response.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"], display_name
        raise ValueError("OpenRouter not configured")

    def try_deepseek():
        if os.environ.get("DEEPSEEK_API_KEY"):
            model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
            content = call_openai_compatible(
                "https://api.deepseek.com/chat/completions",
                os.environ.get("DEEPSEEK_API_KEY"),
                model,
                messages
            )
            return content, f"DeepSeek-{model}"
        raise ValueError("DeepSeek not configured")

    def try_gemini():
        if HAS_GEMINI and os.environ.get("GOOGLE_API_KEY"):
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.environ.get("GOOGLE_API_KEY"),
                temperature=0.7
            )
            
            # Reconstruct human message content with images for Gemini if present
            gemini_messages = list(messages)
            if image_files and gemini_messages:
                last_msg = gemini_messages[-1]
                if last_msg.__class__.__name__ == "HumanMessage":
                    content_list = [{"type": "text", "text": last_msg.content}]
                    for img in image_files:
                        content_list.append({
                            "type": "image_url",
                            "image_url": {"url": img["content"]}
                        })
                    gemini_messages[-1] = HumanMessage(content=content_list)
                    
            response = llm.invoke(gemini_messages)
            content = response.content
            if isinstance(content, list):
                content = content[0].get("text", str(content[0])) if content else ""
            return str(content), "Gemini-Flash"
        raise ValueError("Gemini not configured")

    # 2. Execution order
    call_funcs = {
        "groq": try_groq,
        "fireworks": try_fireworks,
        "openrouter": try_openrouter,
        "deepseek": try_deepseek,
        "gemini": try_gemini
    }
    
    pref_provider = model_preference
    pref_model = None
    if ":" in model_preference and not model_preference.startswith("accounts/"):
        parts = model_preference.split(":", 1)
        if parts[0] in call_funcs:
            pref_provider = parts[0]
            pref_model = parts[1]
            
    if pref_provider in call_funcs:
        try:
            if pref_model:
                return call_funcs[pref_provider](pref_model)
            else:
                return call_funcs[pref_provider]()
        except Exception as e:
            print(f"[PREFERENCE ERROR] Preferred model {model_preference} failed: {e}. Falling back...")
            
    fallback_chain = ["groq", "fireworks", "openrouter", "deepseek", "gemini"]
    for provider in fallback_chain:
        if provider == pref_provider:
            continue
        try:
            return call_funcs[provider]()
        except Exception as e:
            print(f"[FALLBACK ERROR] {provider} failed: {e}")
            
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

        if not prompt and not files:
            self._send_json({"error": "prompt is required"}, 400)
            return

        if not prompt and files:
            # Check if there are images
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

        thinking = []

        # Route
        route = get_route(prompt)
        thinking.append({"step": "[ROUTER]", "detail": f"Route: **{route}**"})

        if route == "CREW":
            thinking.append({"step": "[CREW]", "detail": "CrewAI tidak tersedia di versi web. Melanjutkan dengan AI standar..."})

        model_preference = data.get("model_preference", "auto")
        thinking.append({"step": "[AI]", "detail": f"Cloud mode aktif (Preference: {model_preference.upper()})"})

        messages = build_messages(SYSTEM_PROMPT, history, prompt)
        response_text, model_name = call_ai(messages, model_preference, image_files)

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
