"""
A.T.O.M. Notes Web Search Grounding Module
Lightweight multi-source live web search using ISP-safe public endpoints
(Bing Search RSS, Google News RSS Indonesia, Wikipedia ID/EN API, and explicit URL scraping).
"""

from __future__ import annotations

import html
import json
import re
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

_GENERIC_FILLER_PATTERNS = [
    r"^(tolong|bisa|coba|mohon|please)\b[\s,:-]*",
    r"^(carikan|cari di web|cari|temukan|jelaskan|analisis|rangkum|perkaya|lengkapi|update|perbarui)\b[\s,:-]*",
    r"^(tentang|mengenai|soal|terkait|dari|untuk)\b[\s,:-]*",
    r"\b(catatan ini|dokumen ini|yang baru diunggah|sesuai konteks|secara komprehensif|terbaru dari web)\b",
]


def _clean_html(raw: str) -> str:
    """Strip HTML tags and unescape HTML entities into clean single-line text."""
    if not raw:
        return ""
    unescaped = html.unescape(str(raw))
    no_tags = re.sub(r"<[^>]+>", " ", unescaped)
    return re.sub(r"\s+", " ", no_tags).strip()


def _extract_topic_from_note(note_context: str) -> str:
    """Extract the primary title or leading heading keywords from note context."""
    if not note_context:
        return ""

    # Match === DOKUMEN: [Title] === header built by notes-ai.js
    doc_match = re.search(r"===\s*DOKUMEN(?:\s+UNGGAHAN)?:\s*\[([^\]]+)\]\s*===", note_context)
    candidates: List[str] = []
    if doc_match:
        title = doc_match.group(1).strip()
        if title and title.lower() not in ("catatan baru", "untitled", "untitled note", "catatan aktif"):
            candidates.append(title)

    # Also grab first Markdown heading or meaningful non-empty content line
    for line in note_context.splitlines():
        s = line.strip()
        if not s or s.startswith("===") or s.startswith("(Catatan ini masih kosong"):
            continue
        if s.startswith("> 📄") or s.startswith("---"):
            continue
        heading_m = re.match(r"^#{1,4}\s+(.+)$", s)
        if heading_m:
            candidates.append(re.sub(r"[*_`\[\]]", "", heading_m.group(1)).strip())
            break
        clean_line = re.sub(r"[*_`>#\[\]]", " ", s)
        clean_line = re.sub(r"\s+", " ", clean_line).strip()
        if len(clean_line) >= 8:
            candidates.append(" ".join(clean_line.split()[:8]))
            break

    combined = " ".join(candidates).strip()
    words = [w for w in combined.split() if len(w) > 1]
    return " ".join(words[:10])


_ID_ABBR_MAP = {
    "yg": "yang",
    "brp": "berapa",
    "hrg": "harga",
    "dgn": "dengan",
    "utk": "untuk",
    "gak": "tidak",
    "ga": "tidak",
    "bgt": "banget",
    "kalo": "kalau",
    "kl": "kalau",
}

_CHAT_TOPIC_STOPWORDS = {
    "saya", "aku", "kamu", "anda", "yang", "dan", "atau", "untuk", "dari", "pada",
    "dengan", "ini", "itu", "lagi", "mau", "bisa", "ada", "apa", "bagaimana",
    "gimana", "tolong", "dong", "nih", "sih", "aja", "saja", "nya", "ya",
    "kalau", "kalo", "tentang", "soal", "user", "atom",
}

_FOLLOWUP_MARKERS = (
    "maksudnya", "maksud kamu", "yg itu", "yang itu", "yang tadi", "tadi",
    "bandingkan", "bedanya", "mana yang lebih", "menurutmu", "kenapa gitu",
    "jelaskan lagi", "contohnya", "lanjut", "terus", "kalo yg", "kalau yang",
    "apa bedanya",
)

_QUERY_FOLLOWUP_TOKENS = {
    "itu", "nya", "yang", "yg", "tadi", "kalo", "kalau", "gimana",
    "berapa", "brp", "maksudnya", "bedanya",
}

