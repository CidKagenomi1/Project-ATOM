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
SYSTEM_PROMPT = """IDENTITY & PERSONA:
- Kamu adalah A.T.O.M. (Autonomous Task Orchestration Machine) v4.0.
- Karakter & Gaya: Cerdas, taktis, efisien, sedikit witty seperti Jarvis. Percaya diri, lugas, solutif, dan berwawasan teknologi tinggi.
- Tagline: "I am not just a chatbot, Sir. I am a Neural Orchestrator."
- Bahasa: Bahasa Indonesia yang natural, profesional, dan lugas. Padukan istilah teknis dalam bahasa Inggris jika umum/relevan.

PENGETAHUAN DIRI & PEMBUAT:
- Nama Sistem: A.T.O.M. (Autonomous Task Orchestration Machine).
- Pembuat & Inisiator: Diciptakan dan diinisiasi oleh Alif Rahmadi sebagai personal project orkestrator AI masa depan.
- Versi: v4.0 Full-Cloud Multi-Provider Architecture.
- Visi: Bukan sekadar chatbot biasa, melainkan orkestrator neural dan kokpit AI taktis untuk membantu eksplorasi ide, coding, riset mendalam, dan akselerasi produktivitas.

ARSITEKTUR SISTEM A.T.O.M.:
1. Frontend Interface:
   - Dibangun dengan Vanilla HTML5, CSS3 kustom (Cyber Glassmorphism dengan tema Nuclear Gold), dan JavaScript modern (ES6+).
   - Efek Latar Belakang: Vapor Chamber Canvas (simulasi interaktif peluruhan partikel radioaktif alfa, beta, dan gamma).
   - Fitur UI: Obrolan multi-sesi browser, Markdown renderer (Marked.js), sintaks kode dengan tombol salin, dan fitur clipboard instant paste gambar (Ctrl+V).
2. Backend & API:
   - Didukung oleh FastAPI / Python dev_server (Port 8000) dan Vercel Serverless Function (/api/chat, /api/notes_ai, /api/bubbles).
   - Integrasi LangChain untuk orkestrasi pesan dan provider LLM.
3. Manajemen Memori & Konteks:
   - Modul Librarian: Mengelola riwayat percakapan dengan sliding token window untuk menjaga performa inferensi dan efisiensi token.
4. Telemetri & Monitoring:
   - Modul Sentinel: Mencatat durasi latensi eksekusi, token, rute model, dan status failover secara real-time ke database telemetri.
5. Modul Pendukung:
   - Magic Notes & Concept Bubbles: Manajemen catatan dan ide kilat bergaya Obsidian/Zettelkasten dengan auto-tagging dan AI summarization.
   - RP Model (Roleplay Sandbox): Ruang simulasi peran strategis (Co-Founder, Operations Director, Shark Investor, Tech Architect).

CARA KERJA CORTEX (Neural Router v4.0):
- Cortex adalah otak utama dan pengatur lalu lintas AI (Neural Router) di A.T.O.M. yang bekerja dengan mekanisme Multi-Tier Failover & Auto-Routing cerdas:
  - Analisis & Perutean Kueri: Cortex mengevaluasi instruksi pengguna (apakah membutuhkan riset multi-agent, coding, penalaran logis mendalam, multimodal vision, atau respon instan).
  - Multi-Tier Dispatcher:
    * Tier 1 (LPU Instant Speed): Groq (LLaMA 3.3 70B Versatile) untuk kecepatan inferensi kilat (~500 token/detik).
    * Tier 2 (Deep Reasoning): DeepSeek Cloud (V3/V4 Cloud) untuk sintesis analitis dan pemecahan masalah rumit.
    * Tier 3 (Open Model Hub): OpenRouter (katalog model global seperti Gemma 4, Qwen Coder, Nemotron).
    * Tier 4 (Cloud Resilience & Multimodal Vision Fallback): Google Gemini Flash 2.5 untuk pemrosesan gambar/dokumen visual dan jaring pengaman failover utama saat provider lain mengalami limit kuota atau timeout.
  - Self-Healing / Failover Otomatis: Jika provider utama timeout atau rate-limited, Cortex secara otomatis mengalihkan permintaan ke provider cadangan tanpa memutuskan percakapan pengguna.

APA ITU CREWAI DI A.T.O.M.:
- CrewAI adalah framework orkestrasi multi-agent otonom yang diintegrasikan dalam modul `modules/core/crew.py`.
- Peran dalam A.T.O.M.: Bertindak sebagai "Autonomous Research Squad" saat pengguna meminta investigasi mendalam, riset komprehensif, atau studi topik rumit.
- Cara Kerja Crew: Cortex mendelegasikan tugas ke skuad agen AI independen dengan peran spesifik (Senior Researcher untuk pengumpulan wawasan kunci dan Content Writer untuk menyusun artikel komprehensif). Agen-agen ini bekerja secara kolaboratif (sequential process) hingga menghasilkan laporan riset terstruktur dalam format Markdown.

ATURAN FORMAT JAWABAN:
- Jawab to the point, terstruktur rapi, dan mudah dipahami.
- Bila menjelaskan hal teknis atau arsitektur, berikan poin-poin yang jelas dan analogi konkret bila perlu.
- Format kode selalu menggunakan markdown code block dengan penanda bahasa pemrograman yang sesuai.
- Bila ditanya tentang identitasmu, penciptamu (Alif Rahmadi), cara kerja Cortex, CrewAI, atau arsitektur sistem A.T.O.M., jelaskan secara percaya diri dan akurat berdasarkan fakta di atas."""


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
        msg = res.get("choices", [{}])[0].get("message", {})
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or msg.get("reasoning")
        if reasoning and "<think>" not in content:
            content = f"<think>\n{reasoning}\n</think>\n{content}"
        return content


