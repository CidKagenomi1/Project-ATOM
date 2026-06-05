"""
ATOM CORTEX v4.0 - Local First, Cloud Rescue
Otak utama ATOM dengan arsitektur Timeout Failover.
Primary: Ollama (Llama 3.2 Local) | Backup: Groq Cloud | Fallback: Gemini
"""

import os
import time
import json
import pandas as pd
from datetime import datetime
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(override=True)

def safe_print(*args, **kwargs):
    import sys
    import builtins
    try:
        enc = sys.stdout.encoding or 'cp1252' if (sys.stdout and hasattr(sys.stdout, 'encoding')) else 'cp1252'
        new_args = []
        for arg in args:
            if isinstance(arg, str):
                new_args.append(arg.encode(enc, errors='replace').decode(enc))
            else:
                new_args.append(arg)
        builtins.print(*new_args, **kwargs)
    except Exception:
        try:
            new_args = [str(arg).encode('ascii', errors='replace').decode('ascii') for arg in args]
            builtins.print(*new_args, **kwargs)
        except Exception:
            pass

print = safe_print


# --- CONFIG ---
LOCAL_TIMEOUT_SECONDS = 40  # Kill switch timeout for local model

# --- STATUS FLAGS ---
GROQ_AVAILABLE = bool(os.getenv("GROQ_API_KEY"))
FIREWORKS_AVAILABLE = False  # Terminated by user request
OPENROUTER_AVAILABLE = bool(os.getenv("OPENROUTER_API_KEY"))
DEEPSEEK_AVAILABLE = False  # Terminated by user request
GEMINI_AVAILABLE = bool(os.getenv("GOOGLE_API_KEY"))
OLLAMA_AVAILABLE = True  # Enabled by user request

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq
# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI
# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, SystemMessage

# Import CrewAI (optional)
CREW_AVAILABLE = False
try:
    from modules.core.crew import run_research_crew
    CREW_AVAILABLE = True
except ImportError:
    def run_research_crew(topic):
        return "[CREW OFFLINE] CrewAI belum terinstall. Jalankan: pip install crewai"


# --- OLLAMA LOCAL/CLOUD BRAIN WRAPPER ---
class LocalOllamaBrain:
    def __init__(self, host=None, model=None, api_key=None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "deepseek-v4-flash:cloud")
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")

    def invoke(self, messages):
        import urllib.request
        import json
        import ssl
        
        formatted_messages = []
        for msg in messages:
            role = "user"
            if msg.__class__.__name__ == "SystemMessage":
                role = "system"
            elif msg.__class__.__name__ == "AIMessage":
                role = "assistant"
            formatted_messages.append({"role": role, "content": msg.content})
            
        data = json.dumps({
            "model": self.model,
            "messages": formatted_messages,
            "stream": False
        }).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers=headers,
            method="POST"
        )
        
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ctx, timeout=120) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "message" in res and "content" in res["message"]:
                content = res["message"]["content"]
            elif "choices" in res:
                content = res["choices"][0]["message"]["content"]
            else:
                content = str(res)
            
            class SimpleResponse:
                def __init__(self, content):
                    self.content = content
            return SimpleResponse(content)


# --- 1. THE SENTINEL (Sistem Pengawas/Logger) ---
class Sentinel:
    def __init__(self, log_file="data/atom_telemetry.csv"):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            df = pd.DataFrame(columns=["timestamp", "user_input", "model_used", "response_time", "status"])
            df.to_csv(self.log_file, index=False, encoding='utf-8')

    def log(self, user_input, model_used, start_time, status="SUCCESS"):
        duration = round(time.time() - start_time, 2)
        try:
            new_data = pd.DataFrame([{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": user_input[:50] + "...",
                "model_used": model_used,
                "response_time": duration,
                "status": status
            }])
            new_data.to_csv(self.log_file, mode='a', header=False, index=False, encoding='utf-8')
        except Exception as e:
            print(f"[LOG ERROR] {e}")
        return duration


# --- 2. THE LIBRARIAN (Manajemen Konteks) ---
class Librarian:
    def __init__(self):
        self.raw_history = []
        self.summary = ""
    
    def add_interaction(self, user, ai):
        self.raw_history.append(f"User: {user}")
        self.raw_history.append(f"ATOM: {ai}")
        if len(self.raw_history) > 8:
            self.raw_history = self.raw_history[-6:]
            
    def get_context(self):
        return "\n".join(self.raw_history)
    
    def clear(self):
        self.raw_history = []
        self.summary = ""