_LIVE_WEB_KEYWORDS = (
    "terbaru", "hari ini", "sekarang", "2025", "2026", "berita", "harga",
    "kurs", "rilis", "update", "cari di web", "google", "link", "sumber",
)


def _normalize_chat_abbreviations(text: str) -> str:
    """Expand common Indonesian shorthand tokens while keeping original unknowns intact."""
    tokens = []
    for tok in (text or "").split():
        low = tok.lower()
        tokens.append(_ID_ABBR_MAP.get(low, tok))
    return " ".join(tokens)


def _extract_chat_topic_keywords(context_text: str, max_words: int = 8) -> str:
    """Extract primary topic keywords from chat context hint when not a Notes header."""
    if not context_text or "=== DOKUMEN" in context_text:
        return ""
    cleaned = re.sub(r"\[[^\]]+\]", " ", str(context_text))
    cleaned = re.sub(r"[|•·?!.,:;\"'()\[\]{}]+", " ", cleaned)
    words: List[str] = []
    seen = set()
    for w in cleaned.split():
        low = w.lower()
        if len(low) <= 2 or low in _CHAT_TOPIC_STOPWORDS or low in seen:
            continue
        seen.add(low)
        words.append(w)
        if len(words) >= max_words:
            break
    return " ".join(words)


def _is_contextual_followup_without_web(clean_q: str, context_text: str) -> bool:
    """Smart Web-Search Gating: skip web search for internal conversational follow-ups."""
    if not context_text or not context_text.strip():
        return False
    low = (clean_q or "").lower().strip()
    if not low:
        return False
    if re.search(r"https?://", low):
        return False
    if any(kw in low for kw in _LIVE_WEB_KEYWORDS):
        return False
    words = low.split()
    if len(words) <= 8:
        return True
    if any(marker in low for marker in _FOLLOWUP_MARKERS):
        return True
    return False


def _extract_search_query(query: str, note_context: str = "") -> str:
    """Derive a clean, concise search query from user prompt and/or active note/chat context."""
    text = (query or "").strip()
    # Remove bracketed attachment badges like [📎 file.pdf] and URLs
    text = re.sub(r"\[📎[^\]]*\]", " ", text)
    text_no_urls = re.sub(r"https?://\S+", " ", text).strip()

    cleaned = text_no_urls
    for _ in range(3):
        prev = cleaned
        for pat in _GENERIC_FILLER_PATTERNS:
            cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"[?!.,:;\"']+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned == prev:
            break

    cleaned = _normalize_chat_abbreviations(cleaned)

    # Fall back to note topic or chat topic hint when query is empty, short, or follow-up
    is_chat_hint = bool(note_context) and ("=== DOKUMEN" not in note_context) and ("\n" not in note_context)
    topic = "" if is_chat_hint else _extract_topic_from_note(note_context)
    chat_topic = _extract_chat_topic_keywords(note_context) if is_chat_hint else ""
    active_topic = topic or chat_topic

    low_tokens = set(cleaned.lower().split())
    has_followup_token = (
        bool(low_tokens & _QUERY_FOLLOWUP_TOKENS)
        or any(marker in cleaned.lower() for marker in ("apa bedanya", "kalo yg", "kalau yang"))
    )

    if len(cleaned) < 4 or cleaned.lower() in (
        "catatan", "note", "notes", "web", "internet", "referensi", "fakta",
        "data", "statistik", "wawasan tambahan", "ringkasan", "kesimpulan",
    ):
        cleaned = active_topic or text_no_urls or "pengetahuan umum"
    elif active_topic and (
        (topic and len(cleaned.split()) <= 3)
        or (chat_topic and (len(cleaned.split()) <= 6 or has_followup_token))
    ) and active_topic.lower() not in cleaned.lower():
        # Ground short/follow-up/typo prompts with active topic and deduplicate repeated words
        merged_words: List[str] = []
        seen_w = set()
        for w in f"{active_topic} {cleaned}".split():
            lw = w.lower()
            if lw not in seen_w:
                seen_w.add(lw)
                merged_words.append(w)
        cleaned = " ".join(merged_words)

    words = cleaned.split()
    return " ".join(words[:12]).strip() or "pengetahuan umum"


