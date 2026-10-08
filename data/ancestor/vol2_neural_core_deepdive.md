# ANCESTOR CODEX — VOLUME II
## THE NEURAL CORE & ALGORITHMIC DEEP DIVE
> **Arsip:** `data/ancestor/vol2_neural_core_deepdive.md`  
> **Klasifikasi:** Spesifikasi Algoritma, Routing Heuristics, & Failover Matrix  
> **Komponen Inti:** Cortex v4.0, Librarian, Sentinel, & CrewAI  
> **Inisiator & Arsitek Utama:** Alif Rahmadi  
> **Kapasitas Target:** ~10.000 Token  

---

### DAFTAR ISI VOLUME II
1. [Bedah Arsitektur Cortex Neural Router v4.0](#1-bedah-arsitektur-cortex-neural-router-v40)
2. [Pohon Keputusan Perutean Cerdas (Routing Heuristics Tree)](#2-pohon-keputusan-perutean-cerdas-routing-heuristics-tree)
3. [Matriks Failover Multi-Tier & Circuit Breaker Pattern](#3-matriks-failover-multi-tier--circuit-breaker-pattern)
4. [Librarian Engine: Matematika Token & Sliding Context Window](#4-librarian-engine-matematika-token--sliding-context-window)
5. [Sentinel Observability Engine: Radar Telemetri Real-Time](#5-sentinel-observability-engine-radar-telemetri-real-time)
6. [CrewAI Orchestration Dynamics: Skuad Riset Multi-Agen](#6-crewai-orchestration-dynamics-skuad-riset-multi-agen)
7. [Logika Pemulihan Kesalahan Kritis (Error Recovery Runbook)](#7-logika-pemulihan-kesalahan-kritis-error-recovery-runbook)

---

### 1. BEDAH ARSITEKTUR CORTEX NEURAL ROUTER v4.0

Cortex adalah otak pengatur lalu lintas otonom di dalam sistem A.T.O.M. v4.0. Cortex tidak menjalankan satu model secara statis; ia bertindak sebagai konduktor orkestra yang memilih model LLM terbaik di awan berdasarkan karakteristik kueri pengguna.

```
                    ┌────────────────────────────┐
                    │    Kueri Pengguna Masuk    │
                    │   (Prompt + Image/Files)   │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │   Cortex Intent Analyzer   │
                    │   - Deteksi Gambar/Visual  │
                    │   - Deteksi Riset CrewAI   │
                    │   - Evaluasi Kompleksitas  │
                    └─────────────┬──────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
  [Multimodal Path]       [Deep Research Path]     [Direct Chat Path]
   Gemini Vision           CrewAI Multi-Agent       Multi-Tier Router
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │  Sentinel Telemetry Record │
                    │  - Latensi (Detik)         │
                    │  - Status Rute / Failover  │
                    │  - Token Estimate          │
                    └────────────────────────────┘
```

#### 1.1 Komponen Internal Kelas `ATOMCortex`
Di dalam berkas `modules/core/cortex.py`, kelas `ATOMCortex` memegang komponen-komponen vital:
* `self.librarian`: Menjaga batas konteks percakapan dengan sliding window.
* `self.system_prompt`: Menyimpan persona dasar A.T.O.M., aturan format Markdown, serta data otoritatif sistem.
* `self.model_configs`: Konfigurasi nama model untuk setiap penyedia (Groq, DeepSeek, OpenRouter, Gemini).
* `self.process()`: Fungsi utama yang menerima `user_input`, `model_preference`, `image_files`, dan callback status.

---

### 2. POHON KEPUTUSAN PERUTEAN CERDAS (ROUTING HEURISTICS TREE)

Ketika preferensi model disetel ke mode default `auto`, Cortex mengevaluasi instruksi melalui hierarki logika terstruktur berikut:

#### Langkah 1: Deteksi Lampiran Multimodal Visual
* **Kondisi:** Apakah `image_files` tidak kosong atau apakah prompt menyertakan tautan gambar base64 (`data:image/...`)?
* **Aksi:** Rute langsung dialihkan ke **Tier 4: Google Gemini Flash 2.5**. Model Groq atau DeepSeek berbasis teks murni tidak dipanggil agar tidak menghasilkan error format.

#### Langkah 2: Deteksi Kata Kunci Riset Otonom (CrewAI Trigger)
* **Kondisi:** Apakah teks mengandung kata kunci: `riset mendalam:`, `investigasi:`, `analisis komprehensif:`, `research about:`, atau `deep research:`?
* **Aksi:** Rute dialihkan ke modul `modules/core/crew.py` untuk mengaktifkan skuad multi-agen otonom.

#### Langkah 3: Evaluasi Kompleksitas Kognitif
* **Kasus A: Percakapan Cepat, Ideasi, & Tugas Standar (90% Kueri):**
  * Dialihkan ke **Tier 1 (Groq Cloud)** menggunakan model berkecepatan tinggi `openai/gpt-oss-120b` atau `qwen/qwen3.8-27b`.
  * Menghasilkan kecepatan respons inferensi kilat (~500 token/detik) dengan durasi total di bawah 2 detik.
* **Kasus B: Pemecahan Masalah Matematika Kompleks, Algoritma Rumit, atau Audit Keamanan:**
  * Dialihkan ke **Tier 2 (DeepSeek Cloud)** untuk penalaran analitis mendalam (*CoT - Chain of Thought*).

---

### 3. MATRIKS FAILOVER MULTI-TIER & CIRCUIT BREAKER PATTERN

Salah satu inovasi terbesar pada A.T.O.M. v4.0 adalah ketahanan anti-gagal (*Self-Healing Failover*). Matriks failover ini mencegah situasi di mana teman atau pengguna menerima halaman putih atau pesan `HTTP 500 Internal Server Error`.

#### 3.1 Tabel Matriks Penyedia & Urutan Failover

| Tingkat | Penyedia AI | Model Utama / Cadangan | Karakteristik Utama | Kode Kegagalan Pemicu Failover |
| :---: | :--- | :--- | :--- | :--- |
| **Tier 1** | **Groq Cloud (LPU)** | `openai/gpt-oss-120b`<br>`qwen/qwen3.8-27b`<br>`openai/gpt-oss-20b` | Eksekusi tercepat di dunia (~500 t/s), bebas biaya. | `404` (Model Not Found)<br>`429` (Rate Limited)<br>`503` (Service Overloaded) |
| **Tier 2** | **DeepSeek Cloud** | `deepseek-chat`<br>`deepseek-reasoner` | Penalaran mendalam, arsitektur MoE (Mixture-of-Experts). | `402` (Insufficient Balance)<br>`429` (Quota Reached)<br>`Timeout > 15s` |
| **Tier 3** | **OpenRouter Hub** | `nemotron-3-super-120b-a12b:free`<br>`gemma-4-31b-it:free`<br>`lfm-2.5-2.6b:free` | Model hub dunia, cadangan model bebas biaya aktif. | `404` (Slug Invalid)<br>`429` (Daily Free Cap)<br>`502` (Upstream Error) |
| **Tier 4** | **Google Gemini** | `gemini-2.5-flash`<br>`gemini-1.5-flash` | Jaring pengaman terakhir, context window 1M, multimodal. | `429` (Daily Request Exceeded)<br>`500` (Internal Google Error) |

#### 3.2 Pola Circuit Breaker (Anti-Freeze Mechanism)
Jika sebuah penyedia layanan mengembalikan error:
1. **Pencegahan Timeout Menggantung:** Cortex menetapkan batas waktu tegas per-request (10 detik untuk Groq, 15 detik untuk DeepSeek). Jika model tidak merespons dalam durasi tersebut, panggilan langsung dibatalkan (*aborted*).
2. **Instant Provider Leap:** Sistem tidak mengulang (*retry*) model yang sama berulang kali jika kode error adalah `429` atau `404`. Sistem langsung "melompat" ke tier berikutnya dalam hitungan 50 milidetik.
3. **Pencatatan Insiden ke Sentinel:** Setiap transisi failover dicatat dengan label `[FAILOVER] Groq -> OpenRouter` di riwayat telemetri untuk memudahkan audit performa.

---

### 4. LIBRARIAN ENGINE: MATEMATIKA TOKEN & SLIDING CONTEXT WINDOW

#### 4.1 Tantangan Pembengkakan Konteks (Context Bloat)
Dalam percakapan yang panjang (misalnya 30 kali tanya jawab), riwayat teks obrolan bisa membengkak melebihi puluhan ribu token. Ini menimbulkan tiga bahaya besar:
* Biaya kuota token melonjak drastis.
* Waktu inferensi model melambat karena memproses seluruh riwayat lama.
* Menabrak batas token model (*Context Window Overflow*), memicu error 400 Bad Request.

#### 4.2 Formula Perhitungan Token Heuristik
Modul Librarian menggunakan formula perkiraan token berbasis karakter dan kata:
$$\text{Tokens Estimate} = \frac{\text{Karakter Teks Bahasa Indonesia}}{3.8}$$
Bahasa Indonesia umumnya memiliki rasio token per kata yang sedikit lebih tinggi dibanding Bahasa Inggris karena bentuk imbuhan (prefiks, sufiks, konfiks). Nilai pembagi `3.8` adalah estimasi konservatif yang terbukti akurat dalam pengujian praktis.

#### 4.3 Algoritma Sliding Context Window
Librarian menjaga riwayat obrolan dengan algoritma berikut:
```python
def get_optimized_history(raw_history, max_tokens=6000):
    current_tokens = 0
    optimized = []
    # Memproses pesan dari yang paling baru ke yang paling lama
    for msg in reversed(raw_history):
        msg_tokens = len(msg["content"]) / 3.8
        if current_tokens + msg_tokens > max_tokens:
            break
        optimized.insert(0, msg)
        current_tokens += msg_tokens
    return optimized
```
* Pesan yang berada di luar batas `max_tokens` dipotong secara mulus dari memori kerja, sementara `ATOM_SYSTEM_PROMPT` dan dokumen `Ancestor` tetap dipertahankan utuh pada awal konteks.

---

### 5. SENTINEL OBSERVABILITY ENGINE: RADAR TELEMETRI REAL-TIME

Sentinel adalah komponen pengawas yang memastikan sistem A.T.O.M. selalu terpantau secara transparan.

#### 5.1 Skema Data Telemetri
Setiap transaksi obrolan atau panggilan fungsi AI menghasilkan catatan telemetri dengan skema:
```json
{
  "timestamp": "2026-10-09 03:33:08",
  "user_input": "Verifikasi Arsitektur Sentinel",
  "model_used": "Groq-gpt-oss-120b",
  "response_time": 1.12,
  "tokens": 85,
  "status": "success",
  "ai_response": "Sentinel online dan mencatat telemetri dengan sukses."
}
```

#### 5.2 Strategi Penyimpanan Berlapis (Hybrid Persistence)
Untuk mencegah data telemetri hilang sekaligus menjaga kecepatan rendering antarmuka, Sentinel menggunakan arsitektur 4 lapis:
1. **Lapis 1 — In-Memory Buffer:** Data disimpan instan di memori RAM Python saat request selesai (<1ms).
2. **Lapis 2 — Client LocalStorage:** Browser menyimpan salinan log terakhir di `localStorage['atom_telemetry_logs']` sehingga halaman Telemetry langsung menampilkan grafik tanpa menunggu server.
3. **Lapis 3 — File CSV Lokal:** Pada node server lokal (`dev_server.py`), data dicatat ke `data/atom_telemetry.csv`.
4. **Lapis 4 — Cloud Database (MongoDB Atlas):** Jika string koneksi `MONGODB_URI` tersedia di environment, Sentinel mengirimkan log ke koleksi `telemetry` dengan timeout koneksi aman 1.5 detik (`serverSelectionTimeoutMS=1500`).

---

### 6. CREWAI ORCHESTRATION DYNAMICS: SKUAD RISET MULTI-AGEN

Terletak di dalam `modules/core/crew.py`, CrewAI di A.T.O.M. memisahkan beban riset menjadi dua spesialisasi:

#### 6.1 Agen Senior Researcher
* **Peran:** Ahli analisis metodologi riset, teknologi, dan intelijen pasar.
* **Tugas:** Menemukan fakta utama, menguraikan statistik relevan, mengidentifikasi tantangan dan risiko, serta menyusun intisari poin kunci (*Bullet Points Findings*).
* **Konfigurasi LLM:** Ditenagai oleh `ChatGroq(model="openai/gpt-oss-120b", temperature=0.3)` untuk menjamin kepatuhan pada fakta dan akurasi tinggi.

#### 6.2 Agen Content Writer
* **Peran:** Spesialis penyusun artikel dan laporan taktis berbahasa Indonesia.
* **Tugas:** Mengubah temuan mentah dari Senior Researcher menjadi laporan Markdown komprehensif dengan struktur:
  * Judul artikel yang tajam dan berwibawa.
  * Pendahuluan dan latar belakang masalah.
  * Analisis mendalam topik dengan sub-bab terstruktur.
  * Poin aksi nyata (*Actionable Takeaways*) dan rekomendasi strategis.
  * Kesimpulan ringkas.

#### 6.3 Alur Eksekusi Berantai (Sequential Pipeline)
```
[Topik Riset dari Pengguna]
           │
           ▼
┌─────────────────────────────┐
│    Senior Researcher Task   │ ───> Menghasilkan Wawasan Kunci & Data Mentah
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     Content Writer Task     │ ───> Merangkai Laporan Markdown Lengkap
└──────────────┬──────────────┘
               │
               ▼
[Laporan Riset Disajikan ke Pengguna]
```

---

### 7. LOGIKA PEMULIHAN KESALAHAN KRITIS (ERROR RECOVERY RUNBOOK)

Cortex dirancang untuk merespons kegagalan operasional secara tenang dan terukur:

1. **Kasus Kuota Gemini 429:**
   * Gejala: Google API merespons `RESOURCE_EXHAUSTED`.
   * Penanganan: Cortex menangkap eksepsi, mengabaikan Gemini, dan segera memanggil `ChatGroq`. Pengguna menerima jawaban dalam 2 detik tanpa mengetahui bahwa Gemini sedang kehabisan kuota.
2. **Kasus Nama Model Groq Deprecated (404):**
   * Gejala: Penyedia menghapus nama model lama (misal `llama-3.3-70b-versatile`).
   * Penanganan: Cortex mencoba daftar model fallback aktif (`openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`) sebelum menyerah.
3. **Kasus Filesystem Read-Only (Vercel Serverless):**
   * Gejala: `OSError: [Errno 30] Read-only file system` saat menyimpan sesi ke `data/*.json`.
   * Penanganan: Fungsi `safe_save_json()` secara otomatis mengalihkan penulisan ke direktori `/tmp` memori Lambda tanpa melempar HTTP 500.

---
*Akhir dari Dokumen Ancestor Codex: Volume II*