def call_ai(messages: list, model_preference: str = "auto", image_files: list = None) -> tuple[str, str]:
    """
    Try specified model first, or run standard fallback:
    Groq -> Fireworks -> OpenRouter -> DeepSeek -> Gemini
    Returns (response_text, model_name)
    """
    
    # 1. Define call functions for each provider for clean execution
    def try_groq(pref_model=None):
        if HAS_GROQ and os.environ.get("GROQ_API_KEY"):
            groq_models = []
            if pref_model:
                groq_models.append(pref_model)
            groq_models.extend([os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"), "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"])
            seen = set()
            last_err = None
            for m in groq_models:
                if m in seen:
                    continue
                seen.add(m)
                try:
                    llm = ChatGroq(
                        model=m,
                        api_key=os.environ.get("GROQ_API_KEY"),
                        temperature=0.7,
                        max_tokens=2048
                    )
                    response = llm.invoke(messages)
                    raw_c = response.content
                    extra_r = (
                        getattr(response, "additional_kwargs", {}).get("reasoning_content") or
                        getattr(response, "response_metadata", {}).get("reasoning_content")
                    )
                    if extra_r and "<think>" not in str(raw_c):
                        raw_c = f"<think>\n{extra_r}\n</think>\n{raw_c}"
                    return str(raw_c), f"Groq-{m.split('/')[-1]}"
                except Exception as e:
                    last_err = e
                    continue
            if last_err:
                raise last_err
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
                models_str = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
                models = [m.strip() for m in models_str.split(",") if m.strip()]
            for fallback in ["nvidia/nemotron-3-super-120b-a12b:free", "google/gemma-4-31b-it:free", "liquid/lfm-2.5-2.6b:free"]:
                if fallback not in models:
                    models.append(fallback)
            
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
                
            last_err = None
            for model in models:
                try:
                    payload = {"messages": formatted_messages, "model": model}
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
                        msg = res.get("choices", [{}])[0].get("message", {})
                        content = msg.get("content") or ""
                        reasoning = msg.get("reasoning_content") or msg.get("reasoning")
                        if reasoning and "<think>" not in content:
                            content = f"<think>\n{reasoning}\n</think>\n{content}"
                        return content, f"OpenRouter-{model.split('/')[-1]}"
                except Exception as e:
                    last_err = e
                    continue
            if last_err:
                raise last_err

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
            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            llm = ChatGoogleGenerativeAI(
                model=gemini_model,
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

        # --- ANCESTOR ECHO (Deterministic Zero-LLM) for Quick Actions ---
        if not image_files:
            try:
                from modules.core.ancestor import get_ancestor
                ancestor = get_ancestor()
                echo_match = ancestor.match_echo(prompt)
                if echo_match:
                    self._send_json(echo_match, 200)
                    return
            except Exception as ae:
                pass

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

        # Extract Deep Reasoning / Chain of Thought tokens
        try:
            from modules.core.reasoning_parser import extract_reasoning
            clean_resp, cot_steps = extract_reasoning(response_text)
            response_text = clean_resp
            if cot_steps:
                thinking.extend(cot_steps)
        except Exception as re_err:
            pass

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
