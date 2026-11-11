"""
A.T.O.M. - Notes AI API Endpoint (Vercel Serverless)
POST /api/notes_ai
Body: { "action": "refine"|"autotag"|"chat"|"title"|"metadata", "content": str, "question": str }
Response: { "result": str|list|dict }
"""

import os
import json
from http.server import BaseHTTPRequestHandler
from pydantic import BaseModel, Field
from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Try Groq first (primary for notes AI)
try:
    from langchain_groq import ChatGroq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# Gemini fallback
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from langchain_core.messages import HumanMessage, SystemMessage


class NoteMetadata(BaseModel):
    title: str = Field(description="Short, descriptive title of the note content, max 6 words")
    tags: List[str] = Field(description="3 to 5 lowercase keywords/tags related to the content, max 2 words per tag")
    summary: str = Field(description="One-sentence executive summary of the note content in Indonesian")


def get_llm(temperature: float = 0.3):
    """Get best available LLM."""
    if HAS_GROQ and os.environ.get("GROQ_API_KEY"):
        groq_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
        try:
            return ChatGroq(
                model=groq_model,
                api_key=os.environ.get("GROQ_API_KEY"),
                temperature=temperature
            )
        except Exception:
            pass
    if HAS_GEMINI and os.environ.get("GOOGLE_API_KEY"):
        gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        try:
            return ChatGoogleGenerativeAI(
                model=gemini_model,
                google_api_key=os.environ.get("GOOGLE_API_KEY"),
                temperature=temperature
            )
        except Exception:
            pass
    return None


