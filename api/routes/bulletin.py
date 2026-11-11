import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter
from api.schemas import MarkedNews, UnmarkRequest, SummarizeNewsRequest
from api.utils import safe_load_json, safe_save_json, safe_print

try:
    from modules.core.database import db, MONGODB_CONNECTED
except Exception as e:
    db = None
    MONGODB_CONNECTED = False

MARKED_NEWS_FILE = "data/atom_bulletin_marked.json"

router = APIRouter()

@router.get("/bulletin/fetch")
async def fetch_bulletin(
    category: Optional[str] = "technology",
    q: Optional[str] = None,
    scope: Optional[str] = "international"
):
    import requests
    news_api_key = os.environ.get("NEWS_API_KEY", "")
    is_national = (scope or "").lower() in ["national", "nasional", "id", "indonesia"]
    
    # If no key is set, return mock data for testing UI
    if not news_api_key:
        if is_national:
            return {
                "status": "success",
                "scope": "national",
                "articles": [
                    {
                        "id": "mock-nat-1",
                        "title": "Inovasi Ekosistem Kecerdasan Buatan Nasional di Sektor Industri 2026",
                        "description": "Kementerian dan universitas terkemuka di Indonesia memamerkan terobosan AI lokal untuk manufaktur dan logistik maritim.",
                        "content": "Indonesia resmi meluncurkan inisiatif percepatan kecerdasan buatan nasional dengan konsorsium riset teknologi terpadu. Model neural buatan anak bangsa diarahkan untuk otomatisasi rantai pasok dan pemantauan maritim terdistribusi.",
                        "source": "Antara News / ATOM",
                        "url": "#",
                        "image_url": "",
                        "author": "Biro Nasional",
                        "published_at": "2026-10-14T08:00:00Z",
                        "scope": "national"
                    },
                    {
                        "id": "mock-nat-2",
                        "title": "Pusat Riset Komputasi Kuantum & Keamanan Siber Resmi Dibuka di Jakarta",
                        "description": "Lembaga riset nasional membangun laboratorium enkripsi pos-kuantum guna memproteksi infrastruktur data kritis.",
                        "content": "Laboratorium keamanan siber pos-kuantum perdana di Indonesia mulai beroperasi hari ini. Lembaga ini difokuskan pada mitigasi risiko serangan komputasi kuantum serta penguatan kedaulatan data nasional.",
                        "source": "Tempo Tekno",
                        "url": "#",
                        "image_url": "",
                        "author": "Desk Sains Nasional",
                        "published_at": "2026-10-14T07:30:00Z",
                        "scope": "national"
                    }
                ]
            }
        return {
            "status": "success",
            "scope": "international",
            "articles": [
                {
                    "id": "mock-1",
                    "title": "Quantum Computing Breakthrough in Neural Network Simulation",
                    "description": "Scientists achieve room temperature quantum coherence.",
                    "content": "Scientists have achieved a new level of quantum coherence at room temperature, paving the way for advanced neural network simulations and instant model inference.",
                    "source": "Science Journal",
                    "url": "#",
                    "image_url": "",
                    "author": "Science Desk",
                    "published_at": "2026-10-14T07:30:00Z",
                    "scope": "international"
                }
            ]
        }
    
    headers = {"User-Agent": "ATOM-System/1.0"}
    try:
        if is_national:
            crime_negatives = "-pembunuhan -narkoba -curanmor -pencurian -begal -mutilasi -tawuran"
            if q and q.strip():
                safe_q = requests.utils.quote(f"({q.strip()}) {crime_negatives}")
                newsapi_url = f"https://newsapi.org/v2/everything?q={safe_q}&language=id&sortBy=publishedAt&apiKey={news_api_key}"
            else:
                id_cat_queries = {
                    "general": f"(indonesia OR nasional OR pembangunan OR ikn OR presiden OR masyarakat OR infrastruktur) {crime_negatives}",
                    "politics": f"(politik OR dpr OR mpr OR kementerian OR pemilu OR pilkada OR menteri OR presiden OR kebijakan) {crime_negatives}",
                    "business": f"(bisnis OR ekonomi OR saham OR investasi OR perbankan OR industri OR bumn OR rupiah) {crime_negatives}",
                    "culture": f"(pendidikan OR kampus OR sekolah OR kebudayaan OR pariwisata OR seni OR tradisi) {crime_negatives}",
                    "technology": f"(teknologi OR 'kecerdasan buatan' OR AI OR startup OR gadget OR digital) {crime_negatives}"
                }
                cat_key = (category or "general").lower()
                cat_query = id_cat_queries.get(cat_key, id_cat_queries["general"])
                safe_cat_q = requests.utils.quote(cat_query)
                newsapi_url = f"https://newsapi.org/v2/everything?q={safe_cat_q}&language=id&sortBy=publishedAt&apiKey={news_api_key}"
        else:
            if q and q.strip():
                safe_q = requests.utils.quote(q.strip())
                newsapi_url = f"https://newsapi.org/v2/everything?q={safe_q}&sortBy=publishedAt&language=en&apiKey={news_api_key}"
            else:
                intl_cat_queries = {
                    "technology": "technology OR 'artificial intelligence' OR software OR computing OR gadget",
                    "biology": "biology OR wildlife OR genetics OR evolution OR biodiversity OR 'marine life'",
                    "geography": "geography OR geology OR volcano OR oceanography OR climate OR 'earth science'",
                    "astronomy": "astronomy OR astrophysics OR telescope OR 'deep space' OR cosmology OR quantum",
                    "discoveries": "archaeology OR discovery OR 'ancient civilization' OR fossil OR paleontology",
                    "business": "global economy OR markets OR 'stock market' OR inflation OR trade"
                }
                cat_key = (category or "technology").lower()
                if cat_key in intl_cat_queries:
                    safe_cat_q = requests.utils.quote(intl_cat_queries[cat_key])
                    newsapi_url = f"https://newsapi.org/v2/everything?q={safe_cat_q}&sortBy=publishedAt&language=en&apiKey={news_api_key}"
                else:
                    newsapi_url = f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={news_api_key}"
            
        response = requests.get(newsapi_url, headers=headers, timeout=10)
        
        # Fallback to GNews if NewsAPI fails
        if response.status_code != 200:
            lang_param = "lang=id&country=id&" if is_national else "lang=en&"
            query_param = f"&q={requests.utils.quote(q.strip())}" if (q and q.strip()) else ""
            cat_param = f"category={category}&" if (category and not q) else ""
            gnews_url = f"https://gnews.io/api/v4/top-headlines?{cat_param}{lang_param}{query_param}&apikey={news_api_key}"
            response = requests.get(gnews_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            articles = []
            crime_bad_words = [
                "pembunuhan", "dibunuh", "tewas dibunuh", "mutilasi", "mayat", "jenazah",
                "narkoba", "sabu", "ganja", "ekstasi", "miras", "razia thm", "diskotek",
                "pemerkosaan", "pencabulan", "pelecehan seksual", "rudapaksa",
                "pencurian", "mencuri", "curanmor", "maling", "perampokan", "rampok", "begal",
                "tawuran", "pengeroyokan", "bacok", "senjata tajam", "penikaman",
                "judi online", "judol", "slot online", "slot gacor", "taruhan",
                "penipuan", "penggelapan", "penganiayaan"
            ]
            for art in data.get("articles", []):
                title = art.get("title", "Untitled Transmission")
                desc = art.get("description", "") or ""
                body = art.get("content", "") or ""

                if is_national:
                    haystack = (title + " " + desc).lower()
                    if any(bad in haystack for bad in crime_bad_words):
                        continue

                articles.append({
                    "id": art.get("url") or title,
                    "title": title,
                    "description": desc,
                    "content": (desc + "\n\n" + body).strip() or desc or "Konten artikel lengkap dapat dibaca langsung pada tautan sumber asli.",
                    "source": art.get("source", {}).get("name", "Unknown Source"),
                    "url": art.get("url", "#"),
                    "image_url": art.get("urlToImage") or art.get("image", ""),
                    "author": art.get("author", "Editorial Desk"),
                    "published_at": art.get("publishedAt", ""),
                    "scope": "national" if is_national else "international"
                })
            return {"status": "success", "scope": "national" if is_national else "international", "articles": articles}
        else:
            return {"status": "error", "message": f"API Error: {response.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/bulletin/marked")
async def get_marked_bulletin():
    if MONGODB_CONNECTED:
        try:
            items = list(db["marked_news"].find({}, {"_id": 0}))
            return {"status": "success", "articles": items}
        except Exception as e:
            safe_print(f"[DB ERROR] get_marked_bulletin failed: {e}")
    data = safe_load_json(MARKED_NEWS_FILE, {"marked_news": []})
    if not isinstance(data, dict):
        data = {"marked_news": []}
    return {"status": "success", "articles": data.get("marked_news", [])}

@router.post("/bulletin/mark")
async def mark_bulletin(news: MarkedNews):
    timestamp = datetime.now().isoformat()
    news_entry = news.model_dump()
    news_entry["marked_at"] = timestamp
    
    if MONGODB_CONNECTED:
        try:
            db["marked_news"].update_one(
                {"id": news.id},
                {"$set": news_entry},
                upsert=True
            )
            return {"status": "success"}
        except Exception as e:
            safe_print(f"[DB ERROR] mark_bulletin failed: {e}. Writing locally.")
            
    data = safe_load_json(MARKED_NEWS_FILE, {"marked_news": []})
    if not isinstance(data, dict):
        data = {"marked_news": []}
    if "marked_news" not in data:
        data["marked_news"] = []
    
    if not any(item.get("id") == news.id for item in data["marked_news"]):
        data["marked_news"].append(news_entry)
        safe_save_json(MARKED_NEWS_FILE, data)
    
    return {"status": "success"}

@router.post("/bulletin/unmark")
async def unmark_bulletin(req: UnmarkRequest):
    if MONGODB_CONNECTED:
        try:
            db["marked_news"].delete_one({"id": req.id})
        except Exception as e:
            safe_print(f"[DB ERROR] unmark_bulletin failed: {e}")
            
    data = safe_load_json(MARKED_NEWS_FILE, {"marked_news": []})
    if isinstance(data, dict) and "marked_news" in data:
        data["marked_news"] = [item for item in data["marked_news"] if item.get("id") != req.id]
        safe_save_json(MARKED_NEWS_FILE, data)
    return {"status": "success"}

@router.post("/bulletin/summarize")
async def summarize_news_endpoint(req: SummarizeNewsRequest):
    try:
        from api.notes_ai import get_llm
    except ImportError:
        try:
            from notes_ai import get_llm
        except Exception:
            get_llm = None
    
    prompt = f"""Sebagai asisten cerdas A.T.O.M., berikan ringkasan eksekutif yang bernas, informatif, dan mudah dipahami dari berita berikut:

Judul: {req.title}
Sumber: {req.source}
Konten: {req.content}

Instruksi format jawaban:
- **Inti Berita**: 1-2 kalimat ringkas penjelasan utama berita.
- **Poin Penting & Insight**: 3 poin bullet dampak atau informasi kunci.
- Gunakan bahasa Indonesia yang ramah, santai, dan jelas."""
    if get_llm:
        try:
            llm = get_llm(temperature=0.3)
            if llm:
                res = llm.invoke(prompt)
                return {"status": "success", "summary": res.content}
        except Exception as e:
            safe_print(f"[WARN] summarize_news LLM error: {e}")
    
    # Heuristic fallback if LLM offline
    return {
        "status": "success",
        "summary": f"**Inti Berita:** {req.title}\n\n**Poin Penting:**\n- Informasi diterbitkan oleh {req.source}.\n- {req.content[:240]}..."
    }
