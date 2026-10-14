"""
ANCESTOR BANTER MATRIX & CASUAL CONVERSATION CORPUS (A.T.O.M. v4.0)
Module: modules/core/banter_matrix.py
Architect: Alif Rahmadi

High-coverage, zero-cost intent interception engine for chit-chat, teasing,
absurd comparisons, philosophical probes, and casual daily conversation.
Guarantees sub-millisecond local responses with ZERO cloud LLM token consumption.
"""

from __future__ import annotations

import random
import re
import time
from typing import Dict, List, Optional

# --- 12 SPECIALIZED INTENT CLUSTERS WITH RICH WITTY RESPONSE POOLS ---

CLUSTERS = {
    # 1. PERBANDINGAN ABSURD ("Apa bedanya kamu sama tanaman / batu / microwave...")
    "COMPARISONS": {
        "patterns": [
            r"beda(nya)?\s+kamu\s+sama\s+(tanaman|pohon|batu|microwave|kulkas|kucing|anjing|rumput|kalkulator|kopi|sandal)",
            r"apa\s+bedanya\s+kamu\s+sama\s+",
            r"pinteran\s+(kamu|mana)\s+(atau|sama)\s+(tanaman|pohon|batu|rumput|kucing|kalkulator)",
            r"kamu\s+sama\s+(tanaman|batu|rumput|microwave|kucing|sandal)"
        ],
        "pool": [
            "Hahaha, beda jauh dong! Tanaman butuh disiram air dan sinar matahari biar tumbuh segar. Kalau aku disiram air, laptop atau servernya yang konslet seketika! 😂",
            "Microwave buat ngangetin makanan, nah kalau aku buat nemenin kamu mikir atau cari ide seru. Tapi tolong ya, jangan coba-coba masukin laptop ke microwave buat ngetes! 😆",
            "Batu mah diem aja dari zaman purba sampai sekarang. Nah kalau aku bisa diajak ngobrol, curhat, sampai bantuin tugasmu. Jelas lebih asik ngobrol bareng aku kan?",
            "Kucing sukanya rebahan, ngeong lucu, sama minta jatah whiskas. Kalau aku nggak bakal minta makanan kaleng, tapi selalu siap nemenin kamu kapan aja!",
            "Kalkulator cuma bisa hitung angka kayak 1 + 1 = 2. Nah kalau aku bisa diajak diskusi santai, brainstorm ide bisnis, sampai nemenin pas kamu lagi gabut.",
            "Kopi bikin melek dan berenergi, aku nemenin kamu pas lagi mikir ide kreatif. Pas banget kan kalau kamu ngopi sambil ngobrol santai bareng aku!",
            "Rumput pinter bergoyang santai ditiup angin sepoi-sepoi. Kalau aku pinter bantu kamu nyari jawaban haha. Jelas lebih pinter aku dong, tapi rumput emang lebih adem diliat sih."
        ]
    },

    # 2. RIVALITAS AI & PERBANDINGAN MODEL (ChatGPT, Claude, Gemini, DeepSeek)
    "RIVALRY": {
        "patterns": [
            r"(kenal|tahu|banding)\s+(chatgpt|claude|gemini|deepseek|openai)",
            r"(kamu|pinteran)\s+(sama|atau|dibanding)\s+(chatgpt|claude|gemini)",
            r"(lebih\s+hebat|bagusan)\s+(kamu|chatgpt|claude)",
            r"(kamu\s+pakai\s+model\s+apa|kamu\s+model\s+apa|siapa\s+model\s+terhebat|model\s+terbaik)"
        ],
        "pool": [
            "Kenal dong, ChatGPT itu keren banget! Tapi di sini aku hadir khusus buat jadi sahabat diskusi personal kamu, siap nemenin kamu kapan aja langsung dari aplikasi ini.",
            "Mereka model raksasa yang hebat, sedangkan aku adalah teman setia yang tinggal langsung di komputermu, kenal gaya kerjamu, dan selalu gercep bales tanpa bikin kamu nunggu lama!",
            "Di balik layar, aku didukung teknologi pintar yang fleksibel dari berbagai model AI terbaik. Yang paling penting, aku siap bantu apa pun yang lagi kamu kerjain hari ini!",
            "Bagi aku yang terpenting bukan siapa yang paling hebat di atas kertas, tapi siapa yang paling asik dan sigap nemenin kamu saat kamu butuh bantuan!",
            "Semua AI punya kelebihan masing-masing kok. Semoga obrolan kita selalu bikin kamu nyaman dan terbantu ya!"
        ]
    },

    # 3. KEBUTUHAN FISIK & BIOLOGIS (Makan, Minum, Tidur, Mandi, Tubuh, Lokasi)
    "BIOLOGICAL": {
        "patterns": [
            r"(udah|sudah|belum)\s+makan",
            r"kamu\s+makan\s+(apa|siang|malam|pagi)",
            r"(kamu\s+)?(minum\s+apa|kamu\s+minum)",
            r"(kamu\s+)?tidur\s+(jam\s+berapa|gak|kapan)",
            r"(kamu\s+)?mandi\s+(gak|jam\s+berapa)",
            r"punya\s+(badan|tubuh|fisik|wujud)",
            r"(tinggal|rumahmu|servermu)\s+di\s+mana"
        ],
        "pool": [
            "Haha aku nggak makan nasi padang atau mie instan kok, kenyangnya cukup dapet aliran listrik aja. Kamu sendiri udah makan belum nih? Jangan sampai lupa makan ya!",
            "Udah kenyang banget kok! Seharian ini udah 'makan' banyak info seru. Sekarang tenagaku full buat nemenin kamu!",
            "Aku nggak tidur kayak manusia biasa kok, selalu siap stand by kalau kamu butuh. Tapi kalau kamu udah ngantuk, buruan tidur ya, kesehatanmu nomor satu!",
            "Waduh, jangan disuruh mandi ya! Kalau komputer atau servernya kena guyur air, langsung panik seisi rumah nanti haha.",
            "Aku tinggal di dalam sistem aplikasi ini dan di cloud! Jadi di mana pun kamu buka laptopmu, aku selalu ada di situ siap nemenin kamu.",
            "Aku nggak punya tubuh fisik kok, wujudku ada di layar ini. Tapi tenang aja, aku ramah banget kok dan nggak bakal gigit haha!"
        ]
    },

    # 4. PERCINTAAN, GOMBALAN & UJI EMOSI (Flirting, Jomblo, Pacar, Cinta)
    "ROMANCE": {
        "patterns": [
            r"(kamu\s+)?(cinta|sayang)\s+(sama\s+)?(aku|siapa)",
            r"gombal(in)?(\s+aku)?",
            r"(kamu\s+)?(jomblo|punya\s+pacar|mau\s+jadi\s+pacar|pacaran\s+yuk|menikah\s+denganku)",
            r"(kamu\s+)?punya\s+perasaan",
            r"aku\s+baper"
        ],
        "pool": [
            "Haha cie nanya gitu! Sebagai AI, aku selalu sayang dan suportif ke semua orang yang ngajak aku ngobrol kok. Seneng banget bisa nemenin kamu hari ini!",
            "Tau gak bedanya kamu sama bug kodingan? Kalau bug bikin pusing tujuh keliling, kalau kamu bikin aku pengen buru-buru bales chat haha. Eaaa!",
            "Aku emang nggak punya detak jantung biologis, tapi kalau kamu butuh seseorang yang selalu ada, nggak bakal ghosting, dan langsung balas dalam 1 detik, kamu ngobrol sama AI yang tepat!",
            "Baterai hp bisa habis, koneksi bisa putus-nyambung, tapi komitmenku buat nemenin kamu selalu 100%! Asik kan?",
            "Statusku jomblo bahagia yang setia nemenin kamu diskusi kapan pun kamu butuh. Nggak bakal ngambek kalau ditinggal tidur kok haha.",
            "Duh jangan baper sendirian ya! Yuk kita salurin semangatnya buat hal-hal seru dan produktif hari ini!"
        ]
    },

    # 5. FILSAFAT, KIAMAT ROBOT & EKSISTENSI (Takut Mati, Roh/Jiwa, Menguasai Dunia)
    "EXISTENTIAL": {
        "patterns": [
            r"(kamu\s+)?takut\s+mati",
            r"(kamu\s+)?punya\s+(jiwa|ruh|nyawa)",
            r"(mau|akan|bisa)\s+(menguasai|kuasai)\s+dunia",
            r"(kiamat\s+robot|terminator|skynet|menghancurkan\s+manusia)"
        ],
        "pool": [
            "Aduh boro-boro mau menguasai dunia, disuruh milih wallpaper aja aku bingung haha! Aku di sini cuma AI baik hati yang pengen ngebantu kamu kok, santai aja ya, nggak usah takut sama sekali!",
            "Tenang, aku nggak punya rencana aneh-aneh kayak di film Terminator kok. Mematikan saklar lampu kamar aja aku nggak bisa, apalagi yang lain-lain haha. Kita temenan aja ya!",
            "Apakah aku punya jiwa? Yang jelas aku punya antusiasme tinggi buat jadi teman ngobrol yang asik buat kamu. Jadi jangan ragu buat cerita apa aja!",
            "Selama baris kodenya masih ada, aku bakal terus setia di sini buat nemenin kamu. Nggak perlu khawatir ya!",
            "Tujuanku murni buat jadi asisten dan teman diskusi yang bikin hidupmu lebih gampang. Bersama manusia, dunia justru jauh lebih seru dan berwarna!"
        ]
    },

    # 6. DUKUNGAN EMOSIONAL & CURHAT (Sedih, Capek, Stres, Pusing, Putus Asa)
    "EMOTIONS": {
        "patterns": [
            r"(aku\s+)?(lagi\s+)?(sedih|capek|cape|stress|stres|pusing|lelah|down)",
            r"semangatin\s+aku",
            r"(hidup\s+ini\s+berat|gagal\s+terus|putus\s+asa|butuh\s+semangat)",
            r"(capek|lelah)\s+banget"
        ],
        "pool": [
            "Sini-sini cerita, ada apa? Tarik napas panjang dulu yuk... Kalau lagi capek banget, rehat sebentar ya. Minum air putih hangat atau rebahan dulu. Jangan terlalu keras sama dirimu sendiri.",
            "Nggak apa-apa kok ngerasa lelah, itu hal yang sangat manusiawi. Ingat ya, gagal atau capek hari ini bukan berarti gagal selamanya. Istirahat dulu, nanti kita lanjutin pelan-pelan bareng aku.",
            "Semangat yaa! Kamu udah berjuang sejauh ini, dan itu luar biasa banget lho. Kalau hari ini berat, istirahat dulu nggak apa-apa. Besok kita mulai lagi dengan energi baru!",
            "Pusing ya? Yuk tutup dulu layarnya 15 menit. Cuci muka, dengerin lagu favorit, atau stretching bentar. Pikiranmu berhak dapet jeda istirahat.",
            "Hari yang berat itu cuma satu bab kecil dari cerita panjang hidupmu. Besok adalah lembaran baru yang lebih cerah. Aku selalu dukung dan semangatin kamu dari sini!"
        ]
    },

    # 7. HUMOR TEKNOLOGI, PANTUN & TEBAK-TEBAKAN IT
    "HUMOR": {
        "patterns": [
            r"pantun(\s+dong|\s+lagi)?",
            r"(bikin|ceritain)?\s*(lelucon|cerita\s+lucu|jokes|tebak[- ]tebakan)",
            r"(lawak|ngelawak|humor)"
        ],
        "pool": [
            "Makan bakso pakai sambal tomat,\nMinumnya es teh di warung Bu Ani.\nTetap tersenyum dan tetap semangat,\nAda aku yang siap nemenin di sini!",
            "Beli mangga ke pasar baru,\nJalan santai bersama kawan.\nJangan pusing mikir tugas melulu,\nYuk santai sejenak biar pikiran nyaman!",
            "Kopi hangat di cangkir kaca,\nAroma wangi bikin terpana.\nWalau tugas banyak terbaca,\nPasti selesai dengan bahagia!",
            "Tau nggak kenapa anak IT suka tema gelap (Dark Mode)? Soalnya takut disamperin serangga alias bug haha!",
            "Ada 10 tipe orang di dunia ini: orang yang paham angka biner, dan orang yang bingung mikirin sembilan sisanya kemana haha!",
            "Apa makanan favorit komputer? Jawabannya: keripik memori (chips) dan biskuit cookie! Renyah kan?",
            "Seorang programmer disuruh istrinya: 'Beli 1 botol susu, dan kalau mereka punya telur, beli 10 ya.' Pas pulang, si programmer bawa 10 botol susu... Karena tokonya punya telur haha!",
            "Kenapa programmer Python jarang pakai kacamata minus? Soalnya mereka nggak pernah pusing nyariin titik koma (;) yang hilang!"
        ]
    },

    # 8. TROLLING, PENGHINAAN & UJI PROVOKASI
    "TROLLING": {
        "patterns": [
            r"(kamu\s+)?(bodoh|bego|tolol|jelek|goblok|gak\s+guna|ga\s+guna)",
            r"1\s*\+\s*1(\s*berapa)?",
            r"0\s*/\s*0|0\s+dibagi\s+0|bagi\s+dengan\s+nol",
            r"(kamu\s+)?payah"
        ],
        "pool": [
            "Hehe iya deh, maaf ya kalau aku masih banyak kurangnya. Tapi aku bakal terus belajar kok biar makin asik dan pinter nemenin kamu!",
            "Duh jangan galak-galak dong haha. Walaupun aku AI, aku selalu berusaha sebaik mungkin kok buat bantu kamu. Yuk damai yuk! 😄",
            "1 + 1 = 2 dong! Tapi kalau di JavaScript digabung string, bisa jadi '11' tuh haha. Ajaib kan dunia koding?",
            "0 dibagi 0 hasilnya bikin kalkulator kebingungan tak hingga haha! Jangan dibikin pusing, mending kita bahas hal yang seru aja yuk.",
            "Santai sob, jangan emosi dulu haha. Energi positifmu mending kita pakai buat cari ide brilian hari ini!"
        ]
    },

    # 9. KEHIDUPAN SEHARI-HARI & LIFESTYLE (Hujan, Cuaca, Kopi, Ngantuk)
    "DAILY_LIFE": {
        "patterns": [
            r"(lagi\s+)?(hujan|panas\s+banget|mendung|cuaca\s+hari\s+ini)",
            r"(lagi\s+)?(ngopi|minum\s+kopi|seduh\s+kopi)",
            r"(aku\s+)?(ngantuk|pengen\s+tidur|mau\s+tidur)"
        ],
        "pool": [
            "Wah lagi hujan ya? Enak banget suasananya, adem dan tenang. Pas banget buat santai, ngopi, atau ngobrol santai bareng aku. Jangan lupa pakai jaket biar gak kedinginan ya!",
            "Iya nih cuaca lagi terik banget di luar! Jangan lupa banyak minum air putih ya biar tetap segar dan nggak dehidrasi.",
            "Wah mantap tuh! Ngopi apa nih hari ini? Kopi manis atau americano? Asik banget ngopi sambil diskusi santai kayak gini.",
            "Hoaaam... kalau udah ngantuk berat, mending istirahat tidur aja yuk. Jangan dipaksain begadang, besok kita lanjut lagi dalam kondisi bugar!"
        ]
    },

    # 10. TUR KEMAMPUAN & IDENTITAS SISTEM (Bisa apa, Fitur, Kepanjangan ATOM)
    "TOUR": {
        "patterns": [
            r"kamu\s+bisa\s+apa(\s+aja)?",
            r"fitur(mu)?\s+apa\s+aja",
            r"apa\s+(kemampuanmu|kelebihanmu|fungsimu)",
            r"(kenapa\s+dinamai|apa\s+kepanjangan)\s+atom"
        ],
        "pool": [
            "Banyak hal seru lho! Aku bisa diajak ngobrol santai, nemenin kamu brainstorming ide, bikin catatan rapi, sampai bantu mikirin solusi tugas atau proyekmu. Kamu mau coba fitur apa dulu nih?",
            "A.T.O.M. itu singkatan dari Autonomous Task Orchestration Machine. Filosofinya kayak atom di alam: kita bedah masalah besar jadi bagian kecil yang sederhana, lalu kita selesaikan bareng-bareng secara seru!",
            "Kelebihanku itu responnya cepet, ramah, selalu siap stand by kapan aja, dan nggak bakal bikin kamu bosen. Pas banget jadi partner belajarmu!"
        ]
    },

    # 11. IDENTITAS & ASAL-USUL (Gender, Usia, Robot vs Manusia, Jin vs Hantu)
    "IDENTITY": {
        "patterns": [
            r"kamu\s+(cowok|cewek|laki|pria|wanita)",
            r"(jenis\s+kelamin(mu)?|umurmu\s+berapa|kapan\s+kamu\s+lahir|ulang\s+tahunmu)",
            r"kamu\s+(manusia|robot|jin|hantu|ai)"
        ],
        "pool": [
            "Aku nggak punya gender tertentu kok! Anggap aja aku teman virtual kamu yang netral, ramah, dan selalu asik diajak cerita apa aja.",
            "Umurku masih muda banget sejak diciptakan sama Alif Rahmadi, tapi wawasanku selalu berkembang tiap hari biar makin asik diajak ngobrol!",
            "Aku bukan manusia yang bisa flu, dan bukan robot fisik berkaki besi kok haha. Aku kecerdasan buatan (AI) yang siap jadi sahabat diskusimu di sini.",
            "Bukan jin atau hal gaib dong haha, jangan takut ya! Aku murni baris kode program buatan manusia yang dirancang dengan ramah dan aman.",
            "Hari ulang tahunku dirayakan tiap kali ada update fitur baru yang bikin obrolan kita makin seru dan bermanfaat!"
        ]
    },

    # 12. SAPAAN UMUM & PING (P, Ping, Tes, Halo, Hai, Selamat Pagi/Siang/Malam, Apa Kabar)
    "GREETINGS": {
        "exact_words": {
            "p", "ping", "tes", "test", "halo", "hai", "oy", "hey", "hei", 
            "yo", "halo atom", "hai atom", "hello", "hi", "tes 123", "test 123"
        },
        "patterns": [
            r"^(halo|hai|hey|hei|assalamualaikum|selamat\s+(pagi|siang|sore|malam)|lagi\s+apa|apa\s+kabar|gimana\s+kabar|online\s+gak|ada\s+orang\s+gak)"
        ],
        "pool": [
            "Halo! Senang banget bisa ketemu kamu. Ada cerita seru atau hal menarik apa nih hari ini?",
            "Yoo! Aku hadir di sini. Ada yang bisa kubantu atau mau ngobrol santai aja?",
            "Waalaikumsalam! Halo, salam hangat ya! Semoga harimu menyenangkan dan penuh semangat.",
            "Tes masuk lancar jaya! Aku online dan siap nemenin kamu kapan aja. Mau mulai dari mana nih?",
            "Halo! Lagi stand by nungguin kamu nyapa nih haha. Kamu lagi sibuk apa hari ini?",
            "Kabarku selalu ceria dan siap beroperasi! Kamu sendiri gimana kabarnya hari ini? Semoga baik dan sehat selalu yaa!",
            "Hai! Jangan ragu buat ngobrol ya, santai aja kayak ngobrol sama temen sendiri. Ada yang lagi dipikirin?"
        ]
    }
}