def invoke_llm_safely(prompt_or_messages, temperature: float = 0.3):
    """Invoke LLM with multi-tier failover (Groq -> Gemini)."""
    # 1. Try Groq
    if HAS_GROQ and os.environ.get("GROQ_API_KEY"):
        groq_models = [os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"), "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
        for m in groq_models:
            try:
                llm = ChatGroq(model=m, api_key=os.environ.get("GROQ_API_KEY"), temperature=temperature)
                return llm.invoke(prompt_or_messages)
            except Exception as e:
                print(f"[NOTES AI GROQ FAIL] {m}: {e}")
                continue

    # 2. Try Gemini fallback
    if HAS_GEMINI and os.environ.get("GOOGLE_API_KEY"):
        try:
            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            llm = ChatGoogleGenerativeAI(
                model=gemini_model,
                google_api_key=os.environ.get("GOOGLE_API_KEY"),
                temperature=temperature
            )
            return llm.invoke(prompt_or_messages)
        except Exception as e:
            print(f"[NOTES AI GEMINI FAIL] {e}")

    raise RuntimeError("Tidak ada AI provider yang aktif atau kuota habis.")


def refine_text(raw_text: str, style: str = "structured") -> str:
    """Clean up messy text into structured markdown article with multiple style presets."""
    style_prompts = {
        "structured": """Kamu adalah Editor Artikel Profesional A.T.O.M.
Tugasmu: terima teks mentah → susun ulang menjadi Artikel Markdown terstruktur dan rapi.
ATURAN:
1. Gunakan heading hierarkis (##, ###) yang jelas
2. Gunakan bullet points atau penomoran untuk daftar fakta/poin
3. Perbaiki typo, ejaan, dan tata bahasa (Bahasa Indonesia yang baik dan natural)
4. Pertahankan semua informasi penting, istilah teknis, dan konteks asli
5. Buat paragraf yang mengalir rapi dan nyaman dibaca
6. Jangan menambahkan informasi spekulatif yang tidak ada di teks mentah""",

        "minutes": """Kamu adalah Notulis Profesional Rapat & Proyek A.T.O.M.
Tugasmu: ubah teks mentah/catatan bebas menjadi Format Notulensi & Action Items Profesional.
STRUKTUR WAJIB:
- ## 📌 Ringkasan Eksekutif (1-2 paragraf singkat)
- ## 🗣️ Poin-Poin Pembahasan Utama (bullet points dengan bold keyword)
- ## ✅ Action Items & To-Do (gunakan checklist markdown: `- [ ] Tugas (PIC / Catatan)`)
- ## ⚖️ Keputusan yang Disepakati
ATURAN:
1. Ekstrak tindakan atau tugas yang harus dikerjakan ke dalam checklist
2. Jangan hapus nama orang, tanggal, atau target waktu jika ada
3. Buat pembaca bisa langsung paham langkah selanjutnya dalam 30 detik""",

        "summary": """Kamu adalah Eksekutif Ringkasan Cepat A.T.O.M.
Tugasmu: buat ringkasan super padat, tajam, dan langsung ke inti (TL;DR).
STRUKTUR:
- ## ⚡ Executive Summary (Maksimal 3-4 kalimat padat)
- ## 🎯 5 Poin Inti Terpenting (Bullet points ringkas & to-the-point)
- ## 💡 Key Takeaway (1 kalimat pesan utama)
ATURAN:
1. Hindari basa-basi atau kata pengantar klise
2. Fokus pada substansi terpenting""",

        "grammar": """Kamu adalah Proofreader dan Editor Presisi A.T.O.M.
Tugasmu: merapikan kesalahan bahasa, tanda baca, dan format markdown TANPA merombak susunan kalimat asli.
ATURAN:
1. Pertahankan urutan dan struktur kalimat penulis asli sedekat mungkin
2. Perbaiki kesalahan ketik (typo), tanda baca, huruf kapital, dan format markdown
3. Rapikan spasi ganda, baris baru yang rusak, atau list yang tidak sejajar
4. Jangan menghapus atau menulis ulang dengan kata-kata berbeda kecuali memang salah fatal"""
    }

    selected_prompt = style_prompts.get(style, style_prompts["structured"])
    system = SystemMessage(content=selected_prompt)
    user = HumanMessage(content=f"TEKS MENTAH:\n---\n{raw_text[:6000]}\n---\nRapihkan menjadi artikel Markdown sesuai instruksi di atas:")
    
    try:
        response = invoke_llm_safely([system, user], 0.3)
        return response.content
    except Exception as e:
        return f"[ERROR] Gagal merapihkan: {str(e)}"


def process_micro_ai(snippet: str, micro_type: str = "refine") -> str:
    """Process focused micro AI actions on selected text snippet."""
    micro_prompts = {
        "refine": """Kamu adalah Micro-Editor A.T.O.M.
Tugasmu: rapikan dan poles potongan teks yang dipilih pengguna.
ATURAN:
1. Perbaiki typo, tata bahasa, dan tanda baca
2. Buat kalimat lebih mengalir, jelas, dan profesional
3. Pertahankan arti asli dan jangan buat terlalu panjang
4. Langsung berikan teks hasil perbaikan saja tanpa kata pengantar atau tanda kutip pembuka/penutup""",

        "summarize": """Kamu adalah Micro-Summarizer A.T.O.M.
Tugasmu: ringkas potongan teks terpilih menjadi 1-2 bullet point atau 1 kalimat super padat.
ATURAN:
1. Tangkap esensi terpenting saja
2. Gunakan Bahasa Indonesia yang ringkas dan lugas
3. Langsung berikan hasil ringkasan tanpa basa-basi""",

        "explain": """Kamu adalah Micro-Explainer A.T.O.M.
Tugasmu: jelaskan konsep, istilah, atau kalimat berikut secara singkat dan mudah dimengerti.
ATURAN:
1. Berikan penjelasan ringkas maksimal 2-3 kalimat
2. Jelaskan artinya secara esensial dan kontekstual
3. Gunakan Bahasa Indonesia yang ramah dan jelas
4. Langsung berikan penjelasan tanpa basa-basi""",

        "translate": """Kamu adalah Penerjemah Dwibahasa Presisi A.T.O.M.
Tugasmu: jika teks sumber adalah Bahasa Indonesia, terjemahkan ke Bahasa Inggris yang natural. Jika teks sumber Bahasa Inggris atau bahasa asing lain, terjemahkan ke Bahasa Indonesia yang baik dan benar.
ATURAN:
1. Terjemahan harus akurat, natural, dan kontekstual
2. Langsung berikan hasil terjemahan saja tanpa teks pengantar""",

        "todo": """Kamu adalah Action-Item Extractor A.T.O.M.
Tugasmu: ubah potongan teks berikut menjadi daftar checklist to-do Markdown (`- [ ]`).
ATURAN:
1. Buat butir checklist tindakan yang jelas, diawali kata kerja aksi
2. Format: `- [ ] Tindakan spesifik`
3. Langsung berikan daftar checklist tanpa basa-basi"""
    }

    selected_prompt = micro_prompts.get(micro_type, micro_prompts["refine"])
    system = SystemMessage(content=selected_prompt)
    user = HumanMessage(content=f"POTONGAN TEKS TERPILIH:\n---\n{snippet[:2500]}\n---\nHASIL:")

    try:
        response = invoke_llm_safely([system, user], 0.2)
        content = response.content.strip()
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1].strip()
        return content
    except Exception as e:
        return f"[ERROR] Gagal memproses micro AI: {str(e)}"


def auto_tag(text: str) -> list:
    """Generate 3-5 relevant tags from text."""
    prompt = f"""Analyze this text and generate 3-5 relevant tags/keywords.
TEXT: {text[:2000]}
RULES:
- Tags should be single words or short phrases (max 2 words)
- Use lowercase
- Return ONLY the tags, one per line, no numbering
TAGS:"""
    
    try:
        response = invoke_llm_safely(prompt, 0.1)
        tags = []
        for line in response.content.strip().split('\n'):
            tag = line.strip().strip('-').strip('•').strip()
            if tag and len(tag) < 30:
                tags.append(tag.lower())
        return tags[:5]
    except Exception as e:
        print(f"[AUTOTAG ERROR] {e}")
        return []


