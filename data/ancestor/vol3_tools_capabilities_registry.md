# ANCESTOR CODEX — VOLUME III
## TOOLS, MODULES & CAPABILITIES REGISTRY
> **Arsip:** `data/ancestor/vol3_tools_capabilities_registry.md`  
> **Klasifikasi:** Registri Otoritatif Tools, Agen, Utilitas, & Endpoint Fungsional  
> **Inisiator & Arsitek Utama:** Alif Rahmadi  
> **Sistem:** A.T.O.M. (Autonomous Task Orchestration Machine) v4.0 Cloud-Native  
> **Kapasitas Target:** ~6.000 Token  

---

### DAFTAR ISI VOLUME III
1. [Pilar 1: Core Orchestration & Routing Tools](#1-pilar-1-core-orchestration--routing-tools)
2. [Pilar 2: Live Web Search & Scraping Tools](#2-pilar-2-live-web-search--scraping-tools)
3. [Pilar 3: Multi-Agent & System Action Tools](#3-pilar-3-multi-agent--system-action-tools)
4. [Pilar 4: Zero-Token Local Knowledge & Banter Tools](#4-pilar-4-zero-token-local-knowledge--banter-tools)
5. [Pilar 5: Smart Notes (Crew Notes) & Co-Pilot AI Tools](#5-pilar-5-smart-notes-crew-notes--co-pilot-ai-tools)
6. [Pilar 6: Multi-Format Document Importer & Multimodal Tools](#6-pilar-6-multi-format-document-importer--multimodal-tools)
7. [Pilar 7: News Bulletin & Executive Summarizer Tools](#7-pilar-7-news-bulletin--executive-summarizer-tools)

---

### 1. PILAR 1: CORE ORCHESTRATION & ROUTING TOOLS

Lapisan orkestrasi inti mengatur rute eksekusi kueri, failover lintas penyedia LLM, ekstraksi penalaran, manajemen memori percakapan, hingga telemetri sistem:

#### 1.1 Neural Router (`NeuralRouter.decide_route`)
* **Lokasi:** `modules/core/router.py`
* **Fungsi:** Mengklasifikasikan instruksi pengguna secara heuristik deterministik ke dalam tiga jalur eksekusi:
  * `ACTION` — Perintah aksi fisik/sistem OS (seperti `buka notepad`, `buka calculator`, `buka spotify`, `buka browser`, `buka youtube`, `cek baterai`, `matikan laptop`, `restart`), apabila input bukan berupa kalimat tanya.
  * `CREW` — Tugas riset mendalam multi-agen ketika dipicu kata kunci `riset mendalam:`, `deep research:`, atau `investigasi komprehensif:`.
  * `AI` — Jalur standar untuk percakapan umum, pemrograman, penalaran mendalam, dan analisis multimodal.

#### 1.2 Cortex Multi-Provider Dispatcher (`ATOMCortex._call_ai_with_timeout`)
* **Lokasi:** `modules/core/cortex.py`
* **Fungsi:** Pengatur lalu lintas AI dengan mekanisme *self-healing failover* berantai:
  * Mendukung **Ollama (`LocalOllamaBrain`)**, **Groq Cloud (LPU)**, **OpenRouter**, **Hugging Face Router**, serta **Google Gemini** (`ChatGoogleGenerativeAI` / `_call_gemini_rest`) sebagai jaring pengaman dan pemroses multimodal.
  * Mendukung pemilihan model eksplisit via `model_preference` maupun mode `auto`.

#### 1.3 Deep Reasoning / Chain-of-Thought Parser (`extract_reasoning`)
* **Lokasi:** `modules/core/reasoning_parser.py`
* **Fungsi:** Mengekstrak jejak berpikir internal model penalaran dari tag `<think>`, `<thought>`, `<thinking>`, serta field API `reasoning_content`, `reasoning`, dan `thinking_process` (`extract_from_langchain_response`).
* **Manfaat:** Memisahkan proses berpikir mentah ke panel *View Reasoning* di UI agar gelembung jawaban utama tetap bersih dan memori `Librarian` tidak tercemar token berpikir internal.

#### 1.4 Librarian — Memory & Session Manager (`Librarian`)
* **Lokasi:** `modules/core/librarian.py` & `api/routes/sessions.py`
* **Fungsi:** Mengelola konteks percakapan menggunakan *sliding window* (`add_interaction`, `get_context`, `clear` dengan batas riwayat terpotong otomatis ke 6 entri terbaru saat melebihi 8 pesan) serta sinkronisasi multi-sesi percakapan.

#### 1.5 Sentinel — Telemetry Logger (`Sentinel`)
* **Lokasi:** `modules/core/sentinel.py` & `api/routes/telemetry.py`
* **Fungsi:** Mencatat *timestamp*, ringkasan input, model yang digunakan, durasi respons (`response_time`), dan status eksekusi (`SUCCESS` / `FAILOVER`) ke `data/atom_telemetry.csv` dan endpoint telemetri.

---

### 2. PILAR 2: LIVE WEB SEARCH & SCRAPING TOOLS

A.T.O.M. dilengkapi perangkat pencarian web real-time paralel dan ekstraksi konten halaman web tanpa ketergantungan API berbayar:

#### 2.1 Multi-Source Live Web Search (`search_web_for_notes` & `build_chat_web_grounding`)
* **Lokasi:** `modules/notes/web_search.py`
* **Mekanisme:** Menjalankan 5 worker paralel melalui `ThreadPoolExecutor`:
  1. **Bing Web Search RSS** (`_search_bing_rss`) — Hasil pencarian web umum dengan metadata domain & tanggal publikasi.
  2. **Google News RSS Indonesia** (`_search_google_news_rss`) — Artikel berita terkini berbahasa Indonesia (`hl=id&gl=ID`).
  3. **Wikipedia API (ID)** (`_search_wikipedia`, `lang="id"`) — Referensi ensiklopedia Bahasa Indonesia.
  4. **Wikipedia API (EN)** (`_search_wikipedia`, `lang="en"`) — Referensi ensiklopedia Bahasa Inggris.
  5. **Explicit URL Scraper** (`_scrape_explicit_urls`) — Otomatis mengekstrak konten halaman jika prompt atau konteks catatan menyertakan URL `http`/`https`.
* **Chat Auto-Grounding (`should_search_web_for_chat`):** Secara otomatis memicu pencarian web untuk pertanyaan umum di Chat, sekaligus melewati sapaan singkat, review lampiran statis, dan kueri internal arsitektur A.T.O.M. (`_INTERNAL_ATOM_PATTERNS`).

#### 2.2 Web Page Scraper & File Reader (`scrape_url` & `read_file_content`)
* **Lokasi:** `modules/core/utils.py`
* **Fungsi:**
  * `scrape_url(url)`: Mengambil dan membersihkan teks artikel dari halaman web menggunakan `requests` + `BeautifulSoup` (menghapus `script`, `style`, `nav`, `footer`, `header`, `aside` dengan batas aman 10.000 karakter).
  * `read_file_content(uploaded_file)`: Membaca konten berkas teks (`.txt`, `.md`, `.py`, `.json`, `.csv`, `.html`, `.css`, `.js`) dan PDF (`PyPDF2`).

---

### 3. PILAR 3: MULTI-AGENT & SYSTEM ACTION TOOLS

#### 3.1 CrewAI Autonomous Research Squad (`run_research_crew`)
* **Lokasi:** `modules/core/crew.py`
* **Fungsi:** Menjalankan riset mendalam berbasis tim dua agen berurutan (`Process.sequential`) dengan dukungan LLM Groq/Gemini dan pengayaan data web terkini dari `search_web_for_notes`:
  1. **Senior Researcher:** Menggali poin kunci, fakta, statistik, peluang, tantangan, serta *best practices*.
  2. **Content Writer:** Menyusun hasil temuan menjadi artikel Markdown terstruktur lengkap dalam Bahasa Indonesia.
* **Resilience:** Dilengkapi `_fallback_research` berbasis LLM langsung + *live web search* apabila eksekusi CrewAI mengalami kendala runtime/import.

#### 3.2 ATOM Hands — System Executor (`execute_system_action`)
* **Lokasi:** `modules/core/interpreter.py`
* **Fungsi:** Menerjemahkan perintah bahasa natural menjadi niat JSON terstruktur menggunakan Groq LLM, lalu mengeksekusi aksi desktop Windows melalui **PyAutoGUI** dan **psutil**:
  * **`BROWSER`**: Membuka Chrome via Windows Search, memfokuskan *address bar* (`Ctrl+L`), dan menavigasi ke URL target atau kueri Google/YouTube.
  * **`APP`**: Membuka aplikasi Windows terinstal (`calculator`, `notepad`, `cmd`, `explorer`, `visual studio code`, `spotify`).
  * **`SYSTEM`**: Mengecek status & persentase baterai via `psutil.sensors_battery()`, mengunci layar PC (`Win + L`), serta membatalkan aksi `shutdown` otomatis demi keamanan sistem (`[SAFETY]`).

---

### 4. PILAR 4: ZERO-TOKEN LOCAL KNOWLEDGE & BANTER TOOLS

#### 4.1 Ancestor Engine (`AncestorEngine`)
* **Lokasi:** `modules/core/ancestor.py`
* **Fungsi Dual-Mode:**
  * **Ancestor Echo (`match_echo`):** Menjawab pertanyaan baku seputar identitas A.T.O.M., pembuat (Alif Rahmadi), cara kerja Cortex, CrewAI, arsitektur sistem, dan daftar *tools* secara deterministik (0 token LLM).
  * **Ancestor Synthesis (`get_relevant_context`):** Memuat 8 volume Codex dari `data/ancestor/*.md` serta `master_knowledge.md` ke memori dan menyuntikkan bagian yang relevan berdasarkan kata kunci prompt.

#### 4.2 Banter Matrix Engine (`BanterEngine`)
* **Lokasi:** `modules/core/banter_matrix.py`
* **Fungsi:** Mengintersep obrolan santai secara lokal dalam **12 kluster intent** terprioritas (`COMPARISONS`, `RIVALRY`, `BIOLOGICAL`, `ROMANCE`, `EXISTENTIAL`, `EMOTIONS`, `HUMOR`, `TROLLING`, `DAILY_LIFE`, `TOUR`, `IDENTITY`, `GREETINGS`) dengan memori anti-repetisi tanpa mengonsumsi token cloud.

---

### 5. PILAR 5: SMART NOTES (CREW NOTES) & CO-PILOT AI TOOLS

Seluruh perangkat kecerdasan catatan tersedia melalui `api/notes_ai.py`, `api/routes/notes.py`, dan `api/routes/bubbles.py`, didukung failover LLM `invoke_llm_safely` (**Groq $\rightarrow$ OpenRouter $\rightarrow$ Hugging Face $\rightarrow$ Gemini**):

| Tool / Fungsi | Endpoint / Action | Deskripsi Kemampuan |
| :--- | :--- | :--- |
| **Knowledge Co-Pilot** (`chat_with_context`) | `POST /api/notes_ai` (`action="chat"`) | Tanya-jawab interaktif ala NotebookLM berbasis konten catatan sumber dengan sitasi `[Sumber: ...]` dan opsi `web_search` real-time. |
| **Smart Contextual Insertion** (`smart_insert_into_note`) | `POST /api/notes_ai` (`action="smart_insert"`) | Menyisipkan output Co-Pilot ke posisi heading yang paling relevan di catatan tanpa menghapus teks asli (mode `contextual`, `heading`, `append`). |
| **AI Study Note Generator** (`generate_study_note`) | `POST /api/notes_ai` (`action="study_note"`) | Mengubah dokumen/teks mentah menjadi catatan belajar Markdown lengkap dengan 3 gaya: `comprehensive`, `exam_prep`, dan `deep_dive`. |
| **Magic Article Formatter** (`refine_text`) | `POST /api/notes_ai` (`action="refine"`) | Merapikan teks mentah menjadi Markdown dengan 4 preset: `structured`, `minutes` (notulensi + checklist), `summary` (TL;DR), dan `grammar`. |
| **Micro-AI Selection Tools** (`process_micro_ai`) | `POST /api/notes_ai` (`action="micro"`) | Aksi cepat pada teks terseleksi: `refine`, `summarize`, `explain`, `translate` (ID $\leftrightarrow$ EN), dan `todo` (ekstraktor checklist `- [ ]`). |
| **Auto-Tagging & Auto-Title** (`auto_tag`, `generate_title`) | `POST /api/notes_ai` (`autotag`, `title`) | Menghasilkan 3–5 tag lowercase relevan dan judul ringkas maksimal 6 kata. |
| **Pydantic Metadata Extractor** (`generate_metadata_pydantic`) | `POST /api/notes_ai` (`action="metadata"`) | Mengekstrak `title`, `tags`, dan `summary` tervalidasi skema `NoteMetadata` menggunakan `pydantic_ai` (dengan fallback otomatis). |
| **Concept Bubbles Expander** (`expand_bubble`) | `POST /api/bubbles/{id}/expand` | Mengubah ide kilat menjadi artikel catatan terstruktur penuh menggunakan CrewAI atau `invoke_llm_safely`. |

---

### 6. PILAR 6: MULTI-FORMAT DOCUMENT IMPORTER & MULTIMODAL TOOLS

#### 6.1 Universal Document Parser (`parse_uploaded_document`)
* **Lokasi:** `modules/notes/file_importer.py` & `POST /api/notes/import_file` (serta `action="parse_file"` di `api/notes_ai.py`)
* **Format yang Didukung:**
  * **Dokumen & Presentasi:** `.pdf` (berantai via `pdfplumber` $\rightarrow$ `pypdfium2` $\rightarrow$ `pdfminer.six` $\rightarrow$ `PyPDF2`), `.docx` (ekstraksi paragraf, heading, list, dan tabel langsung dari XML), `.pptx` (ekstraksi teks per slide).
  * **Spreadsheet & Data Terstruktur:** `.xlsx`, `.xlsm` (`openpyxl` + fallback XML stdlib ke tabel Markdown multi-sheet), `.csv`, `.tsv` (deteksi delimiter otomatis), `.json` (pretty-print).
  * **Web, Teks & Kode Sumber:** `.html`/`.htm` (`BeautifulSoup` + fallback `HTMLParser`), `.md`, `.txt`, serta **18 ekstensi kode sumber** dalam `CODE_LANG_MAP` (`.py`, `.js`, `.ts`, `.sql`, `.yaml`, `.yml`, `.xml`, `.css`, `.sh`, `.bat`, `.ps1`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.php`, `.rb`).

#### 6.2 Multimodal Image & Attachment Handler
* **Lokasi:** `api/routes/chat.py` & `public/assets/js/modules/attachment-manager.js`
* **Fungsi:** Memisahkan lampiran gambar base64 (`data:image/...`, termasuk *instant clipboard paste* `Ctrl+V`) untuk rute Vision dan membungkus lampiran file teks ke blok `[FILE: ...]` sebelum diproses `ATOMCortex`.

---

### 7. PILAR 7: NEWS BULLETIN & EXECUTIVE SUMMARIZER TOOLS

* **Lokasi:** `api/routes/bulletin.py`
* **Komponen Tools:**
  1. **Live News Aggregator (`GET /api/bulletin/fetch` — `fetch_bulletin`):** Mengambil berita terbaru melalui **NewsAPI** dengan fallback otomatis ke **GNews API**, mendukung cakupan **Nasional (`national`)** (dilengkapi filter kata kunci negatif anti-berita kriminal) dan **Internasional (`international`)** lintas kategori (`technology`, `biology`, `geography`, `astronomy`, `discoveries`, `business`, `politics`, `culture`, `general`).
  2. **Bookmark & Persistence (`GET /api/bulletin/marked`, `POST /api/bulletin/mark`, `POST /api/bulletin/unmark`):** Menyimpan dan mengelola berita bertanda di MongoDB atau JSON lokal (`data/atom_bulletin_marked.json`).
  3. **AI News Summarizer (`POST /api/bulletin/summarize` — `summarize_news_endpoint`):** Menghasilkan ringkasan eksekutif terstruktur (*Inti Berita* dan *Poin Penting & Insight*) dengan fallback heuristik bila LLM offline.

---

*Akhir dari Ancestor Codex Volume III — Tools, Modules & Capabilities Registry.*