# --- 3. THE DISPATCHER (Router Cepat) ---
class NeuralRouter:
    """Router berbasis keyword untuk kecepatan maksimal."""
    
    def decide_route(self, user_input):
        txt = user_input.lower()
        
        action_kw = ["buka", "open", "jalankan", "run", "cek", "check", 
                     "folder", "file", "baterai", "battery", "youtube",
                     "browser", "notepad", "calculator", "spotify"]
        if any(kw in txt for kw in action_kw):
            return "ACTION"
        
        crew_kw = ["riset", "research", "analisis mendalam", "investigasi", "pelajari"]
        if CREW_AVAILABLE and any(kw in txt for kw in crew_kw):
            return "CREW"
        
        return "AI"  # Changed from "CLOUD" to "AI" for new logic


# --- 4. THE CORTEX (Otak Utama dengan Timeout Failover) ---
class ATOMCortex:
    def __init__(self):
        print("[ATOM] Initializing CORTEX v4.0 - Local First, Cloud Rescue...")
        
        self.sentinel = Sentinel()
        self.librarian = Librarian()
        self.router = NeuralRouter()
        self.status_callback = None  # For UI status updates
        
        # OTAK LOKAL: OLLAMA (Enabled)
        self.local_brain = None
        if OLLAMA_AVAILABLE:
            self.local_brain = LocalOllamaBrain()
            print(f"[OK] LOCAL: Ollama wrapper initialized ({os.getenv('OLLAMA_MODEL', 'deepseek-v4-flash:cloud')})")
        
        # OTAK CLOUD: GROQ (Rescue)
        self.groq_brain = None
        if GROQ_AVAILABLE:
            try:
                self.groq_brain = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    api_key=os.getenv("GROQ_API_KEY"),
                    temperature=0.7
                )
                print("[OK] CLOUD: Groq Llama-70B")
            except Exception as e:
                print(f"[WARN] Groq failed: {e}")
        
        # OTAK CLOUD: FIREWORKS
        if FIREWORKS_AVAILABLE:
            print(f"[OK] CLOUD: Fireworks Model: {os.getenv('FIREWORKS_MODEL')}")
            
        # OTAK CLOUD: OPENROUTER
        if OPENROUTER_AVAILABLE:
            print(f"[OK] CLOUD: OpenRouter Model: {os.getenv('OPENROUTER_MODEL')}")
            
        # OTAK CLOUD: DEEPSEEK
        if DEEPSEEK_AVAILABLE:
            print(f"[OK] CLOUD: DeepSeek Model: {os.getenv('DEEPSEEK_MODEL')}")
        
        # OTAK CADANGAN: GEMINI (Last Resort)
        self.gemini_brain = None
        if GEMINI_AVAILABLE:
            try:
                gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                self.gemini_brain = ChatGoogleGenerativeAI(
                    model=gemini_model,
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    temperature=0.7
                )
                print(f"[OK] FALLBACK: Gemini model loaded ({gemini_model})")
            except Exception as e:
                print(f"[WARN] Gemini failed: {e}")
        
        print(f"[ATOM] All systems ready. Timeout: {LOCAL_TIMEOUT_SECONDS}s")
    
    def set_status_callback(self, callback):
        """Set callback function for UI status updates."""
        self.status_callback = callback
    
    def _update_status(self, message):
        """Update UI status if callback is set."""
        try:
            print(f"   [STATUS] {message}")
        except UnicodeEncodeError:
            try:
                import sys
                enc = sys.stdout.encoding or 'cp1252'
                safe_msg = message.encode(enc, errors='replace').decode(enc)
                print(f"   [STATUS] {safe_msg}")
            except:
                pass
        if self.status_callback:
            try:
                self.status_callback(message)
            except:
                pass
    
    def _call_openai_compatible(self, url, api_key, model, messages):
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
    
    def _invoke_local(self, messages):
        """Call local Ollama model (blocking)."""
        if not self.local_brain:
            return "Ollama model is offline/terminated."
        response = self.local_brain.invoke(messages)
        return response.content
    
    def _call_ai_with_timeout(self, messages, model_preference="auto"):
        """
        Local First, Cloud Rescue Logic:
        If model_preference is set to a specific provider, try it first.
        Otherwise:
        1. Try Ollama first with 40s timeout
        2. If timeout/error, switch to Groq Cloud
        3. If Groq fails, fallback to Gemini
        """
        pref = model_preference.lower() if model_preference else "auto"
        pref_provider = pref
        pref_model = None
        if ":" in pref and not pref.startswith("accounts/"):
            parts = pref.split(":", 1)
            pref_provider = parts[0]
            pref_model = parts[1]

        def get_text_messages(msgs):
            # pyrefly: ignore [missing-import]
            from langchain_core.messages import HumanMessage
            text_msgs = []
            for m in msgs:
                if m.__class__.__name__ == "HumanMessage" and isinstance(m.content, list):
                    txt = next((item["text"] for item in m.content if item.get("type") == "text"), "")
                    text_msgs.append(HumanMessage(content=txt))
                else:
                    text_msgs.append(m)
            return text_msgs

        def try_groq():
            if self.groq_brain:
                self._update_status("🚀 Cloud Turbo (Groq Llama-70B)...")
                response = self.groq_brain.invoke(get_text_messages(messages))
                return response.content, "Groq-Llama-70B-Cloud", False
            raise ValueError("Groq not configured")

        def try_fireworks(model_override=None):
            if FIREWORKS_AVAILABLE:
                self._update_status("🎆 Cloud (Fireworks)...")
                model = model_override if model_override else os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p1-70b-instruct")
                content = self._call_openai_compatible(
                    "https://api.fireworks.ai/inference/v1/chat/completions",
                    os.getenv("FIREWORKS_API_KEY"),
                    model,
                    get_text_messages(messages)
                )
                return content, f"Fireworks-{model.split('/')[-1]}-Cloud", False
            raise ValueError("Fireworks not configured")

        def try_openrouter(model_override=None):
            if OPENROUTER_AVAILABLE:
                self._update_status("🌐 Cloud (OpenRouter)...")
                model = model_override if model_override else os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
                content = self._call_openai_compatible(
                    "https://openrouter.ai/api/v1/chat/completions",
                    os.getenv("OPENROUTER_API_KEY"),
                    model,
                    messages
                )
                return content, f"OpenRouter-{model.split('/')[-1]}-Cloud", False
            raise ValueError("OpenRouter not configured")

        def try_deepseek():
            if DEEPSEEK_AVAILABLE:
                self._update_status("🐳 Cloud (DeepSeek)...")
                model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
                content = self._call_openai_compatible(
                    "https://api.deepseek.com/chat/completions",
                    os.getenv("DEEPSEEK_API_KEY"),
                    model,
                    get_text_messages(messages)
                )
                return content, f"DeepSeek-{model}-Cloud", False
            raise ValueError("DeepSeek not configured")

        def try_gemini():
            if self.gemini_brain:
                self._update_status("🔄 Cloud Fallback (Gemini)...")
                response = self.gemini_brain.invoke(messages)
                content = response.content
                if isinstance(content, list):
                    content = content[0].get('text', str(content[0])) if content else ""
                return str(content), "Gemini-Flash", False
            raise ValueError("Gemini not configured")

        def try_ollama():
            if self.local_brain:
                self._update_status(f"🧠 Thinking via Ollama ({os.getenv('OLLAMA_MODEL', 'deepseek-v4-flash:cloud')})...")
                res = self._invoke_local(get_text_messages(messages))
                return res, f"Ollama-{os.getenv('OLLAMA_MODEL', 'deepseek-v4-flash:cloud')}", False
            raise ValueError("Ollama not configured")

        if pref_provider in ["groq", "fireworks", "openrouter", "deepseek", "gemini", "ollama"]:
            try:
                if pref_provider == "groq":
                    return try_groq()
                elif pref_provider == "fireworks":
                    return try_fireworks(pref_model)
                elif pref_provider == "openrouter":
                    return try_openrouter(pref_model)
                elif pref_provider == "deepseek":
                    return try_deepseek()
                elif pref_provider == "gemini":
                    return try_gemini()
                elif pref_provider == "ollama":
                    return try_ollama()
            except Exception as e:
                print(f"[PREFERENCE ERROR] Preferred provider {pref_provider} failed: {e}. Falling back to default chain.")
                self._update_status(f"⚠️ Preferred model failed. Falling back...")

        # === PHASE 1: TRY LOCAL (OLLAMA) ===
        if self.local_brain:
            self._update_status(f"🧠 Thinking via Ollama ({os.getenv('OLLAMA_MODEL', 'deepseek-v4-flash:cloud')})...")
            
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._invoke_local, get_text_messages(messages))
                    
                    try:
                        # Wait with timeout
                        result = future.result(timeout=LOCAL_TIMEOUT_SECONDS)
                        return result, f"Ollama-{os.getenv('OLLAMA_MODEL', 'deepseek-v4-flash:cloud')}", False
                        
                    except FuturesTimeoutError:
                        # KILL SWITCH ACTIVATED
                        print(f"   [!] Local Timeout (>{LOCAL_TIMEOUT_SECONDS}s). Switching to Cloud.")
                        self._update_status(f"⏱️ Local too slow (>{LOCAL_TIMEOUT_SECONDS}s). Switching to Cloud Turbo...")
                        # Future will be cancelled/abandoned when executor exits
                        
            except Exception as e:
                print(f"   [!] Local error: {e}")
                self._update_status("⚠️ Local error. Switching to Cloud...")
        else:
            self._update_status("☁️ No local model. Using Cloud...")
        
        # === PHASE 2: CLOUD RESCUE (GROQ) ===
        if self.groq_brain:
            self._update_status("🚀 Cloud Turbo (Groq Llama-70B)...")
            try:
                response = self.groq_brain.invoke(get_text_messages(messages))
                return response.content, "Groq-Llama-70B-Cloud", True
            except Exception as e:
                print(f"   [!] Groq error: {e}")
                self._update_status("⚠️ Groq error. Trying Fireworks...")

        # === PHASE 2.1: CLOUD RESCUE (FIREWORKS) ===
        if FIREWORKS_AVAILABLE:
            self._update_status("🎆 Cloud (Fireworks)...")
            try:
                model = os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p1-8b-instruct")
                content = self._call_openai_compatible(
                    "https://api.fireworks.ai/inference/v1/chat/completions",
                    os.getenv("FIREWORKS_API_KEY"),
                    model,
                    get_text_messages(messages)
                )
                return content, f"Fireworks-{model.split('/')[-1]}-Cloud", True
            except Exception as e:
                print(f"   [!] Fireworks error: {e}")
                self._update_status("⚠️ Fireworks error. Trying OpenRouter...")

        # === PHASE 2.2: CLOUD RESCUE (OPENROUTER) ===
        if OPENROUTER_AVAILABLE:
            self._update_status("🌐 Cloud (OpenRouter)...")
            try:
                model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
                content = self._call_openai_compatible(
                    "https://openrouter.ai/api/v1/chat/completions",
                    os.getenv("OPENROUTER_API_KEY"),
                    model,
                    messages
                )
                return content, f"OpenRouter-{model.split('/')[-1]}-Cloud", True
            except Exception as e:
                print(f"   [!] OpenRouter error: {e}")
                self._update_status("⚠️ OpenRouter error. Trying DeepSeek...")

        # === PHASE 2.3: CLOUD RESCUE (DEEPSEEK) ===
        if DEEPSEEK_AVAILABLE:
            self._update_status("🐳 Cloud (DeepSeek)...")
            try:
                model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
                content = self._call_openai_compatible(
                    "https://api.deepseek.com/chat/completions",
                    os.getenv("DEEPSEEK_API_KEY"),
                    model,
                    get_text_messages(messages)
                )
                return content, f"DeepSeek-{model}-Cloud", True
            except Exception as e:
                print(f"   [!] DeepSeek error: {e}")
                self._update_status("⚠️ DeepSeek error. Trying Gemini...")
        
        # === PHASE 3: LAST RESORT (GEMINI) ===
        if self.gemini_brain:
            self._update_status("🔄 Fallback to Gemini...")
            try:
                response = self.gemini_brain.invoke(messages)
                content = response.content
                if isinstance(content, list):
                    content = content[0].get('text', str(content[0])) if content else ""
                return str(content), "Gemini-Flash", True
            except Exception as e:
                return f"Semua server sibuk. Error: {e}", "ALL_FAIL", True
        
        return "Tidak ada AI yang aktif. Cek Ollama/API keys.", "NO_AI", True

    def process(self, user_input, status_callback=None, model_preference="auto", image_files=None):
        """Main processor - returns (response, thinking_steps)"""
        start_time = time.time()
        thinking = []
        
        # Set status callback if provided
        if status_callback:
            self.status_callback = status_callback
        
        route = self.router.decide_route(user_input)
        thinking.append({"step": "[ROUTER]", "detail": f"Route: **{route}**"})
        print(f"   > Route: {route}")
        
        context = self.librarian.get_context()
        if context:
            thinking.append({"step": "[MEMORY]", "detail": f"Context loaded ({len(self.librarian.raw_history)} msgs)"})
        
        response = ""
        model_name = "System"
        was_failover = False
        
        if route == "ACTION":
            thinking.append({"step": "[ACTION]", "detail": "Executing physical command"})
            try:
                from modules.core.interpreter import execute_system_action
                response = execute_system_action(user_input)
                model_name = "ATOM-Hand"
            except ImportError:
                response = "Module modules/core/interpreter.py tidak ditemukan."
                model_name = "Error"
            except Exception as e:
                response = f"Gagal eksekusi: {e}"
                model_name = "Error"
        
        elif route == "CREW":
            thinking.append({"step": "[CREW]", "detail": "Deploying research squad"})
            try:
                response = run_research_crew(user_input)
                model_name = "CrewAI-Squad"
            except Exception as e:
                response = f"CrewAI error: {e}"
                model_name = "Error"
        
        else:  # AI route with timeout failover
            thinking.append({"step": "[AI]", "detail": "Local First, Cloud Rescue mode"})
            
            system_prompt = SystemMessage(content=f"""
            IDENTITY: Kamu adalah ATOM (Autonomous Task Orchestration Machine).
            STYLE: Cerdas, efisien, sedikit witty seperti Jarvis.
            LANGUAGE: Bahasa Indonesia.
            
            KONTEKS PERCAKAPAN:
            {context}
            """)
            
            if image_files:
                content_list = [{"type": "text", "text": user_input}]
                for img in image_files:
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": img["content"]}
                    })
                messages = [system_prompt, HumanMessage(content=content_list)]
            else:
                messages = [system_prompt, HumanMessage(content=user_input)]
                
            response, model_name, was_failover = self._call_ai_with_timeout(messages, model_preference)
            
            # Add failover info to thinking
            if was_failover:
                thinking.append({"step": "[FAILOVER]", "detail": f"Switched to cloud: {model_name}"})
 
        self.librarian.add_interaction(user_input, response)
        
        # Log with failover status
        status = "FAILOVER" if was_failover else "SUCCESS"
        log_input = user_input
        if isinstance(log_input, list):
            log_input = next((item["text"] for item in log_input if item.get("type") == "text"), "[Multimodal Input]")
        duration = self.sentinel.log(log_input, model_name, start_time, status)
        
        thinking.append({"step": "[LOG]", "detail": f"Time: {duration}s | Model: {model_name}"})
        print(f"   > Done in {duration}s via {model_name}")
        
        return response, thinking


