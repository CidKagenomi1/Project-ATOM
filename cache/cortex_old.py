import os
import time
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Tuple, Optional

load_dotenv()

# Import ATOM Interpreter for system actions (optional)
INTERPRETER_AVAILABLE = False
try:
    from atom_interpreter import execute_system_action
    INTERPRETER_AVAILABLE = True
except ImportError:
    def execute_system_action(command):
        return f"[INTERPRETER OFFLINE] Open Interpreter tidak tersedia."

# Check Groq availability
GROQ_AVAILABLE = bool(os.getenv("GROQ_API_KEY"))

# --- 1. THE SENTINEL (Sistem Pengawas/Logger) ---
class Sentinel:
    def __init__(self, log_file="atom_telemetry.csv"):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            df = pd.DataFrame(columns=["timestamp", "user_input", "model_used", "response_time", "status"])
            df.to_csv(self.log_file, index=False)

    def log(self, user_input, model_used, start_time):
        duration = round(time.time() - start_time, 2)
        new_data = pd.DataFrame([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_input[:50] + "..." if len(user_input) > 50 else user_input,
            "model_used": model_used,
            "response_time": duration,
            "status": "SUCCESS"
        }])
        new_data.to_csv(self.log_file, mode='a', header=False, index=False)
        return duration

# --- 2. THE LIBRARIAN (Manajemen Konteks) ---
class Librarian:
    def __init__(self):
        self.raw_history = []
    
    def add_interaction(self, user, ai):
        self.raw_history.append(f"User: {user}")
        self.raw_history.append(f"ATOM: {ai}")
        if len(self.raw_history) > 8:
            self.raw_history = self.raw_history[-6:]
            
    def get_context(self):
        return "\n".join(self.raw_history)
    
    def clear(self):
        self.raw_history = []

# --- 3. THE DISPATCHER (Router - keyword based for speed) ---
class NeuralRouter:
    def decide_route(self, user_input) -> Tuple[str, str]:
        """Fast keyword-based routing."""
        lower_input = user_input.lower()
        
        # ACTION keywords
        action_keywords = ["buka", "open", "cek", "check", "jalankan", "run", 
                         "folder", "file", "baterai", "battery", "brightness",
                         "aplikasi", "app", "browser", "direktori", "directory"]
        
        if any(kw in lower_input for kw in action_keywords):
            return "ACTION", "System command detected"
        
        return "CLOUD", "General query"

# --- 4. THE ORCHESTRATOR (Sang Konduktor) ---
class ATOMCortex:
    def __init__(self):
        self.sentinel = Sentinel()
        self.librarian = Librarian()
        self.router = NeuralRouter()
        
        # Primary: Gemini
        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-flash-latest", 
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        # Fallback: Groq (if available)
        self.groq = None
        if GROQ_AVAILABLE:
            self.groq = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.7
            )

    def _call_llm(self, messages, context=""):
        """Try Gemini first, fallback to Groq if rate limited."""
        system_prompt = SystemMessage(content=f"""
        Kamu adalah ATOM (Autonomous Task Orchestration Machine). 
        Asisten AI yang cerdas dan to-the-point.
        Jawab dalam Bahasa Indonesia yang natural.
        
        Konteks: {context}
        """)
        full_messages = [system_prompt, HumanMessage(content=messages)]
        
        # Try Gemini first
        try:
            response = self.gemini.invoke(full_messages)
            content = response.content
            if isinstance(content, list):
                content = content[0].get('text', str(content[0])) if content else ""
            return str(content), "Gemini-Flash"
        except Exception as gemini_error:
            error_str = str(gemini_error).lower()
            
            # If rate limited, try Groq
            if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
                if self.groq:
                    try:
                        response = self.groq.invoke(full_messages)
                        return response.content, "Groq-Llama"
                    except Exception as groq_error:
                        return f"[ERROR] Groq juga gagal: {groq_error}", "ERROR"
                else:
                    return "[ERROR] Gemini quota habis dan Groq API key belum diset. Tambahkan GROQ_API_KEY di .env", "ERROR"
            else:
                # Other Gemini error
                if self.groq:
                    try:
                        response = self.groq.invoke(full_messages)
                        return response.content, "Groq-Llama"
                    except:
                        pass
                return f"[ERROR] {gemini_error}", "ERROR"

    def process(self, user_input) -> Tuple[str, list]:
        """Process user input and return (response, thinking_steps)."""
        start_time = time.time()
        thinking = []
        
        # A. ROUTING
        route, reason = self.router.decide_route(user_input)
        thinking.append({
            "step": "[ROUTER]",
            "detail": f"Route: **{route}** | {reason}"
        })
        
        # B. CONTEXT
        context = self.librarian.get_context()
        if context:
            thinking.append({
                "step": "[CONTEXT]",
                "detail": f"Loaded {len(self.librarian.raw_history)} messages"
            })
        
        # C. EXECUTE
        try:
            if route == "ACTION":
                thinking.append({
                    "step": "[ACTION]",
                    "detail": "Executing system command"
                })
                
                if INTERPRETER_AVAILABLE:
                    response = execute_system_action(user_input)
                    thinking.append({
                        "step": "[OK]",
                        "detail": "Command executed"
                    })
                else:
                    response = "Interpreter tidak tersedia."
                model_name = "ATOM-Interpreter"
                
            else:  # CLOUD
                thinking.append({
                    "step": "[CLOUD]",
                    "detail": "Calling AI (Gemini -> Groq fallback)"
                })
                
                response, model_name = self._call_llm(user_input, context)
                
        except Exception as e:
            response = f"Error: {e}"
            model_name = "ERROR"
            thinking.append({
                "step": "[ERROR]",
                "detail": str(e)
            })

        # D. SAVE
        self.librarian.add_interaction(user_input, response)
        
        # E. LOG
        duration = self.sentinel.log(user_input, model_name, start_time)
        thinking.append({
            "step": "[LOG]",
            "detail": f"Time: {duration}s | Model: {model_name}"
        })
        
        return response, thinking

# --- TEST ---
if __name__ == "__main__":
    print(f"Groq Available: {GROQ_AVAILABLE}")
    print("Testing ATOMCortex...")
    atom = ATOMCortex()
    res, steps = atom.process("halo, siapa kamu?")
    print(f"\nResponse: {res[:100]}...")
    print(f"Steps: {len(steps)}")
