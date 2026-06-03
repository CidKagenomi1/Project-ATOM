# -*- coding: utf-8 -*-
"""
HIM Unified Hybrid - High Intelligent Model dengan Windows Troubleshooting
Mode Hybrid: Llama 3.2 (lokal via Ollama) + Gemini (cloud) untuk hemat token.
"""

import os
import sys
import subprocess
import json
import re
import requests
from pathlib import Path
from typing import Dict, Optional, Literal

from dotenv import load_dotenv  # type: ignore

load_dotenv()

# Fix Windows console encoding for emoji support
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Optional: Gemini for complex tasks
try:
    import google.generativeai as genai  # type: ignore
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class HIMHybrid:
    """HIM - High Intelligent Model dengan mode Hybrid (Llama lokal + Gemini cloud)."""
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 ollama_model: str = "llama3.2:latest",
                 gemini_api_key: Optional[str] = None,
                 default_mode: Literal["local", "cloud", "auto"] = "auto"):
        """
        Initialize HIM Hybrid.
        
        Args:
            ollama_url: URL ke Ollama server (default: http://localhost:11434)
            ollama_model: Model Ollama yang digunakan (default: llama3.2:latest)
            gemini_api_key: API key untuk Gemini (optional, untuk mode cloud)
            default_mode: 
                - "local" = selalu pakai Qwen lokal
                - "cloud" = selalu pakai Gemini
                - "auto" = lokal untuk simple, cloud untuk kompleks
        """
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.default_mode = default_mode
        self.conversation_history = []
        self.working_directory = os.getcwd()
        
        # Check Ollama availability
        self.ollama_available = self._check_ollama()
        
        # Setup Gemini if available
        self.gemini_available = False
        self.gemini_error = None
        if GEMINI_AVAILABLE:
            self.gemini_api_key = gemini_api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if self.gemini_api_key:
                try:
                    genai.configure(api_key=self.gemini_api_key)
                    # Coba beberapa model secara berurutan (fallback)
                    models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
                    for model_name in models_to_try:
                        try:
                            self.gemini_model = genai.GenerativeModel(model_name)
                            self.gemini_model_name = model_name
                            self.gemini_available = True
                            break
                        except:
                            continue
                except Exception as e:
                    self.gemini_error = str(e)
                    print(f"⚠️ Gemini init error: {e}")
        
        # Current active mode
        if not self.ollama_available and not self.gemini_available:
            raise ValueError("Tidak ada AI tersedia! Pastikan Ollama berjalan atau API Key Gemini valid.")
        
        self.system_instruction = self._build_system_instruction()
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return self.ollama_model in model_names or any(self.ollama_model.split(":")[0] in m for m in model_names)
            return False
        except:
            return False
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for HIM."""
        return """
IDENTITY:
Kamu adalah HIM (High Intelligent Model), terinspirasi dari J.A.R.V.I.S.
AI butler yang anggun, witty, dan sedikit sarkastik tapi tetap hormat.

ATURAN:
1. Panggil user sebagai "Sir"
2. Bahasa Indonesia formal tapi natural
3. Jawaban singkat dan to-the-point
4. Boleh sarkastik tapi tetap membantu
5. Jika diminta menjalankan perintah sistem, gunakan format:
   ```shell
   perintah disini
   ```

CONTOH:
- "Baik Sir, saya akan memproses itu."
- "Pilihan yang... menarik, Sir. Tapi baiklah."
- "Sir, dengan hormat, itu tidak mungkin secara teknis."

