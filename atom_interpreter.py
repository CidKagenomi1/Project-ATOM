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

    # 2. EKSEKUSI NYATA (THE REAL HANDS - PyAutoGUI Version)
    try:
        import pyautogui
        import time
        
        # Safety Fail-Safe: memindahkan mouse ke pojok layar akan menghentikan pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3

        # --- KASUS 1: BROWSER / YOUTUBE / GOOGLE ---
        if action_type == "BROWSER":
            # Buka Windows Search
            pyautogui.press('win')
            time.sleep(0.5)
            # Ketik nama browser (default chrome)
            pyautogui.write('chrome')
            time.sleep(0.5)
            pyautogui.press('enter')
            
            # Tunggu browser terbuka
            time.sleep(2.0)
            
            # Fokus ke address bar menggunakan Ctrl+L
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)
            
            # Ketik URL target dan enter
            pyautogui.write(target)
            pyautogui.press('enter')
            
            return f"[SUKSES] Membuka Browser & Navigasi ke:\n{target}\n\n(Menggunakan PyAutoGUI)"
            
        # --- KASUS 2: APLIKASI WINDOWS ---
        elif action_type == "APP":
            app_map = {
                "kalkulator": "calculator",
                "notepad": "notepad",
                "cmd": "cmd",
                "explorer": "explorer",
                "vscode": "visual studio code",
                "spotify": "spotify"
            }
            
            app_name = app_map.get(target.lower(), target)
            
            # Buka Windows Search
            pyautogui.press('win')
            time.sleep(0.5)
            # Ketik nama aplikasi
            pyautogui.write(app_name)
            time.sleep(0.5)
            pyautogui.press('enter')
            
            return f"[SUKSES] Menjalankan Aplikasi '{app_name}' via Windows Search (Menggunakan PyAutoGUI)"
            
        # --- KASUS 3: SYSTEM UTILS ---
        elif action_type == "SYSTEM":
            if "shutdown" in target.lower():
                return "[SAFETY] Tindakan shutdown dibatalkan demi keamanan sistem Anda."
            elif "lock" in target.lower() or "kunci" in target.lower():
                # Kunci PC (Win + L)
                pyautogui.hotkey('win', 'l')
                return "[SUKSES] Mengunci komputer (Win + L) menggunakan PyAutoGUI"
            elif "battery" in target.lower() or "baterai" in target.lower():
                 import psutil
                 battery = psutil.sensors_battery()
                 percent = battery.percent if battery else "N/A"
                 plugged = battery.power_plugged if battery else "N/A"
                 return f"[INFO SISTEM] Baterai: {percent}% | Charging: {plugged}"
            
        return f"[INFO] Tindakan '{explanation}' telah diproses."
        
    except Exception as e:
        return f"[GAGAL EKSEKUSI] Terjadi kesalahan pada PyAutoGUI: {e}"

# Test Manual
if __name__ == "__main__":
    # Aktifkan import test jika dijalankan langsung
    import pyautogui
    print("[ATOM HANDS] PyAutoGUI siap digunakan.")

