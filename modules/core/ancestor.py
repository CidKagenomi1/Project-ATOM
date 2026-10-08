"""
ANCESTOR GROUNDING & KNOWLEDGE ENGINE (A.T.O.M. v4.0)
Initiated by: Alif Rahmadi

Provides Dual-Mode Knowledge Retrieval:
1. Ancestor Echo (Deterministic Zero-LLM): Instant 0-token response for exact / quick prompts.
2. Ancestor Synthesis (LangChain Grounded): Sectional retrieval from 7 encyclopedic volumes.
"""

from __future__ import annotations

import os
import re
import time
from typing import Dict, List, Optional, Tuple

ANCESTOR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "ancestor")
MASTER_KNOWLEDGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "master_knowledge.md")

# --- 1. DETERMINISTIC QUICK ACTION TEMPLATES (ANCESTOR ECHO - ZERO-LLM) ---
ECHO_TEMPLATES = {
    "identity": """### ⚡ Halo, Saya A.T.O.M. (Autonomous Task Orchestration Machine) v4.0

Saya bukan sekadar chatbot biasa, Sir. Saya adalah **Neural AI Orchestrator** dan kokpit kecerdasan buatan taktis yang dirancang untuk menjadi mitra berpikir Anda dalam mengeksplorasi ide, merancang sistem, dan mengakselerasi produktivitas.

#### Kapabilitas Inti Saya:
1. **Cortex Neural Routing:** Menghubungkan Anda ke jaringan multi-provider awan tercepat (Groq LPU, DeepSeek, OpenRouter, dan Gemini) dengan proteksi pemulihan otomatis (*failover*) jika terjadi gangguan jaringan.
2. **Autonomous Research Squad:** Mengerahkan tim agen otonom CrewAI untuk melakukan investigasi dan riset topik kompleks secara mendalam.
3. **Ideation & Roleplay Sandbox:** Mensimulasikan diskusi strategis bersama berbagai persona ahli (Co-Founder, Tech Architect, Operations Director, hingga Shark Investor).
4. **Magic Notes & Concept Bubbles:** Menangkap kilatan ide singkat dan mengembangkannya menjadi artikel terstruktur bergaya Zettelkasten & NotebookLM.

*Sistem aktif, latensi optimal. Apa misi atau ide yang ingin kita bedah hari ini, Sir?*""",

    "creator": """### 👤 Inisiator & Pengembang Sistem

Sistem **A.T.O.M.** diciptakan dan diinisiasi secara independen oleh **Alif Rahmadi**.

#### Latar Belakang & Visi Proyek:
* **Personal Flagship Project:** A.T.O.M. lahir dari visi Alif Rahmadi untuk membangun sebuah orkestrator kecerdasan buatan mandiri yang melampaui batasan chatbot statis komersial.
* **Filosofi Arsitektur:** Alif merancang sistem ini dengan prinsip *resilience & freedom*—memadukan kekuatan inferensi komputasi awan mutakhir (LPU Groq, DeepSeek Reasoning, katalog OpenRouter, dan Google Gemini) dalam balutan antarmuka Cyber Glassmorphism bertema Nuclear Gold.
* **Peran Sistem:** Sebagai kokpit personal untuk stimulasi ide, perancangan arsitektur teknologi, analisis kritis ide bisnis, serta akselerasi inovasi tanpa terhambat oleh batasan komputasi lokal.

Seluruh cetak biru arsitektur, integrasi modul Cortex, Librarian, Sentinel, hingga basis pengetahuan **Ancestor** ini dirancang atas arahan beliau.""",

    "cortex": """### 🧠 Mekanisme Kerja Cortex Neural Router v4.0

**Cortex** adalah otak pengatur lalu lintas AI otonom di dalam sistem A.T.O.M. yang bekerja dengan mekanisme **Multi-Tier Dispatcher & Self-Healing Failover**:

#### 1. Analisis Kueri Otomatis
Setiap kali Anda mengirim pesan, Cortex menganalisis kebutuhan instruksi:
* Apakah membutuhkan inferensi kilat (dialog cepat)?
* Apakah membutuhkan penalaran mendalam atau audit kode?
* Apakah instruksi menyertakan gambar/dokumen visual?

#### 2. Matriks Perutean Multi-Tier:
* **Tier 1 (LPU Instant Speed) — Groq:** Menggunakan model bertenaga LPU (`gpt-oss-120b` / `qwen3.8-27b`) dengan kecepatan mencapai ~500 token/detik untuk percakapan instan.
* **Tier 2 (Deep Analytical Reasoning) — DeepSeek Cloud:** Dikerahkan saat penalaran logis tingkat tinggi dan pemecahan masalah kompleks diperlukan.
* **Tier 3 (Open Model Hub) — OpenRouter:** Memberikan akses ke katalog model global (`Nemotron`, `Gemma 4`, `Qwen Coder`) saat provider utama sibuk.
* **Tier 4 (Cloud Resilience & Multimodal Anchor) — Google Gemini:** Jaring pengaman utama dengan jendela konteks raksasa dan pemroses visual.

#### 3. Self-Healing Failover (Anti-Crash)
Jika provider di Tier 1 mengalami gangguan (seperti batas kuota harian `429` atau timeout jaringan), Cortex **secara otomatis mengalihkan permintaan ke tier berikutnya dalam hitungan milidetik** tanpa memutuskan percakapan Anda dan tanpa menampilkan error 500.""",

    "crewai": """### 👥 Skuad Riset Otonom: CrewAI Multi-Agent di A.T.O.M.

**CrewAI** di A.T.O.M. adalah modul orkestrator multi-agen otonom yang bertindak sebagai **"Autonomous Research Squad"** untuk investigasi dan riset mendalam.

#### Cara Kerja Kolaborasi Agen:
Alih-alih mengandalkan satu model untuk berpikir sekaligus menulis, CrewAI membagi pekerjaan ke dua agen independen yang bekerja secara berantai (*Sequential Workflow*):

1. **Senior Researcher:**
   * Agen analis senior yang bertugas mengumpulkan data kunci, memvalidasi fakta teknologi, memetakan tantangan, dan menemukan wawasan mendalam seputar topik yang diminta.
2. **Content Writer:**
   * Agen penulis spesialis yang mengambil seluruh hasil temuan Senior Researcher, lalu menyusunnya menjadi laporan riset komprehensif berformat Markdown rapi dalam Bahasa Indonesia lengkap dengan judul menarik, sub-topik, dan rekomendasi praktis.

#### Kapan CrewAI Aktif?
CrewAI dipicu secara otomatis oleh Cortex ketika instruksi Anda diawali dengan kata kunci riset mendalam seperti: `riset mendalam: [topik]`, `investigasi: [topik]`, atau `analisis komprehensif: [topik]`.""",

    "architecture": """### 🏛️ Blueprint Arsitektur Sistem A.T.O.M. v4.0

A.T.O.M. dibangun dengan arsitektur modular berlapis yang efisien dan tangguh:

```
┌────────────────────────────────────────────────────────┐
│               FRONTEND COCKPIT (Vanilla ES6)           │
│  Cyber Glassmorphism · Nuclear Gold · Vapor Chamber   │
│  [Neural Chat] [Roleplay Sandbox] [Magic Notes] [Bubbles]│
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / JSON API
┌───────────────────────────▼────────────────────────────┐
│               BACKEND GATEWAY (FastAPI / Vercel)       │
│  /api/chat       /api/notes_ai      /api/bubbles       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    THE NEURAL CORE                     │
│  • Cortex Router   : Dispatcher & Multi-Tier Failover │
│  • Librarian       : Sliding Token Window Memory       │
│  • Sentinel        : Real-time Latency & Telemetry Log │
│  • Ancestor        : Dual-Mode Local Knowledge Engine  │
│  • CrewAI Squad    : Multi-Agent Research System       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│               MULTI-CLOUD INFERENCE NETWORK            │
│  Groq (LPU) · DeepSeek · OpenRouter · Google Gemini   │
└────────────────────────────────────────────────────────┘
```

#### Keunggulan Utama Arsitektur Ini:
1. **Zero UI Overhead:** Frontend dibangun murni tanpa framework berat untuk memastikan rendering kilat di semua peramban.
2. **Dual-Environment Ready:** Berjalan mulus di `dev_server.py` lokal (port 8000) maupun di serverless cloud Vercel.
3. **Resilience Layer:** Dilengkapi proteksi penyimpanan aman ke `/tmp` jika disk bersifat *read-only*, serta sistem failover mandiri di setiap titik integrasi."""
}


