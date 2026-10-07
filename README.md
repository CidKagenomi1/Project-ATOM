# A.T.O.M (Autonomous Task Orchestration Machine) v4.0

> *"I am not just a chatbot, Sir. I am a Neural Orchestrator."*

**A.T.O.M** adalah ekosistem AI **Multi-Agent & Multi-Provider** berbasis **Cortex Router** cerdas. Sistem ini hadir dalam arsitektur hybrid: **Web Application modern** (FastAPI backend + Vanilla HTML/CSS/JS frontend) dan **Desktop GUI** (Streamlit).

---

## ⚡ Fitur Utama & Keunggulan Spesial

1. **🔀 Multi-Provider Neural Router (Cortex)**:
   * **Auto-Routing**: Secara otomatis memilih model terbaik berdasarkan tipe query (coding, riset, kalkulasi, percakapan santai).
   * **Dukungan Beragam Provider**: 
     * **Groq** (*Llama 3.3 70B*) untuk respon ultra-cepat.
     * **Ollama & DeepSeek** (*DeepSeek V3 / V4 Cloud*).
     * **Gemini Flash 2.5** (Multimodal vision & text).
     * **OpenRouter Catalog Free & Premium** (*Gemma 4 31B, Nemotron 3 Nano Omni, Qwen3 Coder 480B, Hermes 3 405B*, dll).
   * **Self-Healing & Fallback**: Otomatis beralih ke penyedia cadangan jika kuota habis atau terjadi kegagalan jaringan.

2. **🖼️ Multimodal & Clipboard Instant Paste**:
   * Cukup tekan `Ctrl + V` untuk langsung menempelkan tangkapan layar (screenshot) ke input chat.
   * Pembersihan & sanitasi otomatis payload gambar agar aman diproses oleh model multimodal.

3. **📝 Smart Notes (Obsidian-Style Knowledge Base)**:
   * **Magic Formatter**: Merapikan teks mentah menjadi ringkasan markdown terstruktur.
   * **Auto-Tagging**: Memberikan tag & kategori cerdas secara otomatis.
   * **Chat with Notes**: Bertanya langsung kepada AI berdasarkan basis pengetahuan catatan yang tersimpan.

4. **📊 Real-Time Telemetry & Monitoring**:
   * Memantau latensi respon, penggunaan token, dan statistik distribusi model per sesi.
   * Indikator live status untuk provider AI (Ollama Local, Groq Cloud, CrewAI, Gemini Fallback).

5. **⚛️ Visual Estetika Reaktor Nuklir**:
   * Efek latar belakang kanvas interaktif **Vapor Chamber** yang mensimulasikan jejak peluruhan partikel radioaktif (*Alpha, Beta, Gamma paths*).
   * Desain dark-mode futuristik *Nuclear Gold* yang responsif untuk desktop maupun perangkat seluler.

---

## 🛠️ Tech Stack

* **Frontend**: HTML5, Vanilla CSS3 (Custom Design System), JavaScript (ES6+), Marked.js, Chart.js.
* **Backend API**: Python, FastAPI, Uvicorn, LangChain, Pydantic.
* **Desktop App**: Streamlit.
* **Database & Storage**: MongoDB Atlas dengan Fallback otomatis ke File Lokal (JSON & CSV).
* **AI Models**: Google Gemini, Groq (Llama 3.3), DeepSeek, OpenRouter, CrewAI.

---

## 📂 Struktur Proyek

```text
PROJECT ATOM/
├── dev_server.py           # 🚀 Server Development Lokal Web (FastAPI + Static)
├── ATOM_Chat.py            # 💻 Aplikasi UI Desktop (Streamlit)
├── vercel.json             # Konfigurasi deployment serverless Vercel
├── requirements.txt        # Daftar dependency Python
│
├── api/                    # 🌐 Backend API (FastAPI / Serverless)
│   ├── index.py            # Entry point API utama & route handler
│   ├── chat.py             # Logika endpoint chat multimodal & fallback
│   └── notes_ai.py         # Logika AI untuk Smart Notes (Refine & Tagging)
│
├── public/                 # 🎨 Frontend Web Interface
│   ├── index.html          # Halaman Chat utama
│   ├── notes.html          # Halaman Smart Notes
│   ├── telemetry.html      # Halaman Dashboard Telemetri
│   └── assets/
│       ├── css/            # Style sistem & tema
│       └── js/             # Logika aplikasi, partikel kanvas, & chat handler
│
├── modules/                # 🧠 Modul Inti Logika Bisnis
│   ├── core/
│   │   ├── cortex.py       # Neural Router & Fallback Provider Manager
│   │   ├── crew.py         # Orkestrasi Multi-Agent (Deep Research)
│   │   └── database.py     # Integrasi MongoDB & Penyimpanan Lokal
│   ├── notes/              # Manajemen penyimpanan catatan lokal
│   └── settings/           # Pengaturan styling & tema
│
└── data/                   # 💾 Data lokal & log telemetri
    ├── atom_notes.json
    └── atom_telemetry.csv
```

---

## 🚀 Cara Menjalankan

### 1. Menjalankan Aplikasi Web (Direkomendasikan)
Gunakan virtual environment yang sudah tersedia:
```powershell
# Jalankan Dev Server lokal
.\.venv\Scripts\python.exe dev_server.py
```
* Buka browser di: **`http://localhost:8000`**
* Dokumentasi API Swagger di: **`http://localhost:8000/docs`**

### 2. Menjalankan Aplikasi Desktop (Streamlit)
```powershell
.\.venv\Scripts\streamlit.exe run ATOM_Chat.py
```

---

## ⚙️ Konfigurasi Environment (`.env`)

Pastikan file `.env` di direktori utama telah memiliki konfigurasi API key yang diperlukan:
```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
MONGODB_URI=your_mongodb_connection_string # Opsional (otomatis fallback ke lokal)
```
