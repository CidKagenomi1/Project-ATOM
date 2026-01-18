"""
ATOM CORNTEXT v3.0
Otak utama ATOM dengan arsitektur bersih.
Primary: Groq | Backup: Gemini | Special: CrewAI & Interpreter
"""

import os
import time
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# --- STATUS FLAGS ---
GROQ_AVAILABLE = bool(os.getenv("GROQ_API_KEY"))
GEMINI_AVAILABLE = bool(os.getenv("GOOGLE_API_KEY"))

# Import CrewAI (optional)
CREW_AVAILABLE = False
try:
    from crew_atom import run_research_crew
    CREW_AVAILABLE = True
except ImportError:
    def run_research_crew(topic):
        return "[CREW OFFLINE] CrewAI belum terinstall. Jalankan: pip install crewai"


# --- 1. THE SENTINEL (Sistem Pengawas/Logger) ---
class Sentinel:
    def __init__(self, log_file="atom_telemetry.csv"):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            df = pd.DataFrame(columns=["timestamp", "user_input", "model_used", "response_time", "status"])
            df.to_csv(self.log_file, index=False)

    def log(self, user_input, model_used, start_time):
        duration = round(time.time() - start_time, 2)
        try:
            new_data = pd.DataFrame([{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": user_input[:50] + "...",
                "model_used": model_used,
                "response_time": duration,
                "status": "SUCCESS"
            }])
            new_data.to_csv(self.log_file, mode='a', header=False, index=False)
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
        # Pangkas memori: simpan 3 pasang terakhir
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
        
        # ROUTE 1: ACTION (Perintah Fisik Laptop)
        action_kw = ["buka", "open", "jalankan", "run", "cek", "check", 
                     "folder", "file", "baterai", "battery", "youtube",
                     "browser", "notepad", "calculator", "spotify"]
        if any(kw in txt for kw in action_kw):
            return "ACTION"
        
        # ROUTE 2: CREW (Riset Mendalam)
        crew_kw = ["riset", "research", "analisis mendalam", "investigasi", "pelajari"]
        if CREW_AVAILABLE and any(kw in txt for kw in crew_kw):
            return "CREW"
        
        # ROUTE 3: CLOUD (Default - Chat Biasa)
        return "CLOUD"


# --- 4. THE CORNTEXT (Otak Utama) ---
class ATOMCorntext:
    def __init__(self):
        print("[ATOM] Initializing CORNTEXT v3.0...")
        
        # Load Sub-Sistem
        self.sentinel = Sentinel()
        self.librarian = Librarian()
        self.router = NeuralRouter()
        
        # OTAK UTAMA: GROQ (Super Cepat)
        self.groq_brain = None
        if GROQ_AVAILABLE:
            try:
                self.groq_brain = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    api_key=os.getenv("GROQ_API_KEY"),
                    temperature=0.7
                )
                print("[OK] PRIMARY: Groq Llama-70B")
            except Exception as e:
                print(f"[WARN] Groq failed: {e}")
        
        # OTAK CADANGAN: GEMINI
        self.gemini_brain = None
        if GEMINI_AVAILABLE:
            try:
                self.gemini_brain = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    temperature=0.7
                )
                print("[OK] BACKUP: Gemini Flash")
            except Exception as e:
                print(f"[WARN] Gemini failed: {e}")
        
        print("[ATOM] All systems ready.")

    def _call_ai(self, messages):
        """Logika Failover: Groq -> Gemini"""
        
        # 1. Coba GROQ dulu
        if self.groq_brain:
            try:
                response = self.groq_brain.invoke(messages)
                return response.content, "Groq-Llama-70B"
            except Exception as e:
                print(f"   [!] Groq error: {e}")
        
        # 2. Fallback ke GEMINI
        if self.gemini_brain:
            try:
                response = self.gemini_brain.invoke(messages)
                content = response.content
                if isinstance(content, list):
                    content = content[0].get('text', str(content[0])) if content else ""
                return str(content), "Gemini-Flash"
            except Exception as e:
                return f"Semua server sibuk. Error: {e}", "ALL_FAIL"
        
        return "Tidak ada AI yang aktif. Cek API keys.", "NO_AI"

    def process(self, user_input):
        """Main processor - returns (response, thinking_steps)"""
        start_time = time.time()
        thinking = []
        
        # A. DISPATCHER: Tentukan jalur
        route = self.router.decide_route(user_input)
        thinking.append({
            "step": "[ROUTER]",
            "detail": f"Route: **{route}**"
        })
        print(f"   > Route: {route}")
        
        # B. LIBRARIAN: Ambil konteks
        context = self.librarian.get_context()
        if context:
            thinking.append({
                "step": "[MEMORY]",
                "detail": f"Context loaded ({len(self.librarian.raw_history)} msgs)"
            })
        
        # C. EKSEKUSI BERDASARKAN ROUTE
        response = ""
        model_name = "System"
        
        if route == "ACTION":
            # === JALUR TANGAN (Interpreter) ===
            thinking.append({"step": "[ACTION]", "detail": "Executing physical command"})
            try:
                from atom_interpreter import execute_system_action
                response = execute_system_action(user_input)
                model_name = "ATOM-Hand"
            except ImportError:
                response = "Module atom_interpreter.py tidak ditemukan."
                model_name = "Error"
            except Exception as e:
                response = f"Gagal eksekusi: {e}"
                model_name = "Error"
        
        elif route == "CREW":
            # === JALUR CREW (Multi-Agent Research) ===
            thinking.append({"step": "[CREW]", "detail": "Deploying research squad"})
            try:
                response = run_research_crew(user_input)
                model_name = "CrewAI-Squad"
            except Exception as e:
                response = f"CrewAI error: {e}"
                model_name = "Error"
        
        else:
            # === JALUR CLOUD (Chat Biasa) ===
            thinking.append({"step": "[CLOUD]", "detail": "Calling AI brain"})
            
            system_prompt = SystemMessage(content=f"""
            IDENTITY: Kamu adalah ATOM (Autonomous Task Orchestration Machine).
            STYLE: Cerdas, efisien, sedikit witty seperti Jarvis.
            LANGUAGE: Bahasa Indonesia.
            
            KONTEKS PERCAKAPAN:
            {context}
            """)
            
            messages = [system_prompt, HumanMessage(content=user_input)]
            response, model_name = self._call_ai(messages)

        # D. LIBRARIAN: Simpan ingatan
        self.librarian.add_interaction(user_input, response)
        
        # E. SENTINEL: Catat telemetry
        duration = self.sentinel.log(user_input, model_name, start_time)
        thinking.append({
            "step": "[LOG]",
            "detail": f"Time: {duration}s | Model: {model_name}"
        })
        print(f"   > Done in {duration}s via {model_name}")
        
        return response, thinking


# --- TEST ---
if __name__ == "__main__":
    print("\n=== ATOM CORNTEXT TEST ===\n")
    atom = ATOMCorntext()
    
    while True:
        q = input("\nBoss: ")
        if q.lower() == "exit": 
            break
        
        res, steps = atom.process(q)
        print(f"\nATOM: {res}")
