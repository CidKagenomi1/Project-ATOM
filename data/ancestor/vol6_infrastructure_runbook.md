# ANCESTOR CODEX — VOLUME VI
## INFRASTRUCTURE, SERVERLESS & RUNBOOK
> **Arsip:** `data/ancestor/vol6_infrastructure_runbook.md`  
> **Klasifikasi:** Panduan Operasional Infrastruktur, Deployment & Pemecahan Masalah  
> **Lingkungan:** Local Node (`dev_server.py`) & Cloud Serverless (`vercel.json`)  
> **Inisiator & Arsitek Utama:** Alif Rahmadi  
> **Kapasitas Target:** ~5.000 Token  

---

### DAFTAR ISI VOLUME VI
1. [Arsitektur Dual-Environment A.T.O.M. v4.0](#1-arsitektur-dual-environment-atom-v40)
2. [Konfigurasi & Pengoperasian Local Development Node](#2-konfigurasi--pengoperasian-local-development-node)
3. [Arsitektur Cloud Serverless Vercel & Bundling Module Python](#3-arsitektur-cloud-serverless-vercel--bundling-module-python)
4. [Protokol Ketahanan Serverless: Menghadapi Filesystem Read-Only](#4-protokol-ketahanan-serverless-menghadapi-filesystem-read-only)
5. [Daftar Periksa Kunci Lingkungan (Environment Variables Checklist)](#5-daftar-periksa-kunci-lingkungan-environment-variables-checklist)
6. [Buku Panduan Pemecahan Masalah (Troubleshooting Runbook)](#6-buku-panduan-pemecahan-masalah-troubleshooting-runbook)

---

### 1. ARSITEKTUR DUAL-ENVIRONMENT A.T.O.M. v4.0

A.T.O.M. dirancang dengan prinsip portabilitas tinggi. Sistem ini dapat dijalankan pada dua lingkungan yang sepenuhnya berbeda tanpa perlu merombak basis kode inti:

```
                  ┌─────────────────────────────────────────┐
                  │          A.T.O.M. REPOSITORY            │
                  │   FastAPI · LangChain · Cyber UI        │
                  └────────────────────┬────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        ┌───────────────────────┐             ┌───────────────────────┐
        │     LOCAL NODE        │             │   VERCEL SERVERLESS   │
        │ - dev_server.py       │             │ - vercel.json         │
        │ - Port 8000 (0.0.0.0) │             │ - /api/index.py       │
        │ - Local LAN / Wi-Fi   │             │ - Global Edge Network │
        │ - Local CSV & JSON    │             │ - /tmp Memory Buffer  │
        └───────────────────────┘             └───────────────────────┘
```

---

### 2. KONFIGURASI & PENGOPERASIAN LOCAL DEVELOPMENT NODE

#### 2.1 File Peluncur: `dev_server.py`
Server lokal menggunakan kerangka kerja ASGI `uvicorn` dengan integrasi penyajian berkas statis `FastAPI StaticFiles`:
* **Port Standar:** `8000`
* **Host Binding:** `0.0.0.0` (Bukan sekadar `127.0.0.1`).
  * *Mengapa 0.0.0.0?* Memungkinkan pengembang membuka akses web ke perangkat lain (smartphone, laptop rekan kerja, atau tablet) yang terhubung dalam satu jaringan Wi-Fi lokal yang sama.
* **Penyajian Aset:** Folder `public/` dipasang langsung ke rute akar (`/`) dengan penanganan file HTML otomatis (`html=True`).

#### 2.2 Perintah Peluncuran di Terminal:
```bash
# Menjalankan virtual environment lokal
.venv\Scripts\python.exe dev_server.py
```
Saat server menyala, log terminal akan menampilkan:
```text
Starting dev server on port 8000...
[*] ATOM Local Dev Server ready at http://localhost:8000
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### 3. ARSITEKTUR CLOUD SERVERLESS VERCEL & BUNDLING MODULE PYTHON

Ketika A.T.O.M. di-deploy ke cloud Vercel, arsitektur bertransformasi menjadi fungsi tanpa server (*Serverless Functions*).

#### 3.1 Konfigurasi Krusial di `vercel.json`
Vercel membutuhkan instruksi eksplisit untuk memaketkan modul Python yang berada di luar folder `api/`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": {
        "includeFiles": [
          "modules/**",
          "data/**"
        ]
      }
    },
    {
      "src": "public/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/public/$1"
    }
  ]
}
```

* **Pentingnya `includeFiles`:** Jika baris `"modules/**"` tidak disertakan, fungsi Python Vercel akan mengalami kegagalan *Cold Start* dengan error `ModuleNotFoundError: No module named 'modules'`.

---

### 4. PROTOKOL KETAHANAN SERVERLESS: MENGHADAPI FILESYSTEM READ-ONLY

#### 4.1 Akar Masalah Error 500 di Serverless
Di lingkungan Vercel AWS Lambda container:
* Seluruh disk sistem bersifat **Read-Only**.
* Kode Python yang mencoba mengeksekusi `with open("data/atom_bubbles.json", "w") as f:` akan langsung melempar:
  `OSError: [Errno 30] Read-only file system`.
* Tanpa penanganan khusus, eksepsi ini memicu `HTTP 500 FUNCTION_INVOCATION_FAILED`.

#### 4.2 Solusi Fallback `/tmp` di A.T.O.M.
A.T.O.M. mengimplementasikan fungsi pembungkus penyimpanan aman di `api/index.py` dan `modules/notes/note_storage.py`:
```python
def safe_save_json(filepath: str, data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        # Fallback cerdas untuk serverless read-only
        tmp_path = os.path.join("/tmp", os.path.basename(filepath))
        try:
            with open(tmp_path, "w", encoding="utf-8") as tf:
                json.dump(data, tf, indent=2)
        except Exception:
            pass
```
* Hasilnya: Aplikasi dapat beroperasi dengan mulus di Vercel tanpa pernah crash karena masalah izin tulis disk lokal.

---

### 5. DAFTAR PERIKSA KUNCI LINGKUNGAN (ENVIRONMENT VARIABLES CHECKLIST)

Sebelum melakukan deployment ke Vercel atau menyalakan server lokal, pastikan variabel-variabel berikut telah dikonfigurasi:

| Nama Variabel | Wajib / Opsional | Fungsi Utama | Contoh Nilai |
| :--- | :---: | :--- | :--- |
| `GROQ_API_KEY` | **Sangat Dianjurkan** | Akses komputasi LPU Tier 1 (Cortex & CrewAI) | `gsk_...` |
| `GROQ_MODEL` | Opsional | Model aktif default Groq | `openai/gpt-oss-120b` |
| `GOOGLE_API_KEY` | **Sangat Dianjurkan** | Jaring pengaman Tier 4 & Pemroses Multimodal Gambar | `AIzaSy...` |
| `GEMINI_MODEL` | Opsional | Versi model Google Gemini | `gemini-2.5-flash` |
| `OPENROUTER_API_KEY` | Opsional | Akses katalog model terbuka Tier 3 | `sk-or-v1-...` |
| `DEEPSEEK_API_KEY` | Opsional | Model penalaran analitis Tier 2 | `sk-...` |
| `MONGODB_URI` | Opsional | Database telemetri dan catatan cloud | `mongodb+srv://...` |

---

### 6. BUKU PANDUAN PEMECAHAN MASALAH (TROUBLESHOOTING RUNBOOK)

#### Masalah 1: "Saat diuji teman di web, semua AI mengembalikan Error 500"
* **Diagnosis:**
  1. Periksa apakah variabel lingkungan (`GROQ_API_KEY`, `GOOGLE_API_KEY`) sudah diisi di **Vercel Dashboard > Settings > Environment Variables**. Ingat bahwa file `.env` lokal tidak terkirim ke Git.
  2. Periksa apakah kuota harian Gemini gratis sedang habis (`429 RESOURCE_EXHAUSTED`). Pastikan kunci Groq aktif agar sistem otomatis mengalihkan failover ke Groq.
* **Solusi:** Tambahkan API key di Vercel Dashboard, lalu lakukan Redeploy (`git push` atau klik *Redeploy* di Vercel).

#### Masalah 2: "Model Groq Mengembalikan HTTP 404 Model Not Found"
* **Diagnosis:** Nama model yang diminta telah dipensiunkan oleh Groq (seperti `llama-3.3-70b-versatile`).
* **Solusi:** Periksa `modules/core/cortex.py` dan `api/chat.py`. Pastikan model default diarahkan ke model aktif seperti `openai/gpt-oss-120b` atau `qwen/qwen3.8-27b`.

#### Masalah 3: "Koneksi MongoDB Atlas Mengalami Timeout Saat Startup"
* **Diagnosis:** DNS resolving Atlas memakan waktu terlalu lama atau koneksi internet lokal terblokir firewall.
* **Solusi:** Di [modules/core/database.py](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/modules/core/database.py), pastikan parameter `serverSelectionTimeoutMS` disetel ke `1500` (1.5 detik) agar proses booting langsung beralih ke penyimpanan lokal tanpa membuat aplikasi membeku (*hang*).

---
*Akhir dari Dokumen Ancestor Codex: Volume VI*
