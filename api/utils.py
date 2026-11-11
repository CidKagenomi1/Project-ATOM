import os
import sys
import json
from typing import Any

def safe_print(*args, **kwargs):
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

def safe_save_json(filepath: str, data: Any) -> bool:
    """Safely save JSON file with fallback to /tmp if filesystem is read-only (e.g. Vercel)."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        safe_print(f"[WARN] Local save failed for {filepath}: {e}. Trying /tmp fallback...")
        try:
            tmp_path = os.path.join("/tmp", os.path.basename(filepath))
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as tmp_e:
            safe_print(f"[WARN] /tmp fallback save also failed: {tmp_e}")
            return False

def safe_load_json(filepath: str, default: Any = None) -> Any:
    """Safely load JSON file with /tmp fallback."""
    candidates = [filepath, os.path.join("/tmp", os.path.basename(filepath))]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return default if default is not None else {}

# Shared Cortex Instance & Fallback
cortex_instance = None

def get_cortex():
    global cortex_instance
    if cortex_instance is None:
        try:
            from modules.core.cortex import ATOMCortex
            cortex_instance = ATOMCortex()
        except Exception as e:
            safe_print(f"[CORTEX INIT ERROR] {e}. Using resilient FallbackCortex.")
            class FallbackCortex:
                class Librarian:
                    def __init__(self):
                        self.raw_history = []
                    def clear(self):
                        self.raw_history = []
                def __init__(self):
                    self.librarian = self.Librarian()
                def process(self, user_input, model_preference="auto", image_files=None, status_callback=None):
                    google_key = os.getenv("GOOGLE_API_KEY")
                    if google_key:
                        try:
                            from langchain_google_genai import ChatGoogleGenerativeAI
                            llm = ChatGoogleGenerativeAI(
                                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                                google_api_key=google_key,
                                temperature=0.7
                            )
                            res = llm.invoke(user_input).content
                            if isinstance(res, list):
                                res = res[0].get('text', str(res[0])) if res else ""
                            return str(res), [
                                {"step": "[ROUTER]", "detail": "Fallback Gemini"},
                                {"step": "[LOG]", "detail": "Model: Gemini-Flash"}
                            ]
                        except Exception as ge:
                            return f"Cortex error: {ge}", [{"step": "[ERROR]", "detail": str(ge)}]
                    return "Sistem AI sedang offline. Silakan tambahkan API key di environment.", [{"step": "[ERROR]", "detail": "No API key"}]
            cortex_instance = FallbackCortex()
    return cortex_instance