class AncestorEngine:
    """The central manager for Ancestor knowledge storage, Echo routing, and Synthesis."""

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._load_volumes()

    def _load_volumes(self):
        """Pre-cache all volumes into memory for ultra-fast sectional retrieval."""
        if os.path.exists(ANCESTOR_DIR):
            for fname in os.listdir(ANCESTOR_DIR):
                if fname.endswith(".md"):
                    path = os.path.join(ANCESTOR_DIR, fname)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            self._cache[fname] = f.read()
                    except Exception:
                        pass
        if os.path.exists(MASTER_KNOWLEDGE_PATH):
            try:
                with open(MASTER_KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                    self._cache["master_knowledge.md"] = f.read()
            except Exception:
                pass

    def match_echo(self, prompt: str) -> Optional[Dict]:
        """
        Check if prompt matches a deterministic Quick Action pattern.
        Returns a complete ChatResponse dict if matched, else None.
        """
        p = prompt.strip().lower()

        # 1. Identity match
        if any(kw in p for kw in [
            "siapa dirimu", "apa peran utamamu", "siapa anda", "identitas atom", 
            "siapa kamu di atom", "peran utamamu di a.t.o.m."
        ]):
            return {
                "response": ECHO_TEMPLATES["identity"],
                "model": "Ancestor-Echo (Zero-LLM)",
                "thinking": [
                    {"step": "[ANCESTOR]", "detail": "Instant Identity Echo (0ms / 0 Token)"},
                    {"step": "[STATUS]", "detail": "Grounded from Ancestor Core"}
                ],
                "duration": 0.001
            }

        # 2. Creator match
        if any(kw in p for kw in [
            "siapa pembuatmu", "siapa inisiator", "pembuat atau inisiator", 
            "siapa pencipta", "siapa yang membuat atom", "alif rahmadi"
        ]) and len(p.split()) < 20:
            return {
                "response": ECHO_TEMPLATES["creator"],
                "model": "Ancestor-Echo (Zero-LLM)",
                "thinking": [
                    {"step": "[ANCESTOR]", "detail": "Instant Creator Lore Echo (0ms / 0 Token)"},
                    {"step": "[FOUNDER]", "detail": "Alif Rahmadi Otoritatif"}
                ],
                "duration": 0.001
            }

        # 3. Cortex match
        if any(kw in p for kw in [
            "cara kerja cortex", "cortex neural router", "bagaimana cara kerja cortex",
            "mekanisme cortex", "failover multi-provider"
        ]):
            return {
                "response": ECHO_TEMPLATES["cortex"],
                "model": "Ancestor-Echo (Zero-LLM)",
                "thinking": [
                    {"step": "[ANCESTOR]", "detail": "Instant Cortex Architecture Echo (0ms / 0 Token)"},
                    {"step": "[ROUTER]", "detail": "Multi-Tier Dispatcher Verified"}
                ],
                "duration": 0.001
            }

        # 4. CrewAI match
        if any(kw in p for kw in [
            "apa itu crewai", "peran multi-agent squad", "modul crewai", 
            "bagaimana peran multi-agent", "crewai di atom"
        ]):
            return {
                "response": ECHO_TEMPLATES["crewai"],
                "model": "Ancestor-Echo (Zero-LLM)",
                "thinking": [
                    {"step": "[ANCESTOR]", "detail": "Instant CrewAI Squad Echo (0ms / 0 Token)"},
                    {"step": "[SQUAD]", "detail": "Researcher + Writer Workflow Verified"}
                ],
                "duration": 0.001
            }

        # 5. Architecture match
        if any(kw in p for kw in [
            "arsitektur sistem a.t.o.m.", "arsitektur sistem atom", 
            "arsitektur atom secara keseluruhan", "frontend hingga backend",
            "blueprint arsitektur sistem"
        ]):
            return {
                "response": ECHO_TEMPLATES["architecture"],
                "model": "Ancestor-Echo (Zero-LLM)",
                "thinking": [
                    {"step": "[ANCESTOR]", "detail": "Instant Blueprint Architecture Echo (0ms / 0 Token)"},
                    {"step": "[TOPOLOGY]", "detail": "Full-Stack Topology Verified"}
                ],
                "duration": 0.001
            }

        # --- 6. CASUAL BANTER MATRIX (10 INTENT CLUSTERS & RANDOMIZED WITTY POOL) ---
        try:
            from modules.core.banter_matrix import get_banter_engine
            banter_resp = get_banter_engine().match(prompt)
            if banter_resp:
                return banter_resp
        except Exception:
            pass

        return None

    def get_relevant_context(self, prompt: str) -> str:
        """Select relevant volume sections based on prompt keywords to feed LangChain."""
        p = prompt.lower()
        selected_docs = []

        if any(k in p for k in ["alif", "sejarah", "filosofi", "manifesto", "visi", "tujuan", "founder"]):
            if "vol1_origin_manifesto.md" in self._cache:
                selected_docs.append(self._cache["vol1_origin_manifesto.md"])

        if any(k in p for k in ["cortex", "failover", "librarian", "sentinel", "telemetri", "token", "circuit breaker"]):
            if "vol2_neural_core_deepdive.md" in self._cache:
                selected_docs.append(self._cache["vol2_neural_core_deepdive.md"])

        if any(k in p for k in ["roleplay", "persona", "co_founder", "investor", "shark", "tech lead", "operations"]):
            if "vol3_roleplay_personas.md" in self._cache:
                selected_docs.append(self._cache["vol3_roleplay_personas.md"])

        if any(k in p for k in ["notes", "zettelkasten", "bubble", "notebooklm", "catatan", "pydantic"]):
            if "vol4_ideation_lab_notes.md" in self._cache:
                selected_docs.append(self._cache["vol4_ideation_lab_notes.md"])

        if any(k in p for k in ["security", "keamanan", "privasi", "prompt injection", "xss", "hardening", "purge"]):
            if "vol5_security_privacy_hardening.md" in self._cache:
                selected_docs.append(self._cache["vol5_security_privacy_hardening.md"])

        if any(k in p for k in ["vercel", "serverless", "deploy", "runbook", "env", "troubleshooting", "error 500"]):
            if "vol6_infrastructure_runbook.md" in self._cache:
                selected_docs.append(self._cache["vol6_infrastructure_runbook.md"])

        if any(k in p for k in ["perbandingan", "tanya jawab", "benchmark", "autogen", "react", "darurat"]):
            if "vol7_tactical_qa_registry.md" in self._cache:
                selected_docs.append(self._cache["vol7_tactical_qa_registry.md"])

        # Default fallback to master_knowledge if none specifically matched
        if not selected_docs:
            if "master_knowledge.md" in self._cache:
                selected_docs.append(self._cache["master_knowledge.md"][:8000])

        combined = "\n\n---\n\n".join(selected_docs)
        # Limit to safe token window (~12000 chars)
        return combined[:14000]


# Global Singleton Instance
_ancestor_instance = None

def get_ancestor() -> AncestorEngine:
    global _ancestor_instance
    if _ancestor_instance is None:
        _ancestor_instance = AncestorEngine()
    return _ancestor_instance
