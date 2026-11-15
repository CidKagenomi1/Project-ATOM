"""
A.T.O.M. - Notes AI API Endpoint (Vercel Serverless)
POST /api/notes_ai
Body: { "action": "refine"|"autotag"|"chat"|"title"|"metadata", "content": str, "question": str }
Response: { "result": str|list|dict }
"""

import os
import re
import json
import ssl
import urllib.request
from http.server import BaseHTTPRequestHandler
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass


# Try Groq first (primary for notes AI)
try:
    from langchain_groq import ChatGroq
    HAS_GROQ = True
except ImportError:
    ChatGroq = None
    HAS_GROQ = False

# Gemini fallback
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GEMINI = True
except ImportError:
    ChatGoogleGenerativeAI = None
    HAS_GEMINI = False

try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    HAS_LC_MESSAGES = True
except ImportError:
    HAS_LC_MESSAGES = False

    class _BaseMessage:
        def __init__(self, content: str = ""):
            self.content = content

    class SystemMessage(_BaseMessage):
        pass

    class HumanMessage(_BaseMessage):
        pass

    class AIMessage(_BaseMessage):
        pass


class SimpleLLMResponse:
    """Lightweight LLM response container compatible with LangChain's .content attribute."""
    def __init__(self, content: str, model: str = "unknown"):
        self.content = content
        self.model = model


_FALLBACK_THINK_REGEX = re.compile(
    r"<(think|thought|thinking)>(.*?)(?:</\1>|$)",
    re.DOTALL | re.IGNORECASE
)


def _clean_llm_text(raw_content: Any, extra_reasoning: Optional[str] = None) -> str:
    """Extract plain text and strip internal <think> reasoning tags."""
    if isinstance(raw_content, list):
        parts = []
        for item in raw_content:
            if isinstance(item, dict):
                if item.get("text"):
                    parts.append(str(item["text"]))
            elif item is not None:
                parts.append(str(item))
        text = "\n".join(parts)
    else:
        text = str(raw_content or "")

    try:
        from modules.core.reasoning_parser import extract_reasoning
        clean_resp, _ = extract_reasoning(text, extra_reasoning=extra_reasoning)
        return clean_resp.strip()
    except Exception:
        cleaned = _FALLBACK_THINK_REGEX.sub("", text).strip()
        return cleaned


def _normalize_messages(prompt_or_messages: Any):
    """Convert prompt string or message objects into (lc_messages, role_dicts)."""
    if isinstance(prompt_or_messages, str):
        lc_msgs = [HumanMessage(content=prompt_or_messages)]
        dict_msgs = [{"role": "user", "content": prompt_or_messages}]
        return lc_msgs, dict_msgs

    lc_msgs = []
    dict_msgs = []
    for msg in prompt_or_messages:
        if isinstance(msg, dict):
            role = str(msg.get("role", "user")).lower()
            content = str(msg.get("content", ""))
            dict_msgs.append({"role": role, "content": content})
            if role == "system":
                lc_msgs.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_msgs.append(AIMessage(content=content))
            else:
                lc_msgs.append(HumanMessage(content=content))
        else:
            cls_name = msg.__class__.__name__
            content = str(getattr(msg, "content", msg))
            if cls_name == "SystemMessage":
                role = "system"
            elif cls_name == "AIMessage":
                role = "assistant"
            else:
                role = "user"
            lc_msgs.append(msg)
            dict_msgs.append({"role": role, "content": content})
    return lc_msgs, dict_msgs