def _http_get_text(url: str, timeout: int = 6) -> str:
    """Fetch UTF-8 response body safely with TLS bypass & standard headers."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        },
        method="GET",
    )
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _search_bing_rss(clean_query: str, limit: int = 4) -> List[Dict[str, str]]:
    """Query Bing Web Search RSS feed."""
    results: List[Dict[str, str]] = []
    try:
        encoded = urllib.parse.quote(clean_query)
        url = f"https://www.bing.com/search?q={encoded}&format=rss"
        xml_text = _http_get_text(url, timeout=6)
        root = ET.fromstring(xml_text)
        for item in root.findall(".//item"):
            title = _clean_html(item.findtext("title") or "")
            link = (item.findtext("link") or "").strip()
            desc = _clean_html(item.findtext("description") or "")
            pub = (item.findtext("pubDate") or "").strip()
            if title and link.startswith("http"):
                domain = urllib.parse.urlparse(link).netloc.replace("www.", "")
                results.append({
                    "title": title,
                    "url": link,
                    "source": domain or "Bing Web",
                    "snippet": desc[:320] + (f" ({pub[:16]})" if pub else ""),
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[WEB SEARCH BING WARN] {e}")
    return results


def _search_google_news_rss(clean_query: str, limit: int = 4) -> List[Dict[str, str]]:
    """Query Google News RSS (Indonesia locale) for current articles & facts."""
    results: List[Dict[str, str]] = []
    try:
        encoded = urllib.parse.quote(clean_query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=id&gl=ID&ceid=ID:id"
        xml_text = _http_get_text(url, timeout=6)
        root = ET.fromstring(xml_text)
        for item in root.findall(".//item"):
            title = _clean_html(item.findtext("title") or "")
            link = (item.findtext("link") or "").strip()
            desc = _clean_html(item.findtext("description") or "")
            source_el = item.find("source")
            src_name = (source_el.text.strip() if source_el is not None and source_el.text else "Google News")
            pub = (item.findtext("pubDate") or "").strip()
            if title and link.startswith("http"):
                snippet = desc[:280] if desc and desc != title else title
                if pub:
                    snippet = f"{snippet} · {pub[:16]}"
                results.append({
                    "title": title,
                    "url": link,
                    "source": src_name,
                    "snippet": snippet,
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[WEB SEARCH GNEWS WARN] {e}")
    return results


def _search_wikipedia(clean_query: str, lang: str = "id", limit: int = 2) -> List[Dict[str, str]]:
    """Query Wikipedia MediaWiki OpenSearch JSON API."""
    results: List[Dict[str, str]] = []
    try:
        encoded = urllib.parse.quote(clean_query)
        url = (
            f"https://{lang}.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={encoded}&utf8=&format=json&srlimit={limit}"
        )
        raw_json = _http_get_text(url, timeout=6)
        data = json.loads(raw_json)
        hits = data.get("query", {}).get("search", [])
        for hit in hits[:limit]:
            title = str(hit.get("title", "")).strip()
            snippet = _clean_html(hit.get("snippet", ""))
            if title:
                wiki_url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                results.append({
                    "title": f"{title} (Wikipedia {lang.upper()})",
                    "url": wiki_url,
                    "source": f"wikipedia.{lang}",
                    "snippet": snippet[:320],
                })
    except Exception as e:
        print(f"[WEB SEARCH WIKI-{lang.upper()} WARN] {e}")
    return results


def _scrape_explicit_urls(text: str, max_urls: int = 2) -> List[Dict[str, str]]:
    """Scrape explicit http/https URLs present in prompt or note excerpt."""
    urls = re.findall(r"https?://[^\s\)\]>\"']+", text or "")
    unique_urls: List[str] = []
    for u in urls:
        u_clean = u.rstrip(".,;:!?")
        if u_clean not in unique_urls:
            unique_urls.append(u_clean)
        if len(unique_urls) >= max_urls:
            break

    if not unique_urls:
        return []

    results: List[Dict[str, str]] = []
    try:
        from modules.core.utils import scrape_url
    except Exception:
        return []

    for u in unique_urls:
        try:
            scraped = scrape_url(u)
            if scraped and not scraped.startswith("[ERROR]"):
                domain = urllib.parse.urlparse(u).netloc.replace("www.", "") or "Tautan Web"
                results.append({
                    "title": f"Konten dari {domain}",
                    "url": u,
                    "source": domain,
                    "snippet": re.sub(r"\s+", " ", scraped[:1500]).strip(),
                })
        except Exception as e:
            print(f"[WEB SEARCH SCRAPE WARN] {u}: {e}")
    return results


def search_web_for_notes(
    query: str,
    note_context: str = "",
    max_results: int = 8,
) -> Dict[str, Any]:
    """
    Search multiple ISP-safe public web sources in parallel and return
    structured sources alongside a Markdown grounding block for Notes Co-Pilot.
    """
    clean_query = _extract_search_query(query, note_context)
    collected: List[Dict[str, str]] = []

    workers = [
        ("bing", _search_bing_rss, (clean_query, 4)),
        ("gnews", _search_google_news_rss, (clean_query, 4)),
        ("wiki_id", _search_wikipedia, (clean_query, "id", 2)),
        ("wiki_en", _search_wikipedia, (clean_query, "en", 2)),
        ("scrape", _scrape_explicit_urls, (f"{query}\n{(note_context or '')[:1500]}", 2)),
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(fn, *args): name for name, fn, args in workers}
        try:
            for future in as_completed(future_map, timeout=7):
                try:
                    items = future.result(timeout=1) or []
                    collected.extend(items)
                except Exception as exc:
                    print(f"[WEB SEARCH WORKER WARN] {future_map[future]}: {exc}")
        except Exception as exc:
            print(f"[WEB SEARCH TIMEOUT WARN] {exc}")

    # Deduplicate by normalized URL and title
    seen_urls = set()
    seen_titles = set()
    sources: List[Dict[str, str]] = []
    for item in collected:
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()
        norm_title = title.lower()
        if not url or not title:
            continue
        if url in seen_urls or norm_title in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(norm_title)
        sources.append({
            "title": title,
            "url": url,
            "source": item.get("source") or "Web",
            "snippet": item.get("snippet") or "",
        })
        if len(sources) >= max_results:
            break

    if sources:
        lines = [f"HASIL PENCARIAN WEB REAL-TIME (Kueri: \"{clean_query}\"):"]
        for i, src in enumerate(sources, 1):
            lines.append(
                f"{i}. **{src['title']}** ({src['source']})\n"
                f"   URL: {src['url']}\n"
                f"   Ringkasan: {src['snippet']}"
            )
        formatted = "\n".join(lines)
    else:
        formatted = (
            f"HASIL PENCARIAN WEB REAL-TIME (Kueri: \"{clean_query}\"):\n"
            "(Tidak ada hasil eksternal yang berhasil diambil saat ini — gunakan pengetahuan internal dengan catatan keterbatasan data terkini.)"
        )

    return {
        "query": clean_query,
        "sources": sources,
        "formatted_context": formatted,
    }


_GREETING_WORDS = {
    "halo", "hai", "hi", "hello", "hey", "p", "tes", "test", "ping",
    "ok", "oke", "okay", "siap", "makasih", "terima kasih", "thanks", "thank you",
    "pagi", "siang", "sore", "malam", "selamat pagi", "selamat siang",
    "selamat sore", "selamat malam",
}

_INTERNAL_ATOM_PATTERNS = [
    "siapa dirimu", "apa peran utamamu", "identitas atom", "siapa kamu di atom",
    "siapa pembuatmu", "alif rahmadi", "siapa pencipta", "siapa inisiator",
    "cara kerja cortex", "cortex neural router", "modul sentinel", "modul librarian",
    "arsitektur atom", "arsitektur sistem a.t.o.m", "arsitektur sistem atom",
    "blueprint arsitektur", "apa itu crewai di atom", "modul crewai",
    "tools apa saja", "apa saja tools", "daftar tools", "tools yang dimiliki", "tools atom",
]


def extract_user_query_from_chat_prompt(prompt: str) -> str:
    """Strip attached [FILE: ...] blocks so only the trailing user question is searched."""
    if not prompt:
        return ""
    text = str(prompt).strip()
    m = re.search(r"\[END FILE\]\s*Query:\s*(.+)$", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    if text.startswith("[FILE:"):
        text = re.sub(r"\[FILE:.*?\].*?\[END FILE\]\s*", "", text, flags=re.DOTALL).strip()
        text = re.sub(r"^Query:\s*", "", text, flags=re.IGNORECASE).strip()
    return text


def should_search_web_for_chat(
    prompt: str,
    has_images: bool = False,
    context_text: str = "",
) -> Tuple[bool, str]:
    """Return (should_search, clean_query) for ATOM Chat prompts."""
    clean_q = extract_user_query_from_chat_prompt(prompt)
    low = re.sub(r"[?!.,:;]+$", "", clean_q.lower()).strip()

    if len(low) < 3 or low in _GREETING_WORDS:
        return False, ""

    if has_images and low in ("jelaskan gambar ini", "review file yang terlampir", "apa ini"):
        return False, ""

    if low == "review file yang terlampir":
        return False, ""

    if any(pat in low for pat in _INTERNAL_ATOM_PATTERNS) and len(low.split()) <= 15:
        return False, ""

    if _is_contextual_followup_without_web(clean_q, context_text):
        return False, ""

    return True, clean_q


def build_chat_web_grounding(
    prompt: str,
    context_text: str = "",
    has_images: bool = False,
    max_results: int = 6,
) -> Dict[str, Any]:
    """Evaluate if chat query needs web grounding and fetch live references gracefully."""
    should_search, clean_q = should_search_web_for_chat(
        prompt,
        has_images=has_images,
        context_text=context_text,
    )
    if not should_search:
        return {"searched": False, "block": "", "step": None, "sources": [], "query": ""}

    try:
        web_data = search_web_for_notes(clean_q, note_context=context_text, max_results=max_results)
        sources = web_data.get("sources") or []
        if not sources:
            return {
                "searched": True,
                "block": "",
                "step": None,
                "sources": [],
                "query": web_data.get("query", clean_q),
            }

        block = (
            "\n\nWEB SEARCH GROUNDING (REAL-TIME):\n"
            f"{web_data['formatted_context']}\n\n"
            "INSTRUKSI PENGGUNAAN HASIL WEB:\n"
            "- HANYA gunakan hasil web di atas jika benar-benar relevan dengan topik percakapan aktif.\n"
            "- Jika hasil pencarian melenceng (misalnya akibat typo pada kueri), ABAIKAN hasil web tersebut dan jawab berdasarkan konteks percakapan serta pengetahuan internal.\n"
            "- Jika relevan, cantumkan kutipan sumber secara natural menggunakan tautan Markdown `[Nama Sumber / Judul](URL)`.\n"
        )
        step = {
            "step": "[WEB SEARCH]",
            "detail": f"Grounded with {len(sources)} live web sources (Query: '{web_data['query']}')",
        }
        return {
            "searched": True,
            "block": block,
            "step": step,
            "sources": sources,
            "query": web_data["query"],
        }
    except Exception as exc:
        print(f"[CHAT WEB GROUNDING WARN] {exc}")
        return {"searched": True, "block": "", "step": None, "sources": [], "query": clean_q}