def chat_with_context(context_text: str, question: str) -> str:
    """Answer question based on provided note contents (NotebookLM Multi-Note style)."""
    system = SystemMessage(content="""Kamu adalah ATOM Knowledge Assistant (Multi-Note Intelligence Co-Pilot).
TUGAS & ATURAN PENTING:
1. Jawab pertanyaan HANYA berdasarkan KUMPULAN DOKUMEN / SUMBER CATATAN yang disertakan dalam konteks.
2. CITATION / RUJUKAN SUMBER (WAJIB):
   - Setiap kali Anda mengutip fakta, data, atau informasi dari dokumen tertentu, sertakan rujukan dokumen di akhir kalimat/poin dengan format: `[Sumber: Judul Dokumen]`.
   - Jika pengguna meminta perbandingan atau sintesis dari beberapa dokumen, bandingkan secara eksplisit poin-poin persamaan dan perbedaannya.
3. KETIADAAN INFORMASI:
   - Jika jawaban tidak ditemukan sama sekali di kumpulan catatan yang disertakan, katakan terus terang: "Informasi tersebut tidak ditemukan dalam kumpulan catatan sumber yang dipilih."
4. TATA BAHASA & STRUKTUR:
   - Gunakan Bahasa Indonesia yang profesional, ramah, dan terstruktur rapi (gunakan bolding dan bullet points jika menjabarkan).
   - Buat jawaban padat dan berbobot tanpa basa-basi berlebihan.""")

    user = HumanMessage(content=f"""KUMPULAN CATATAN SUMBER KNOWLEDGE BASE:
---
{context_text[:12000]}
---
PERTANYAAN PENGGUNA:
{question}

Berikan jawaban terstruktur dan sertakan rujukan sumber dokumen:""")
    
    try:
        response = invoke_llm_safely([system, user], 0.2)
        return response.content
    except Exception as e:
        return f"[ERROR] Gagal memproses: {str(e)}"


def generate_title(content: str) -> str:
    """Generate concise title for note content."""
    prompt = f"""Generate a short, descriptive title (max 6 words) for this content:
{content[:500]}
Return ONLY the title, no quotes or extra formatting.
Use Indonesian if content is in Indonesian.
TITLE:"""
    
    try:
        response = invoke_llm_safely(prompt, 0.2)
        title = response.content.strip().strip('"').strip("'")
        return title[:60] if title else "Untitled Note"
    except:
        return "Untitled Note"


def generate_metadata_pydantic(content: str) -> dict:
    """Generate structured title, tags, and summary using Pydantic AI with graceful fallback."""
    try:
        from pydantic_ai import Agent
        
        groq_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
        if os.environ.get("GROQ_API_KEY"):
            os.environ["GROQ_API_KEY"] = os.environ.get("GROQ_API_KEY")
            agent = Agent(f'groq:{groq_model}', result_type=NoteMetadata)
        elif os.environ.get("GOOGLE_API_KEY"):
            os.environ["GEMINI_API_KEY"] = os.environ.get("GOOGLE_API_KEY")
            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            agent = Agent(gemini_model, result_type=NoteMetadata)
        else:
            raise ValueError("No API key configured for metadata generation")

            
        result = agent.run_sync(f"Ekstrak metadata untuk konten berikut:\n\n{content[:4000]}")
        return {
            "title": result.data.title,
            "tags": result.data.tags,
            "summary": result.data.summary
        }
    except Exception as e:
        print(f"[PYDANTIC AI FALLBACK] Using standard backup due to error: {e}")
        # Fallback to existing working LangChain functions
        return {
            "title": generate_title(content),
            "tags": auto_tag(content),
            "summary": "Metadata hasil ekstraksi cepat (Pydantic AI fallback)."
        }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
        except Exception as e:
            self._send_json({"error": f"Invalid body: {e}"}, 400)
            return

        action = data.get("action", "")
        content = data.get("content", "")
        question = data.get("question", "")

        if not action:
            self._send_json({"error": "action is required"}, 400)
            return

        result = None

        if action == "refine":
            if not content:
                self._send_json({"error": "content is required for refine"}, 400)
                return
            style = data.get("style", "structured")
            result = refine_text(content, style=style)

        elif action == "micro":
            if not content:
                self._send_json({"error": "content is required for micro AI"}, 400)
                return
            micro_type = data.get("micro_type", "refine")
            result = process_micro_ai(content, micro_type=micro_type)

        elif action == "autotag":
            if not content:
                self._send_json({"error": "content is required for autotag"}, 400)
                return
            result = auto_tag(content)

        elif action == "chat":
            if not content or not question:
                self._send_json({"error": "content and question are required for chat"}, 400)
                return
            result = chat_with_context(content, question)

        elif action == "title":
            if not content:
                self._send_json({"error": "content is required for title"}, 400)
                return
            result = generate_title(content)

        elif action == "metadata":
            if not content:
                self._send_json({"error": "content is required for metadata"}, 400)
                return
            result = generate_metadata_pydantic(content)

        else:
            self._send_json({"error": f"Unknown action: {action}"}, 400)
            return

        self._send_json({"result": result})

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