def _call_openai_compatible_rest(
    url: str,
    api_key: str,
    model: str,
    dict_messages: List[Dict[str, str]],
    temperature: float = 0.3,
    extra_headers: Optional[Dict[str, str]] = None
) -> str:
    """Zero-dependency OpenAI-compatible chat completions call via urllib."""
    payload = {
        "model": model,
        "messages": dict_messages,
        "temperature": temperature
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "ATOM-NotesAI/4.0"
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        res = json.loads(response.read().decode("utf-8"))
        choice = res.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or msg.get("reasoning")
        return _clean_llm_text(content, extra_reasoning=reasoning)


def _call_gemini_rest(
    api_key: str,
    model: str,
    dict_messages: List[Dict[str, str]],
    temperature: float = 0.3
) -> str:
    """Zero-dependency Google Gemini generateContent REST call via urllib."""
    system_parts = []
    contents = []
    for m in dict_messages:
        role = m.get("role", "user")
        text = m.get("content", "")
        if not text:
            continue
        if role == "system":
            system_parts.append(text)
        else:
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": text}]})

    if not contents:
        contents = [{"role": "user", "parts": [{"text": "\n\n".join(system_parts)}]}]
        system_parts = []

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"temperature": temperature}
    }
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "ATOM-NotesAI/4.0"},
        method="POST"
    )
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        res = json.loads(response.read().decode("utf-8"))
        candidates = res.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: {res}")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        return _clean_llm_text(text)


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
    """Invoke LLM with multi-tier failover (Groq -> OpenRouter -> HuggingFace -> Gemini)."""
    lc_msgs, dict_msgs = _normalize_messages(prompt_or_messages)
    errors = []

    def _dedupe(items: List[str]) -> List[str]:
        seen = set()
        out = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                out.append(item)
        return out

    # 1. Try Groq Cloud (LangChain if available, else REST API)
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        groq_models = _dedupe([
            os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
        ])
        for m in groq_models:
            try:
                if HAS_GROQ and HAS_LC_MESSAGES:
                    llm = ChatGroq(model=m, api_key=groq_key, temperature=temperature)
                    resp = llm.invoke(lc_msgs)
                    extra_r = (
                        getattr(resp, "additional_kwargs", {}).get("reasoning_content") or
                        getattr(resp, "response_metadata", {}).get("reasoning_content")
                    )
                    cleaned = _clean_llm_text(getattr(resp, "content", resp), extra_reasoning=extra_r)
                else:
                    cleaned = _call_openai_compatible_rest(
                        "https://api.groq.com/openai/v1/chat/completions",
                        groq_key,
                        m,
                        dict_msgs,
                        temperature=temperature
                    )
                if cleaned:
                    return SimpleLLMResponse(content=cleaned, model=f"Groq:{m}")
            except Exception as e:
                errors.append(f"Groq({m}): {e}")
                print(f"[NOTES AI GROQ FAIL] {m}: {e}")
                continue

    # 2. Try OpenRouter Cloud
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        raw_or = os.environ.get("OPENROUTER_MODEL", "")
        or_models = [m.strip() for m in raw_or.split(",") if m.strip()]
        or_models.extend([
            "nvidia/nemotron-3-super-120b-a12b:free",
            "google/gemma-4-31b-it:free",
            "liquid/lfm-2.5-2.6b:free",
        ])
        for m in _dedupe(or_models):
            try:
                cleaned = _call_openai_compatible_rest(
                    "https://openrouter.ai/api/v1/chat/completions",
                    openrouter_key,
                    m,
                    dict_msgs,
                    temperature=temperature
                )
                if cleaned:
                    return SimpleLLMResponse(content=cleaned, model=f"OpenRouter:{m}")
            except Exception as e:
                errors.append(f"OpenRouter({m}): {e}")
                print(f"[NOTES AI OPENROUTER FAIL] {m}: {e}")
                continue

    # 3. Try Hugging Face Router
    hf_key = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
    if hf_key:
        raw_hf = os.environ.get("HUGGINGFACE_MODELS") or os.environ.get("HUGGINGFACE_MODEL", "")
        hf_models = [m.strip() for m in raw_hf.split(",") if m.strip()]
        hf_models.extend([
            "deepseek-ai/DeepSeek-V4.1-Flash",
            "meta-llama/Llama-3.1-8B-Instruct",
        ])
        for m in _dedupe(hf_models):
            try:
                cleaned = _call_openai_compatible_rest(
                    "https://router.huggingface.co/v1/chat/completions",
                    hf_key,
                    m,
                    dict_msgs,
                    temperature=temperature
                )
                if cleaned:
                    return SimpleLLMResponse(content=cleaned, model=f"HF:{m}")
            except Exception as e:
                errors.append(f"HF({m}): {e}")
                print(f"[NOTES AI HF FAIL] {m}: {e}")
                continue

    # 4. Try Gemini Fallback (LangChain if available, else REST API)
    google_key = os.environ.get("GOOGLE_API_KEY")
    if google_key:
        gemini_models = _dedupe([
            os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            "gemini-2.5-flash",
            "gemini-2.0-flash",
        ])
        for gm in gemini_models:
            try:
                if HAS_GEMINI and HAS_LC_MESSAGES:
                    llm = ChatGoogleGenerativeAI(
                        model=gm,
                        google_api_key=google_key,
                        temperature=temperature
                    )
                    resp = llm.invoke(lc_msgs)
                    cleaned = _clean_llm_text(getattr(resp, "content", resp))
                else:
                    cleaned = _call_gemini_rest(
                        google_key,
                        gm,
                        dict_msgs,
                        temperature=temperature
                    )
                if cleaned:
                    return SimpleLLMResponse(content=cleaned, model=f"Gemini:{gm}")
            except Exception as e:
                errors.append(f"Gemini({gm}): {e}")
                print(f"[NOTES AI GEMINI FAIL] {gm}: {e}")
                continue

    detail = "; ".join(errors[-2:]) if errors else "API key belum dikonfigurasi."
    raise RuntimeError(f"Tidak ada AI provider yang aktif atau semua provider gagal ({detail}).")


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