# --- HELPER FUNCTIONS FOR MULTIMODAL INPUT ---

def read_file_content(uploaded_file) -> str:
    """
    Read content from an uploaded file.
    Supports: .txt, .md, .py, .json, .csv, .pdf
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        String content of the file
    """
    try:
        filename = uploaded_file.name.lower()
        
        # Text-based files
        if filename.endswith(('.txt', '.md', '.py', '.json', '.csv', '.html', '.css', '.js')):
            return uploaded_file.read().decode('utf-8')
        
        # PDF files
        elif filename.endswith('.pdf'):
            try:
                # pyrefly: ignore [missing-import]
                import PyPDF2
                import io
                
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            except ImportError:
                return "[ERROR] PyPDF2 not installed. Run: pip install PyPDF2"
            except Exception as e:
                return f"[ERROR] Failed to read PDF: {e}"
        
        else:
            return f"[ERROR] Unsupported file type: {filename}"
            
    except Exception as e:
        return f"[ERROR] Failed to read file: {e}"


def scrape_url(url: str) -> str:
    """
    Scrape text content from a URL.
    
    Args:
        url: Web URL to scrape
        
    Returns:
        String content of the webpage (text only)
    """
    try:
        import requests
        # pyrefly: ignore [missing-import]
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Limit length
        if len(clean_text) > 10000:
            clean_text = clean_text[:10000] + "\n\n[Content truncated...]"
        
        return clean_text
        
    except ImportError:
        return "[ERROR] BeautifulSoup not installed. Run: pip install beautifulsoup4"
    except requests.RequestException as e:
        return f"[ERROR] Failed to fetch URL: {e}"
    except Exception as e:
        return f"[ERROR] Failed to scrape URL: {e}"


# Backward compatibility alias
ATOMCorntext = ATOMCortex


# --- TEST ---
if __name__ == "__main__":
    print("\n=== ATOM CORTEX v4.0 TEST ===\n")
    print(f"Local: {'OK' if OLLAMA_AVAILABLE else 'OFF'} | Groq: {'OK' if GROQ_AVAILABLE else 'OFF'} | Gemini: {'OK' if GEMINI_AVAILABLE else 'OFF'}")
    print(f"Timeout: {LOCAL_TIMEOUT_SECONDS}s\n")
    
    atom = ATOMCortex()
    
    while True:
        q = input("\nBoss: ")
        if q.lower() == "exit": 
            break
        
        res, steps = atom.process(q)
        print(f"\nATOM: {res}")