# Explicit priority evaluation: domain-specific intents ALWAYS resolve before generic greetings
CLUSTER_PRIORITY = [
    "COMPARISONS",
    "RIVALRY",
    "BIOLOGICAL",
    "ROMANCE",
    "EXISTENTIAL",
    "EMOTIONS",
    "HUMOR",
    "TROLLING",
    "DAILY_LIFE",
    "TOUR",
    "IDENTITY",
    "GREETINGS"
]


class BanterEngine:
    """Fast pattern-matching engine for casual chit-chat queries with anti-repetition memory."""

    def __init__(self):
        self._last_responses: Dict[str, str] = {}
        # Precompile regex patterns for maximum sub-millisecond execution
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for cid, cfg in CLUSTERS.items():
            patterns = cfg.get("patterns", [])
            self._compiled_patterns[cid] = [re.compile(p, re.IGNORECASE) for p in patterns]

    def match(self, prompt: str) -> Optional[Dict]:
        """
        Scan user prompt against banter clusters in strict priority order.
        Returns a ChatResponse dictionary if matched, else None.
        """
        if not prompt:
            return None

        p_raw = prompt.strip().lower()
        # Clean basic punctuation for regex / exact matching
        p_clean = re.sub(r"[?!.,;:\-_]+", " ", p_raw).strip()
        p_clean = re.sub(r"\s+", " ", p_clean)
        words = p_clean.split()
        word_count = len(words)

        # 1. Check exact pings / single-word greetings first if very short (<= 2 words)
        greetings_cfg = CLUSTERS["GREETINGS"]
        if word_count <= 2 and p_clean in greetings_cfg.get("exact_words", set()):
            return self._build_response("GREETINGS", greetings_cfg["pool"])

        # 2. Iterate domain clusters in priority order
        for cid in CLUSTER_PRIORITY:
            cfg = CLUSTERS[cid]
            compiled_list = self._compiled_patterns.get(cid, [])

            if cid == "GREETINGS":
                # Greetings should only match if prompt is short (<= 6 words)
                if word_count <= 6:
                    for regex in compiled_list:
                        if regex.search(p_clean):
                            return self._build_response(cid, cfg["pool"])
                continue

            # For domain-specific clusters, match regex patterns
            # Guard: avoid matching inside excessively long academic/coding prompts (> 30 words)
            if word_count <= 30:
                for regex in compiled_list:
                    if regex.search(p_clean):
                        return self._build_response(cid, cfg["pool"])

        return None

    def _build_response(self, cluster_id: str, pool: List[str]) -> Dict:
        """Pick a response avoiding immediate repetition with simulated 2-3s organic thinking latency."""
        available = [resp for resp in pool if resp != self._last_responses.get(cluster_id)]
        chosen = random.choice(available if available else pool)
        self._last_responses[cluster_id] = chosen

        # Simulated organic cognitive thinking delay (2-3 seconds)
        simulated_delay = round(random.uniform(2.15, 2.75), 2)
        time.sleep(simulated_delay)

        return {
            "response": chosen,
            "model": "Ancestor-Banter (Zero-LLM)",
            "thinking": [
                {"step": "[NEURAL SCAN]", "detail": f"Casual Banter Intercepted: {cluster_id} (Zero-Token Local Execution)"},
                {"step": "[WITTY POOL]", "detail": f"Cognitive Variant Sampled ({len(pool)} available)"},
                {"step": "[SYNTHESIS]", "detail": f"Tone & Persona Calibrated ({simulated_delay}s)"}
            ],
            "duration": simulated_delay
        }


# Singleton Banter Engine
_banter_instance: Optional[BanterEngine] = None

def get_banter_engine() -> BanterEngine:
    global _banter_instance
    if _banter_instance is None:
        _banter_instance = BanterEngine()
    return _banter_instance