def chat_with_context(
    context_text: str,
    question: str,
    history: Optional[List[Dict[str, Any]]] = None,
    web_search: bool = False,
) -> Any:
    """Answer question based on provided note contents with optional live web search grounding."""
    ctx_snippet = (context_text or "").strip() or "(Catatan masih kosong)"

    web_data: Optional[Dict[str, Any]] = None
    web_block = ""
    web_rules = ""
    if web_search:
        try:
            from modules.notes.web_search import search_web_for_notes
            web_data = search_web_for_notes(question, ctx_snippet)
            web_block = f"\n\n{web_data['formatted_context']}"
            web_rules = """
4. INTEGRASI PENCARIAN WEB REAL-TIME:
   - Gabungkan wawasan dari CATATAN SUMBER bersama fakta, konteks terbaru, dan referensi dari HASIL PENCARIAN WEB REAL-TIME di bawah ini.
   - Saat menyebut informasi dari internet, sertakan sitasi `[Web: Nama Sumber]` serta tautan Markdown clickable `[Judul/Sumber](URL)` bila URL tersedia.
   - Susun jawaban dengan sub-heading Markdown yang rapi (## atau ###) dan poin-poin jelas agar mudah langsung disisipkan untuk memperkaya catatan."""
        except Exception as we:
            print(f"[NOTES AI WEB SEARCH WARN] {we}")
            web_data = {"query": question, "sources": [], "formatted_context": ""}

    system = SystemMessage(content=f"""Kamu adalah A.T.O.M. Knowledge Co-Pilot, asisten cerdas di dalam Crew Notes.
TUGAS & ATURAN PENTING:
1. FOKUS PADA DOKUMEN SUMBER:
   - Prioritaskan analisis, fakta, dan wawasan dari KUMPULAN CATATAN SUMBER di bawah ini.
   - Setiap kali mengutip fakta atau data dari catatan tertentu, sertakan rujukan di akhir kalimat/poin dengan format: `[Sumber: Judul Dokumen]`.
   - Jika pengguna meminta perbandingan atau sintesis beberapa catatan, bandingkan persamaan, perbedaan, dan benang merahnya secara eksplisit.
2. DUKUNGAN BRAINSTORMING & EKSPANSI IDE:
   - Jika pengguna meminta untuk brainstorming, membuat kerangka/draft baru, memperdalam konsep, atau catatan sumber masih kosong/singkat, bantu secara proaktif dan konstruktif dengan saran nyata sambil membedakan secara jelas mana yang berasal dari catatan (`[Sumber: ...]`) dan mana yang merupakan saran/elaborasi Co-Pilot.
   - Jika pengguna menanyakan fakta spesifik yang seharusnya ada di catatan namun tidak ditemukan, beritahukan dengan jujur bahwa fakta tersebut tidak ada di catatan terpilih, lalu tawarkan bantuan lanjutan jika relevan.
3. BAHASA & STRUKTUR:
   - Gunakan Bahasa Indonesia yang natural, profesional, solutif, dan terstruktur rapi (heading singkat, bold, atau bullet points bila perlu).
   - Ikuti konteks percakapan sebelumnya jika pengguna mengajukan pertanyaan lanjutan.{web_rules}

KUMPULAN CATATAN SUMBER KNOWLEDGE BASE:
---
{ctx_snippet[:11000]}
---{web_block}""")

    messages: List[Any] = [system]
    if history:
        for msg in history[-8:]:
            if not isinstance(msg, dict):
                continue
            msg_content = str(msg.get("content", "")).strip()
            if not msg_content or msg_content.startswith("[ERROR]"):
                continue
            role = str(msg.get("role", "user")).lower()
            if role == "assistant":
                messages.append(AIMessage(content=msg_content[:4000]))
            else:
                messages.append(HumanMessage(content=msg_content[:4000]))

    messages.append(HumanMessage(content=question))

    try:
        response = invoke_llm_safely(messages, 0.3)
        if web_search:
            return {
                "answer": response.content,
                "web_sources": (web_data or {}).get("sources", []),
                "search_query": (web_data or {}).get("query", question),
            }
        return response.content
    except Exception as e:
        return f"[ERROR] Gagal memproses: {str(e)}"


# ─── Smart Contextual Insertion Helpers ───────────────────
_CHAT_LEADIN_RE = re.compile(
    r"^(tentu|baiklah|baik|siap|oke|berikut(?:\s+adalah)?|berdasarkan\s+(?:catatan|dokumen|pencarian)|"
    r"hasil\s+(?:analisis|pencarian)|ini\s+(?:adalah|rangkuman))\b",
    re.IGNORECASE,
)
_CHAT_SIGNOFF_RE = re.compile(
    r"^(semoga\s+(?:membantu|bermanfaat)|apakah\s+(?:anda|kamu)\s+(?:ingin|mau)|jika\s+(?:anda|kamu)\s+(?:ingin|membutuhkan)|"
    r"silakan\s+(?:beri\s+tahu|tanyakan)|ada\s+lagi\s+yang)\b",
    re.IGNORECASE,
)
_STOPWORDS_ID_EN = {
    "yang", "dan", "atau", "untuk", "dari", "pada", "dalam", "dengan", "akan", "adalah",
    "ini", "itu", "juga", "sebagai", "oleh", "karena", "dapat", "bisa", "agar", "lebih",
    "the", "and", "for", "with", "from", "that", "this", "into", "are", "was", "were",
}


