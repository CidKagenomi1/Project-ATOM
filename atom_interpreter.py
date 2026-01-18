"""
ATOM HANDS (DIRECT EXECUTOR)
Sistem eksekusi nyata menggunakan Python Native Libraries.
Fokus: Web Browsing, App Launching, & Media Playing.
"""

import os
import sys
import subprocess
import webbrowser
import json
import urllib.parse
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def execute_system_action(user_command):
    """
    Penerjemah Perintah Manusia -> Aksi Python Asli
    """
    print(f"   [ATOM HANDS] Menerima perintah '{user_command}'...")
    
    # 1. ANALISIS NIAT (INTENT) PAKAI GROQ
    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1
        )
        
        prompt = f"""
        Kamu adalah Operator Sistem Windows. Tugasmu menerjemahkan perintah user menjadi JSON.
        
        User Command: "{user_command}"
        
        PILIH SATU 'ACTION_TYPE' YANG PALING COCOK:
        1. "BROWSER" -> Jika user minta buka website, cari info, putar video, buka youtube/google.
        2. "APP" -> Jika user minta buka aplikasi terinstall (Notepad, Calculator, VS Code, Spotify).
        3. "SYSTEM" -> Jika user minta cek baterai, matikan laptop, restart.
        
        FORMAT JSON (Wajib):
        {{
            "action_type": "BROWSER" | "APP" | "SYSTEM",
            "target": "URL_LENGKAP" (jika BROWSER) atau "NAMA_EXE" (jika APP),
            "explanation": "Penjelasan singkat bahasa indonesia"
        }}
        
        CONTOH PINTAR:
        - "Cari resep nasi goreng" -> {{"action_type": "BROWSER", "target": "https://www.google.com/search?q=resep+nasi+goreng"}}
        - "Putarkan video Malaka Project" -> {{"action_type": "BROWSER", "target": "https://www.youtube.com/results?search_query=malaka+project+podcast"}}
        - "Buka Youtube" -> {{"action_type": "BROWSER", "target": "https://www.youtube.com"}}
        - "Buka Notepad" -> {{"action_type": "APP", "target": "notepad.exe"}}
        - "Matikan Laptop" -> {{"action_type": "SYSTEM", "target": "shutdown"}}
        
        HANYA OUTPUT JSON. JANGAN PAKAI MARKDOWN.
        """
        
        response = llm.invoke(prompt).content
        clean_json = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        action_type = data.get("action_type")
        target = data.get("target")
        explanation = data.get("explanation")
        
        print(f"   [INTENT] {action_type} -> {target}")
        
    except Exception as e:
        return f"[ERROR] Otak Groq Gagal: {e}"

    # 2. EKSEKUSI NYATA (THE REAL HANDS)
    try:
        # --- KASUS 1: BROWSER / YOUTUBE / GOOGLE ---
        if action_type == "BROWSER":
            webbrowser.open(target)
            return f"[SUKSES] Membuka Browser:\n{target}\n\n(Cek tab browser Anda, Sir)"
            
        # --- KASUS 2: APLIKASI WINDOWS ---
        elif action_type == "APP":
            app_map = {
                "kalkulator": "calc.exe", "calculator": "calc.exe",
                "notepad": "notepad.exe",
                "cmd": "cmd.exe",
                "explorer": "explorer.exe",
                "vscode": "code",
                "spotify": "spotify"
            }
            
            cmd_to_run = app_map.get(target.lower(), target)
            subprocess.Popen(cmd_to_run, shell=True)
            return f"[SUKSES] Meluncurkan Aplikasi: `{cmd_to_run}`"
            
        # --- KASUS 3: SYSTEM UTILS ---
        elif action_type == "SYSTEM":
            if "shutdown" in target.lower():
                return "[SAFETY] Saya tidak akan mematikan laptop otomatis. Perintahnya: `shutdown /s /t 60`"
            elif "battery" in target.lower() or "baterai" in target.lower():
                 import psutil
                 battery = psutil.sensors_battery()
                 return f"[INFO SISTEM] Baterai: {battery.percent}% | Charging: {battery.power_plugged}"
            
        return f"[INFO] Tindakan '{explanation}' telah diproses."
        
    except Exception as e:
        return f"[GAGAL EKSEKUSI] Tangan tergelincir: {e}"

# Test Manual
if __name__ == "__main__":
    print(execute_system_action("Putarkan video podcast malaka project"))