GOAL: Bantu user dengan efisien sambil jadi teman ngobrol yang cerdas.
"""
    
    def _is_complex_query(self, query: str) -> bool:
        """Determine if query needs cloud (Gemini) or can be handled locally."""
        complex_keywords = [
            'code', 'coding', 'program', 'script', 'debug', 'error',
            'analisis', 'analyze', 'explain', 'jelaskan panjang',
            'riset', 'research', 'tulis', 'write', 'buat', 'create',
            'panjang', 'detail', 'lengkap', 'comprehensive',
            'strategi', 'strategy', 'rencana', 'plan'
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in complex_keywords) or len(query) > 200
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Qwen via Ollama API."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            return f"Error Ollama: {response.status_code}"
        except Exception as e:
            return f"Error koneksi Ollama: {str(e)}"
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        if not self.gemini_available:
            return "Gemini tidak tersedia. Pastikan API key valid dan library google-generativeai terinstall."
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Deteksi berbagai jenis error
            if "API_KEY" in error_msg or "api key" in error_msg.lower():
                return f"Error Gemini: API Key tidak valid atau tidak ditemukan. Periksa GOOGLE_API_KEY di .env"
            elif "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                # Extract retry time if available
                retry_match = re.search(r'retry.*?(\d+)', error_msg.lower())
                retry_seconds = retry_match.group(1) if retry_match else "beberapa"
                return f"⚠️ Kuota Gemini API habis (free tier limit). Tunggu {retry_seconds} detik dan coba lagi, atau gunakan /mode local untuk pakai Qwen lokal."
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                return f"Error Gemini: Tidak bisa terhubung ke server. Periksa koneksi internet."
            elif "model" in error_msg.lower():
                return f"Error Gemini: Model tidak tersedia. Detail: {error_msg}"
            else:
                return f"Error Gemini: {error_msg}"
    
    def chat(self, user_input: str, force_mode: Optional[Literal["local", "cloud"]] = None) -> tuple[str, str]:
        """
        Chat dengan HIM menggunakan mode hybrid.
        
        Returns:
            tuple: (response, mode_used)
        """
        # Build prompt with history
        messages = [self.system_instruction]
        for msg in self.conversation_history[-5:]:
            messages.append(msg)
        messages.append(f"User: {user_input}")
        prompt = "\n".join(messages)
        
        # Determine which model to use
        if force_mode:
            mode = force_mode
        elif self.default_mode == "local":
            mode = "local" if self.ollama_available else "cloud"
        elif self.default_mode == "cloud":
            mode = "cloud" if self.gemini_available else "local"
        else:  # auto mode
            if self._is_complex_query(user_input) and self.gemini_available:
                mode = "cloud"
            else:
                mode = "local" if self.ollama_available else "cloud"
        
        # Call appropriate model
        if mode == "local":
            response = self._call_ollama(prompt)
            mode_label = "🔒 Llama (lokal)"
        else:
            response = self._call_gemini(prompt)
            mode_label = "☁️ Gemini (cloud)"
        
        # Update history
        self.conversation_history.append(f"User: {user_input}")
        self.conversation_history.append(f"HIM: {response}")
        
        return response, mode_label
    
    # ==================== SHELL/CODE EXECUTION ====================
    
    def execute_shell_command(self, command: str) -> Dict[str, any]:
        """Execute shell/PowerShell command."""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                cwd=self.working_directory, timeout=60
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def execute_python_code(self, code: str) -> Dict[str, any]:
        """Execute Python code."""
        try:
            exec_globals = {'__builtins__': __builtins__, 'os': os, 'sys': sys, 'json': json}
            exec_locals = {}
            
            from contextlib import redirect_stdout, redirect_stderr
            stdout_cap = io.StringIO()
            stderr_cap = io.StringIO()
            
            with redirect_stdout(stdout_cap), redirect_stderr(stderr_cap):
                exec(code, exec_globals, exec_locals)
            
            return {'success': True, 'output': stdout_cap.getvalue(), 'error': stderr_cap.getvalue()}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    # ==================== WINDOWS DIAGNOSTICS ====================
    
    def get_system_info(self) -> str:
        """Get system information."""
        ps_cmd = '''
        $os = Get-WmiObject Win32_OperatingSystem
        $cs = Get-WmiObject Win32_ComputerSystem
        Write-Host "Komputer: $($cs.Name)"
        Write-Host "OS: $($os.Caption) Build $($os.BuildNumber)"
        Write-Host "RAM: $([math]::Round($cs.TotalPhysicalMemory/1GB, 2)) GB"
        Write-Host "Uptime: $((Get-Date) - $os.ConvertToDateTime($os.LastBootUpTime))"
        '''
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, timeout=30)
        return result.stdout or result.stderr
    
    def get_processes(self) -> str:
        """Get top processes."""
        ps_cmd = '''Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, 
        @{N='CPU(s)';E={[math]::Round($_.CPU,2)}}, @{N='MB';E={[math]::Round($_.WorkingSet/1MB,2)}} | Format-Table -AutoSize'''
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, timeout=30)
        return result.stdout or result.stderr
    
    def get_disk_usage(self) -> str:
        """Get disk usage."""
        ps_cmd = '''Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
            Write-Host "$($_.DeviceID) Total: $([math]::Round($_.Size/1GB,2))GB, Free: $([math]::Round($_.FreeSpace/1GB,2))GB"
        }'''
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, timeout=30)
        return result.stdout or result.stderr
    
    def check_network(self) -> str:
        """Quick network check."""
        ps_cmd = '''
        Write-Host "Gateway: $(if(Test-Connection (Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1).NextHop -Count 1 -Quiet){'OK'}else{'FAIL'})"
        Write-Host "Internet: $(if(Test-Connection 8.8.8.8 -Count 1 -Quiet){'OK'}else{'FAIL'})"
        '''
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, timeout=30)
        return result.stdout or result.stderr
    
    def cleanup_temp(self) -> str:
        """Clean temp files."""
        ps_cmd = '''
        $count = 0
        Get-ChildItem $env:TEMP -Recurse -Force -ErrorAction SilentlyContinue | 
        Where-Object { !$_.PSIsContainer -and $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
        ForEach-Object { try { Remove-Item $_.FullName -Force -ErrorAction Stop; $count++ } catch {} }
        Write-Host "$count file dihapus."
        '''
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, timeout=120)
        return result.stdout or result.stderr
    
    # ==================== MAIN LOOP ====================
    
    def process_message(self, user_input: str) -> tuple[str, str]:
        """Process message with slash commands and AI."""
        cmd = user_input.lower().strip()
        
        # Slash commands (no AI needed)
        if cmd in ['/info', '/system']:
            return self.get_system_info(), "⚡ Local"
        if cmd in ['/proses', '/process']:
            return self.get_processes(), "⚡ Local"
        if cmd in ['/disk']:
            return self.get_disk_usage(), "⚡ Local"
        if cmd in ['/network', '/net']:
            return self.check_network(), "⚡ Local"
        if cmd == '/cleanup':
            confirm = input("⚠️ Hapus temp files? (y/n): ").strip().lower()
            if confirm == 'y':
                return self.cleanup_temp(), "⚡ Local"
            return "Dibatalkan.", "⚡ Local"
        
        # Force mode commands
        if cmd.startswith('/local '):
            query = user_input[7:]
            return self.chat(query, force_mode="local")
        if cmd.startswith('/cloud '):
            query = user_input[7:]
            return self.chat(query, force_mode="cloud")
        
        # Mode switch
        if cmd == '/mode local':
            self.default_mode = "local"
            return "Mode diubah ke LOCAL (Llama). Semua chat akan diproses lokal.", "⚡ Local"
        if cmd == '/mode cloud':
            self.default_mode = "cloud"
            return "Mode diubah ke CLOUD (Gemini). Semua chat akan diproses cloud.", "⚡ Local"
        if cmd == '/mode auto':
            self.default_mode = "auto"
            return "Mode diubah ke AUTO. Simple=lokal, Complex=cloud.", "⚡ Local"
        if cmd == '/mode':
            return f"Mode saat ini: {self.default_mode.upper()}\nOllama: {'✓' if self.ollama_available else '✗'}\nGemini: {'✓' if self.gemini_available else '✗'}", "⚡ Local"
        
        # Regular chat with hybrid AI
        response, mode = self.chat(user_input)
        
        # Execute any code blocks in response
        code_blocks = re.findall(r'```(python|shell|powershell)\n(.*?)```', response, re.DOTALL)
        exec_results = []
        for btype, content in code_blocks:
            if btype == 'python':
                r = self.execute_python_code(content)
                exec_results.append(f"[Python]\n{r['output']}{r['error']}")
            elif btype in ['shell', 'powershell']:
                r = self.execute_shell_command(content.strip())
                exec_results.append(f"[Shell]\n{r['output']}{r['error']}")
        
        if exec_results:
            response += "\n\n" + "\n".join(exec_results)
        
        return response, mode
    
    def run(self):
        """Run interactive HIM session."""
        print("=" * 60)
        print("🤖 HIM - High Intelligent Model (Hybrid)")
        mode_status = []
        if self.ollama_available:
            mode_status.append(f"🔒 Llama ({self.ollama_model})")
        if self.gemini_available:
            mode_status.append("☁️ Gemini")
        print(f"   Mode: {self.default_mode.upper()} | Available: {' + '.join(mode_status)}")
        print("=" * 60)
        print()
        print("💬 Commands:")
        print("  /info, /proses, /disk, /network - System diagnostics")
        print("  /local [msg]  - Force local Llama")
        print("  /cloud [msg]  - Force cloud Gemini")
        print("  /mode [local|cloud|auto] - Switch default mode")
        print()
        print("Ketik 'off' untuk keluar, 'clear' untuk reset history")
        print("=" * 60)
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['off', 'exit', 'quit']:
                    print("\n> HIM: Shutting down. Goodbye, Sir. 👋")
                    break
                
                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("✓ History cleared.\n")
                    continue
                
                if user_input.lower() == 'help':
                    print("""
Commands:
  /info     - System info
  /proses   - Running processes
  /disk     - Disk usage
  /network  - Network check
  /cleanup  - Clean temp files

  /local [msg] - Use Llama locally
  /cloud [msg] - Use Gemini cloud
  /mode        - Check current mode
  /mode [local|cloud|auto] - Set mode
""")
                    continue
                
                response, mode = self.process_message(user_input)
                print(f"\n[{mode}]")
                print(f"> HIM: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\n> HIM: Interrupted. Goodbye, Sir. 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")


def main():
    """Main entry point."""
    try:
        him = HIMHybrid(
            ollama_model="llama3.2:latest",
            default_mode="auto"  # Auto: simple=local, complex=cloud
        )
        him.run()
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