def _clean_copilot_markdown(text: str) -> str:
    """Strip conversational chatbot filler while keeping headings, bullets, tables, and web links."""
    if not text:
        return ""
    lines = text.strip().splitlines()

    # Strip leading short conversational preamble lines
    while lines:
        first = lines[0].strip()
        if not first:
            lines.pop(0)
            continue
        if (
            not first.startswith(("#", "-", "*", ">", "|", "```"))
            and len(first) < 160
            and _CHAT_LEADIN_RE.match(first)
            and first.endswith((":", ".", "!"))
        ):
            lines.pop(0)
            continue
        break

    # Strip trailing conversational sign-off lines
    while lines:
        last = lines[-1].strip()
        if not last:
            lines.pop()
            continue
        if (
            not last.startswith(("#", "-", "*", ">", "|", "```"))
            and len(last) < 180
            and _CHAT_SIGNOFF_RE.match(last)
        ):
            lines.pop()
            continue
        break

    cleaned = "\n".join(lines).strip()
    # Remove redundant internal note citation badges when weaving back into the note itself
    cleaned = re.sub(r"\s*\[Sumber:\s*[^\]]+\]", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned or text.strip()


def _derive_contextual_heading(cleaned_text: str) -> str:
    """Derive a natural contextual sub-heading if text does not already start with a heading."""
    lines = [ln.strip() for ln in (cleaned_text or "").splitlines() if ln.strip()]
    if not lines:
        return "### 📌 Poin Tambahan"
    if re.match(r"^#{1,4}\s+", lines[0]):
        return ""

    # Try first bold label or clean phrase
    first = re.sub(r"^[-*•\d.)>\s]+", "", lines[0])
    bold_m = re.match(r"\*\*([^*]{3,48})\*\*", first)
    if bold_m:
        topic = bold_m.group(1).strip(" :-–—")
        if topic and len(topic.split()) <= 7:
            return f"### 📌 {topic}"

    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", first)
    plain = re.sub(r"[*_`#\[\]()]", " ", plain)
    words = [w for w in plain.split() if w]
    if len(words) >= 2:
        snippet = " ".join(words[:5]).rstrip(".,:;!?")
        return f"### 📌 {snippet}"
    return "### 📌 Poin Tambahan & Referensi"


def _extract_markdown_sections(note_content: str) -> List[Dict[str, Any]]:
    """Parse note Markdown headings and exact line boundaries (skipping code fences)."""
    lines = (note_content or "").splitlines()
    sections: List[Dict[str, Any]] = []
    in_code_fence = False

    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        m = re.match(r"^(#{1,4})\s+(.+?)\s*$", stripped)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            sections.append({
                "level": level,
                "heading": title,
                "line_idx": i,
                "end_idx": len(lines),
            })

    for idx, sec in enumerate(sections):
        for nxt in sections[idx + 1:]:
            if nxt["level"] <= sec["level"]:
                sec["end_idx"] = nxt["line_idx"]
                break
        body_lines = lines[sec["line_idx"] + 1 : sec["end_idx"]]
        sec["body"] = "\n".join(body_lines)

    return sections


def _strip_matching_leading_heading(block: str, target_heading: str) -> str:
    """Avoid duplicating the target heading if the inserted block already starts with it."""
    lines = (block or "").splitlines()
    if not lines:
        return ""
    m = re.match(r"^#{1,4}\s+(.+)$", lines[0].strip())
    if m and target_heading:
        norm_first = re.sub(r"[^a-z0-9]+", "", m.group(1).lower())
        norm_target = re.sub(r"[^a-z0-9]+", "", target_heading.lower())
        if norm_first and norm_target and (norm_first == norm_target or norm_target in norm_first or norm_first in norm_target):
            return "\n".join(lines[1:]).strip()
    return block.strip()


def _insert_under_heading(note_content: str, target_heading: str, block_to_insert: str) -> Tuple[str, str]:
    """Insert block_to_insert cleanly at the end of the matching Markdown heading section."""
    sections = _extract_markdown_sections(note_content)
    needle = re.sub(r"^#{1,4}\s+", "", (target_heading or "").strip()).lower()

    matched_sec = None
    for sec in sections:
        if sec["heading"].strip().lower() == needle:
            matched_sec = sec
            break
    if not matched_sec and needle:
        for sec in sections:
            h_low = sec["heading"].strip().lower()
            if needle in h_low or h_low in needle:
                matched_sec = sec
                break

    if not matched_sec:
        heading_line = _derive_contextual_heading(block_to_insert)
        addition = f"{heading_line}\n{block_to_insert}" if heading_line else block_to_insert
        base = (note_content or "").rstrip()
        merged = f"{base}\n\n{addition}\n" if base else f"{addition}\n"
        return merged, "Akhir Catatan"

    cleaned_block = _strip_matching_leading_heading(block_to_insert, matched_sec["heading"])
    lines = (note_content or "").splitlines()
    insert_at = matched_sec["end_idx"]
    while insert_at > matched_sec["line_idx"] + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1

    before = "\n".join(lines[:insert_at]).rstrip()
    after = "\n".join(lines[insert_at:]).lstrip("\n")

    if after:
        merged = f"{before}\n\n{cleaned_block}\n\n{after}\n"
    else:
        merged = f"{before}\n\n{cleaned_block}\n"
    return merged, matched_sec["heading"]


def _heuristic_contextual_insert(note_content: str, cleaned: str) -> Tuple[str, str, str]:
    """Choose best matching section by keyword overlap when LLM merge is unavailable or unsafe."""
    sections = _extract_markdown_sections(note_content)
    if not sections:
        heading_line = _derive_contextual_heading(cleaned)
        addition = f"{heading_line}\n{cleaned}" if heading_line else cleaned
        merged = f"{note_content.rstrip()}\n\n{addition}\n"
        return merged, "Ditambahkan sebagai sub-bagian baru di akhir catatan", "Akhir Catatan"

    insert_tokens = {
        w for w in re.findall(r"[a-zA-Z0-9\u00C0-\u024F]{3,}", cleaned.lower())
        if w not in _STOPWORDS_ID_EN
    }

    best_sec = None
    best_score = 0
    for sec in sections:
        sec_text = f"{sec['heading']} {sec['body']}".lower()
        sec_tokens = {
            w for w in re.findall(r"[a-zA-Z0-9\u00C0-\u024F]{3,}", sec_text)
            if w not in _STOPWORDS_ID_EN
        }
        overlap = len(insert_tokens & sec_tokens)
        heading_tokens = {
            w for w in re.findall(r"[a-zA-Z0-9\u00C0-\u024F]{3,}", sec["heading"].lower())
            if w not in _STOPWORDS_ID_EN
        }
        score = overlap + (3 * len(insert_tokens & heading_tokens))
        if score > best_score:
            best_score = score
            best_sec = sec

    if best_sec and best_score >= 2:
        merged, used_heading = _insert_under_heading(note_content, best_sec["heading"], cleaned)
        return merged, f"Disisipkan secara kontekstual ke bagian \"{used_heading}\"", used_heading

    heading_line = _derive_contextual_heading(cleaned)
    addition = f"{heading_line}\n{cleaned}" if heading_line else cleaned
    merged = f"{note_content.rstrip()}\n\n{addition}\n"
    return merged, "Ditambahkan sebagai bagian baru di akhir catatan", "Akhir Catatan"


def smart_insert_into_note(
    note_content: str,
    insert_content: str,
    mode: str = "contextual",
    target_heading: str = "",
) -> Dict[str, Any]:
    """Context-aware insertion of Co-Pilot output into an existing Markdown note without losing data."""
    raw_note = (note_content or "").strip()
    cleaned = _clean_copilot_markdown(insert_content or "")
    if not cleaned:
        return {
            "merged_content": note_content or "",
            "placement_summary": "Tidak ada konten baru untuk disisipkan",
            "target_heading": "",
        }

    # Empty note -> populate directly without wrapper heading
    if not raw_note:
        return {
            "merged_content": f"{cleaned}\n",
            "placement_summary": "Catatan kosong diisi langsung dengan konten baru",
            "target_heading": "Awal Catatan",
        }

    mode_norm = (mode or "contextual").strip().lower()

    if mode_norm == "heading" and (target_heading or "").strip():
        merged, used_heading = _insert_under_heading(note_content, target_heading, cleaned)
        return {
            "merged_content": merged,
            "placement_summary": f"Disisipkan ke bagian \"{used_heading}\"",
            "target_heading": used_heading,
        }

    if mode_norm == "append":
        heading_line = _derive_contextual_heading(cleaned)
        addition = f"{heading_line}\n{cleaned}" if heading_line else cleaned
        merged = f"{note_content.rstrip()}\n\n{addition}\n"
        return {
            "merged_content": merged,
            "placement_summary": "Ditambahkan sebagai bagian baru di akhir catatan",
            "target_heading": "Akhir Catatan",
        }

    # Contextual mode: use AI for full merge on standard-length notes, else pick best heading
    sections = _extract_markdown_sections(note_content)
    if len(raw_note) <= 9500:
        try:
            system = SystemMessage(content="""Kamu adalah Smart Contextual Note Editor A.T.O.M.
TUGAS: Sisipkan `WAWASAN BARU CO-PILOT` ke dalam `CATATAN ASLI` di posisi yang PALING SESUAI KONTEKS.

ATURAN WAJIB (TIDAK BOLEH DILANGGAR):
1. DILARANG KERAS menghapus, meringkas, memotong, atau menghilangkan kalimat/paragraf dari `CATATAN ASLI`. Pertahankan 100% isi asli.
2. Bersihkan kalimat basa-basi pembuka/penutup percakapan pada `WAWASAN BARU`, namun pertahankan seluruh poin fakta, data, checklist, tabel, dan tautan Markdown `[judul](url)` atau `[Web: ...]`.
3. Jika `CATATAN ASLI` memiliki heading/bagian yang topiknya cocok dengan `WAWASAN BARU`, sisipkan tepat di bawah bagian tersebut agar menyatu rapi dengan konteksnya. Jika topiknya berbeda namun terkait bagian lain, tempatkan di posisi paling logis atau buat sub-heading baru yang relevan.
4. Baris pertama output HARUS persis berformat:
   `[[PENEMPATAN: Nama Bagian/Heading Tempat Disisipkan]]`
   lalu diikuti 1 baris kosong, lalu seluruh isi Markdown `CATATAN ASLI` yang sudah tersisipi `WAWASAN BARU` (tanpa pembungkus code fence luar).""")

            user = HumanMessage(content=(
                f"CATATAN ASLI:\n---\n{note_content}\n---\n\n"
                f"WAWASAN BARU CO-PILOT YANG AKAN DISISIPKAN:\n---\n{cleaned[:5000]}\n---\n\n"
                "Berikan hasil penggabungan Markdown lengkap sesuai format di atas:"
            ))

            response = invoke_llm_safely([system, user], 0.15)
            raw_out = (response.content or "").strip()

            placement_heading = "Sesuai Konteks Catatan"
            m = re.match(r"^\[\[PENEMPATAN:\s*(.*?)\]\]\s*\n?", raw_out, re.IGNORECASE)
            if m:
                placement_heading = m.group(1).strip() or placement_heading
                raw_out = raw_out[m.end():].strip()

            # Strip accidental outer markdown fence if LLM added ```markdown ... ```
            if raw_out.startswith("```") and raw_out.endswith("```"):
                raw_out = re.sub(r"^```(?:markdown|md)?\s*\n?", "", raw_out)
                raw_out = re.sub(r"\n?```\s*$", "", raw_out).strip()

            # Safety verification: ensure original note was not truncated/overwritten
            original_lines = [ln.strip() for ln in raw_note.splitlines() if len(ln.strip()) >= 12]
            preserved_count = sum(1 for ln in original_lines if ln in raw_out)
            preservation_ratio = (preserved_count / len(original_lines)) if original_lines else 1.0

            if (
                raw_out
                and len(raw_out) >= int(len(raw_note) * 0.85)
                and preservation_ratio >= 0.70
            ):
                return {
                    "merged_content": f"{raw_out}\n",
                    "placement_summary": f"Disisipkan secara kontekstual pada bagian \"{placement_heading}\"",
                    "target_heading": placement_heading,
                }
        except Exception as e:
            print(f"[SMART INSERT LLM FALLBACK] {e}")

    # Reliable deterministic contextual fallback (never truncates long notes)
    if sections:
        merged, summary, used_heading = _heuristic_contextual_insert(note_content, cleaned)
        return {
            "merged_content": merged,
            "placement_summary": summary,
            "target_heading": used_heading,
        }

    heading_line = _derive_contextual_heading(cleaned)
    addition = f"{heading_line}\n{cleaned}" if heading_line else cleaned
    return {
        "merged_content": f"{note_content.rstrip()}\n\n{addition}\n",
        "placement_summary": "Ditambahkan sebagai sub-bagian terstruktur di akhir catatan",
        "target_heading": "Akhir Catatan",
    }


def generate_study_note(
    raw_text: str,
    source_name: str = "",
    style: str = "comprehensive",
) -> Dict[str, Any]:
    """Transform uploaded document or pasted writing into a comprehensive long-form Markdown study note."""
    text_clean = (raw_text or "").strip()
    if not text_clean:
        return {
            "title": source_name or "Catatan Belajar",
            "tags": ["study-notes"],
            "study_markdown": "",
            "word_count": 0,
        }

    style_norm = (style or "comprehensive").strip().lower()
    style_instructions = {
        "comprehensive": """GAYA: CATATAN BELAJAR LENGKAP & MENDALAM (COMPREHENSIVE STUDY GUIDE)
Susun materi menjadi catatan belajar panjang yang terstruktur, mudah dipahami cepat, namun tetap mendalam dengan struktur WAJIB berikut:
1. ## 🎯 Gambaran Umum & Inti Materi (penjelasan ringkas konteks besar topik dan mengapa materi ini penting)
2. ## 🧠 Konsep, Istilah & Definisi Kunci (daftar istilah penting beserta definisi jelas dan mudah diingat)
3. ## 📚 Pembahasan Mendalam & Terstruktur (pecah topik menjadi beberapa sub-heading `###` secara berurutan; jelaskan mekanisme, alur proses, fakta penting, rumus/kerangka kerja, serta berikan contoh nyata atau analogi intuitif agar pembaca langsung paham)
4. ## 📊 Tabel Ringkasan & Pemetaan Konsep (buat minimal 1 tabel Markdown yang memetakan konsep/komponen, fungsi, atau perbandingannya)
5. ## 💡 Intisari & Cara Cepat Mengingat (Key Takeaways & jembatan keledai/poin praktis)
6. ## ❓ Pertanyaan Evaluasi Mandiri (Active Recall) — sertakan 4–6 soal/pertanyaan uji pemahaman lengkap dengan jawaban singkat di bawahnya""",

        "exam_prep": """GAYA: RANGKUMAN CEPAT & PERSIAPAN UJIAN (HIGH-YIELD EXAM PREP)
Fokus pada poin berdaya ungkit tinggi untuk hafalan cepat dan latihan ujian dengan struktur WAJIB berikut:
1. ## 🎯 Cheat Sheet Inti Materi (ringkasan super jelas dalam 1-2 paragraf + poin prioritas)
2. ## 📖 Daftar Istilah, Definisi & Konsep Wajib Hafal
3. ## ⚡ Mekanisme, Alur & Rumus / Kerangka Penting (pecah dengan sub-heading `###` + langkah sistematis)
4. ## 📊 Tabel Perbandingan & Pembeda Utama (sering keluar di ujian/wawancara)
5. ## ⚠️ Jebakan Umum & Hal yang Sering Tertukar
6. ## 📝 Bank Soal Latihan & Pembahasan Singkat (5–8 pertanyaan active recall beserta kunci jawaban ringkas)""",

        "deep_dive": """GAYA: ANALISIS MENDALAM & TEKNIS (DEEP DIVE MASTER NOTE)
Bedah materi secara analitis, sistematis, dan kritis untuk penguasaan tingkat lanjut dengan struktur WAJIB berikut:
1. ## 🔬 Tesis Utama & Latar Belakang Konteks
2. ## 🧩 Dekonstruksi Arsitektur / Metodologi / Kerangka Berpikir (gunakan sub-heading `###` untuk setiap pilar utama)
3. ## 🔗 Hubungan Sebab-Akibat, Implikasi & Trade-Off (analisis dampak, kelebihan, keterbatasan, dan studi kasus/contoh aplikasi)
4. ## 📊 Matriks Sintesis & Pemetaan Detail (tabel Markdown komprehensif)
5. ## 🧠 Pertanyaan Kritis & Ekstensi Pemikiran untuk Eksplorasi Lanjutan""",
    }
    chosen_guide = style_instructions.get(style_norm, style_instructions["comprehensive"])

    source_hint = f"\nNAMA SUMBER / DOKUMEN: {source_name}" if (source_name or "").strip() else ""
    system = SystemMessage(content=f"""Kamu adalah A.T.O.M. Study Architect & Knowledge Synthesizer.
Tugasmu adalah mengubah tulisan atau isi dokumen mentah menjadi CATATAN BELAJAR PANJANG DALAM MARKDOWN agar pengguna dapat mempelajari dan menguasai materi tersebut dengan cepat, menyeluruh, dan sistematis.

{chosen_guide}

ATURAN FORMAT OUTPUT WAJIB:
- Baris pertama HARUS persis berformat:
  `[[JUDUL: Judul Catatan Belajar yang Spesifik & Deskriptif Maksimal 7 Kata]]`
- Baris kedua HARUS persis berformat:
  `[[TAGS: tag1, tag2, tag3, tag4]]` (gunakan huruf kecil, maksimal 5 tag, pisahkan dengan koma)
- Baris ketiga kosong, lalu langsung mulai isi catatan Markdown dari heading `##` (jangan bungkus seluruh output dengan code fence ```markdown).
- Gunakan Bahasa Indonesia yang natural, jernih, edukatif, dan terstruktur rapi (kecuali istilah teknis/akademik umum yang sebaiknya dipertahankan beserta penjelasannya).
- Jangan memangkas konsep penting dari teks sumber; jabarkan secara komprehensif dengan poin-poin, bold keyword, callout blockquote (`> 💡 ...`), dan tabel agar sangat enak dipelajari.""")

    user = HumanMessage(content=(
        f"MATERI SUMBER YANG DIIMPOR:{source_hint}\n"
        f"---\n{text_clean[:16000]}\n---\n\n"
        "Susun menjadi catatan belajar Markdown yang lengkap dan panjang sesuai format di atas:"
    ))

    fallback_title = (source_name or "").strip()
    if fallback_title:
        fallback_title = re.sub(r"\.[^/.]+$", "", fallback_title).replace("_", " ").replace("-", " ").strip()
    fallback_title = fallback_title or "Catatan Belajar Baru"

    try:
        response = invoke_llm_safely([system, user], 0.25)
        raw_out = (response.content or "").strip()

        # Strip outer markdown code fence if model added one
        if raw_out.startswith("```") and raw_out.endswith("```"):
            raw_out = re.sub(r"^```(?:markdown|md)?\s*\n?", "", raw_out)
            raw_out = re.sub(r"\n?```\s*$", "", raw_out).strip()

        parsed_title = ""
        parsed_tags: List[str] = []

        lines = raw_out.splitlines()
        body_start_idx = 0
        for idx, ln in enumerate(lines[:6]):
            s = ln.strip()
            m_title = re.match(r"^\[\[JUDUL:\s*(.*?)\]\]$", s, re.IGNORECASE)
            if m_title:
                parsed_title = m_title.group(1).strip().strip('"').strip("'")
                body_start_idx = max(body_start_idx, idx + 1)
                continue
            m_tags = re.match(r"^\[\[TAGS:\s*(.*?)\]\]$", s, re.IGNORECASE)
            if m_tags:
                raw_tags = m_tags.group(1)
                for t in raw_tags.split(","):
                    clean_t = t.strip().lstrip("#").lower()
                    if clean_t and len(clean_t) < 32 and clean_t not in parsed_tags:
                        parsed_tags.append(clean_t)
                body_start_idx = max(body_start_idx, idx + 1)
                continue

        body_md = "\n".join(lines[body_start_idx:]).strip()
        if not body_md:
            body_md = raw_out

        if not parsed_title:
            m_h1 = re.search(r"^#\s+(.+)$", body_md, re.MULTILINE)
            if m_h1:
                parsed_title = m_h1.group(1).strip()[:70]
            else:
                parsed_title = fallback_title[:70]

        if not parsed_tags:
            parsed_tags = ["study-notes", "imported"]

        if "study-notes" not in parsed_tags and len(parsed_tags) < 5:
            parsed_tags.append("study-notes")

        return {
            "title": parsed_title[:80],
            "tags": parsed_tags[:5],
            "study_markdown": f"{body_md.rstrip()}\n",
            "word_count": len(body_md.split()),
        }
    except Exception as e:
        print(f"[STUDY NOTE FALLBACK] {e}")
        # Deterministic structured fallback so user's imported text is preserved cleanly
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text_clean) if p.strip()]
        bullets = "\n".join(
            f"- {p[:240]}{'...' if len(p) > 240 else ''}"
            for p in paragraphs[:6]
        ) or "- _(Materi terimpor)_"
        fallback_md = (
            f"## 🎯 Ringkasan Awal Materi\n\n"
            f"> ⚠️ Penyusunan AI otomatis belum tersedia ({e}). Berikut struktur dasar dari materi impor Anda.\n\n"
            f"{bullets}\n\n"
            f"## 📚 Teks Materi Lengkap\n\n"
            f"{text_clean}\n"
        )
        return {
            "title": fallback_title[:80],
            "tags": ["study-notes", "imported"],
            "study_markdown": fallback_md,
            "word_count": len(fallback_md.split()),
        }


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
            if not question or not str(question).strip():
                self._send_json({"error": "question is required for chat"}, 400)
                return
            history = data.get("history", [])
            web_search = bool(data.get("web_search", False))
            ctx_content = content if (content and str(content).strip()) else "(Catatan masih kosong)"
            result = chat_with_context(ctx_content, question, history=history, web_search=web_search)

        elif action == "smart_insert":
            insert_content = data.get("insert_content", "")
            if not insert_content or not str(insert_content).strip():
                self._send_json({"error": "insert_content is required for smart_insert"}, 400)
                return
            result = smart_insert_into_note(
                note_content=content or "",
                insert_content=insert_content,
                mode=data.get("insert_mode", "contextual") or "contextual",
                target_heading=data.get("target_heading", "") or "",
            )

        elif action == "study_note":
            if not content or not str(content).strip():
                self._send_json({"error": "content is required for study_note"}, 400)
                return
            style = data.get("style", "comprehensive") or "comprehensive"
            source_name = data.get("source_name", "") or ""
            result = generate_study_note(content, source_name=source_name, style=style)

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

        elif action == "parse_file":
            filename = data.get("filename", "")
            mime_type = data.get("mime_type", "")
            if not filename or not content:
                self._send_json({"error": "filename and content are required for parse_file"}, 400)
                return
            from modules.notes.file_importer import parse_uploaded_document
            result = parse_uploaded_document(filename, content, mime_type)

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
