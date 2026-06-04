# Struktur Aplikasi A.T.O.M. (Autonomous Task Orchestration Machine)

Dokumen ini menjelaskan struktur folder, modul, tanggung jawab file, dan alur data dari aplikasi **ATOM (v4.0 Cortex)**. Aplikasi ini dirancang hybrid: dapat dijalankan sebagai aplikasi desktop berbasis Streamlit (`ATOM_Chat.py`) maupun dideploy ke web (Vercel/Local Server) melalui folder API Serverless (`api/`) dan Frontend Statis (`public/`).

---

## 📁 Pohon Struktur Direktori

```text
PROJECT ATOM/
│
├── ATOM_Chat.py            # Aplikasi UI Desktop utama (Streamlit)
├── dev_server.py           # Server lokal untuk development web (Port 3000)
├── vercel.json             # Konfigurasi deployment serverless Vercel
├── requirements.txt        # Daftar dependency Python
├── README.md               # Dokumentasi umum proyek
│
├── api/                    # Backend API (Vercel Serverless Functions)
│   ├── chat.py             # Handler API untuk chat & vision fallback
│   └── notes_ai.py         # Handler API untuk pemrosesan AI pada Smart Notes
│
├── public/                 # Frontend Web (Aset Statis HTML/CSS/JS)
│   ├── index.html          # Halaman utama interface Chat
│   ├── notes.html          # Halaman Smart Notes
│   ├── telemetry.html      # Halaman visualisasi data & metrik AI
│   └── assets/
│       ├── css/
│       │   ├── main.css    # Desain global, variabel CSS, & tema gelap/emas
│       │   └── components.css # Styling detail chat bubbles, input, & expander
│       └── js/
│           ├── app.js      # Navigasi sidebar responsif & UI global
│           ├── chat.js     # Logika chat, paste clipboard screenshot, & render UI
│           ├── notes.js    # Manajemen CRUD catatan & integrasi AI Notes
│           └── telemetry.js # Pembuat grafik latensi & performa model
│
├── modules/                # Modul Python Core (Logika Bisnis)
│   ├── core/               # Pusat Logika AI & Eksekusi
│   │   ├── cortex.py       # Pengatur router AI & fallback provider (Gemini/Groq)
│   │   ├── interpreter.py  # Eksekutor kode Python dinamis (sandbox)
│   │   └── crew.py         # Orkestrasi multi-agent (Deep Research)
│   │
│   ├── notes/              # Fitur Smart Notes
│   │   ├── note_brain.py   # AI pembuat rangkuman & pengindeks note
│   │   └── note_storage.py # Penyimpanan data note lokal (.json)
│   │
│   └── settings/           # Pengaturan Aplikasi
│       └── style_manager.py # Manajemen kustomisasi tema visual
│
├── data/                   # Database Lokal & Telemetri (Format JSON & CSV)
│   ├── atom_notes.json     # File penyimpanan catatan umum
│   ├── atom_smart_notes.json # File penyimpanan smart notes terenkripsi/terindeks
│   ├── atom_bubbles.json   # Penyimpanan prompt bubbles/shortcuts
│   └── atom_telemetry.csv  # Log statistik latensi, token, & kegagalan model
│
└── archive/                # Folder Legacy / Cadangan
    ├── project_atom.py     # Desain awal program atom desktop
    ├── atom_legacy.py      # Kode program versi lawas
    └── atom_brainstorm_erd.json # Desain rancangan database awal
```

---

## 🛠️ Penjelasan Tanggung Jawab Komponen

### 1. Entry Points (Titik Masuk Aplikasi)
*   **[ATOM_Chat.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/ATOM_Chat.py)**: Kode UI berbasis Streamlit. Ini memuat modul-modul di bawah `modules/` untuk menyajikan visualisasi chat dan notes versi desktop.
*   **[dev_server.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/dev_server.py)**: Server HTTP bawaan Python yang berjalan di localhost:3000 untuk memetakan rute `/api/*` ke fungsi serverless Python, dan folder `/public` sebagai root dokumen web statis untuk proses uji coba/development web lokal.

### 2. Backend API (`/api`)
*   **[api/chat.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/api/chat.py)**: Menerima request `POST` berisi history chat, prompt, dan lampiran file/gambar. Mengarahkan prompt secara cerdas, memotong data base64 untuk model non-vision (mencegah crash), dan menyusun pesan multimodal vision untuk Gemini/OpenRouter.
*   **[api/notes_ai.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/api/notes_ai.py)**: Menggunakan kecerdasan buatan untuk merangkum catatan, mendeteksi kategori, dan membuat tag otomatis berdasarkan konten catatan yang dikirim frontend.

### 3. Core Modules (`/modules`)
*   **[modules/core/cortex.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/modules/core/cortex.py)**: Otak utama ATOM. Mengambil keputusan apakah prompt butuh agen riset (`CREW`) atau cukup jawaban AI standar. Mengatur fallback otomatis jika API key penyedia utama (misal Groq) bermasalah untuk beralih ke cadangan (Gemini).
*   **[modules/core/interpreter.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/modules/core/interpreter.py)**: Membaca blok kode di dalam jawaban, mengeksekusinya secara lokal, dan mengembalikan output (hasil print/error runtime) langsung ke chat.
*   **[modules/core/crew.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/modules/core/crew.py)**: Menjalankan agen-agen riset mandiri untuk melakukan investigasi mendalam terhadap topik sulit.

---

## 🔄 Alur Kerja Data (Data Flow)

### Kirim Pesan & Gambar (Vision Chat)
1. Pengguna memasukkan teks/menempelkan (`Ctrl+V`) screenshot gambar di **[index.html](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/public/index.html)**.
2. Script **[chat.js](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/public/assets/js/chat.js)** membaca file gambar sebagai Base64 string dan mengirim request POST JSON ke `/api/chat`.
3. Fungsi **[api/chat.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/api/chat.py)** memisahkan lampiran gambar dengan teks.
4. Jika model terpilih mendukung vision (seperti Gemini 1.5 Flash), API akan menyusun payload multimodal dan memanggil model tersebut. Jika model tidak mendukung vision (seperti Groq Llama-3.3), data base64 dilewati agar payload tetap aman tanpa crash.
5. Jawaban AI dikirim kembali, dirender dalam format Markdown yang indah di web, dan statistik durasi serta jenis model dicatat ke dalam database telemetri.
