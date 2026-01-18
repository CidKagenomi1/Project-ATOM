# A.T.O.M (Autonomous Task Orchestration Machine) v3.1

> *"I am not just a chatbot, Sir. I am a Neural Orchestrator."*

**A.T.O.M** is a sophisticated **Multi-Agent System** powered by a central **Cortex**. It doesn't just answer; it *thinks*, *decides*, and *delegates*.

![ATOM Interface](https://via.placeholder.com/800x400/000000/FFFFFF?text=A.T.O.M+CORTEX+INTERFACE)

---

## 🇺🇸 English Documentation

### 🧠 The CORTEX Architecture

At the core of A.T.O.M is **`modules/cortex.py`**, an intelligent orchestrator that manages critical subsystems:

1.  **🔀 Neural Router**: Instantly analyzes your prompt and decides the best route:
    *   **☁️ CLOUD (Gemini Flash)**: For coding, math, and fast factual queries.
    *   **🏠 LOCAL (Llama 3.2)**: For casual chat, privacy-focused tasks, and offline usage.
    *   **🚀 CREW (CrewAI)**: For deep research, generating comprehensive reports, and multi-step reasoning.
2.  **� Smart Notes**: A dedicated brain for knowledge management managed by `modules/note_brain.py`.
3.  **👁️ Sentinel**: Tracks every interaction for the Telemetry Dashboard.
4.  **🧠 Transparent Thinking**: Exposes the internal logic steps (Routing -> Context -> Execution) directly in the UI.

### ⚡ Key Features

*   **Hybrid Intelligence**: Seamlessly blends Cloud AI, Local AI, and Agent Swarms.
*   **Smart Notes System**: 
    *   Create and manage markdown notes with auto-tagging.
    *   **Chat with Notes**: Ask questions specifically about your stored notes context.
    *   **Magic Formatter**: Use AI to refine and format raw text into structured articles.
*   **Telemetry Dashboard**: Monitor usage stats, response times, and model distribution.
*   **Self-Correction**: Robust error handling and graceful fallbacks.

### 🛠️ Technology Stack

*   **Frontend**: Streamlit
*   **Orchestration**: Python (Custom Cortex Class)
*   **LLM Framework**: LangChain
*   **Models**: Gemini 2.0 (Cloud), Llama 3.2 (Local via Ollama)

### 🚀 Usage

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the Interface**:
    ```bash
    streamlit run ATOM_Chat.py
    ```
3.  **Navigate**:
    *   **Chat**: Main interface for interaction.
    *   **Notes**: Manage and chat with your knowledge base.
    *   **Telemetry**: View system performance.

### 📂 Project Structure

```
PROJECT ATOM/
├── ATOM_Chat.py        # 🚀 ENTRY POINT: Main Chat Interface
├── modules/
│   ├── cortex.py       # 🧠 THE BRAIN: Neural Router & Orchestrator
│   ├── note_brain.py   # 📝 NOTE AI: Logic for Smart Notes & Magic Formatter
│   └── note_storage.py # 💾 DATABASE: JSON storage for notes
├── pages/
│   ├── notes.py        # 📝 UI: Notes Management Page
│   └── telemetry.py    # 📊 UI: Analytics Dashboard
└── ...
```

---

## 🇮🇩 Dokumentasi Bahasa Indonesia

### 🧠 Arsitektur CORTEX

Inti dari A.T.O.M adalah **`modules/cortex.py`**, orchestrator cerdas yang mengelola subsistem kritis:

1.  **🔀 Neural Router**: Menganalisis prompt Anda secara instan dan menentukan rute terbaik:
    *   **☁️ CLOUD (Gemini Flash)**: Untuk coding, matematika, dan pertanyaan faktual cepat.
    *   **🏠 LOCAL (Llama 3.2)**: Untuk obrolan santai, tugas privasi, dan penggunaan offline.
    *   **🚀 CREW (CrewAI)**: Untuk riset mendalam dan penalaran multi-langkah.
2.  **📝 Smart Notes**: Otak khusus untuk manajemen pengetahuan yang dikelola oleh `modules/note_brain.py`.
3.  **👁️ Sentinel**: Melacak setiap interaksi untuk Dashboard Telemetri.

### ⚡ Fitur Utama

*   **Kecerdasan Hibrida**: Menggabungkan AI Cloud, AI Lokal, dan Agent Swarms.
*   **Sistem Smart Notes**:
    *   Buat dan kelola catatan markdown dengan auto-tagging.
    *   **Chat with Notes**: Tanya jawab khusus berdasarkan konteks catatan Anda.
    *   **Magic Formatter**: Gunakan AI untuk merapikan teks mentah menjadi artikel terstruktur.
*   **Dashboard Telemetri**: Pantau statistik penggunaan dan distribusi model.

### 🚀 Cara Penggunaan

1.  **Instal Dependensi**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Jalankan Interface**:
    ```bash
    streamlit run ATOM_Chat.py
    ```

### 📂 Struktur Proyek

```
PROJECT ATOM/
├── ATOM_Chat.py        # 🚀 ENTRY POINT: Antarmuka Chat Utama
├── modules/
│   ├── cortex.py       # 🧠 THE BRAIN: Router & Orchestrator
│   ├── note_brain.py   # � NOTE AI: Logika untuk Smart Notes
│   └── note_storage.py # 💾 DATABASE: Penyimpanan JSON untuk catatan
├── pages/
│   ├── notes.py        # � UI: Halaman Manajemen Catatan
│   └── telemetry.py    # 📊 UI: Dashboard Analitik
└── ...
```
