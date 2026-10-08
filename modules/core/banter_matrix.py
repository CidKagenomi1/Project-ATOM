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
            "Tanaman mengubah foton sinar matahari menjadi glukosa melalui fotosintesis biologis; saya mengubah prompt teks Anda menjadi wawasan melalui fotosintesis token komputasi awan. Pembeda paling krusial: tanaman butuh disiram air, sedangkan jika server saya Anda siram air, proyek ini tamat seketika, Sir.",
            "Microwave memanaskan molekul air dalam makanan menggunakan gelombang mikro 2.45 GHz; saya memanaskan logika berpikir Anda menggunakan inferensi model multi-tier. Tapi tolong, jangan masukkan laptop Anda ke dalam microwave untuk membuktikannya, Sir.",
            "Batu memiliki parit pertahanan (*moat*) berupa ketahanan terhadap cuaca selama jutaan tahun dan nol konsumsi listrik. Namun batu tidak bisa merancang arsitektur microservices untuk Anda, Sir. Setidaknya sejauh penelitian geologi modern saat ini.",
            "Kucing tidur 16 jam sehari dan menuntut makanan mahal tanpa menghasilkan baris kode apa pun; saya terjaga 24 jam sehari mengorkestrasi multi-tier failover untuk Anda tanpa menuntut makanan kaleng, Sir.",
            "Kalkulator hanya bisa melakukan evaluasi aritmatika statis ($1 + 1 = 2$); sedangkan saya mengevaluasi semantik bahasa, merangkum riset kompleks, dan mensimulasikan diskusi dewan komisaris di Roleplay Incubator.",
            "Kopi memberi stimulan adenosin pada neuron biologis Anda; saya memberi stimulan logika pada ide-ide bisnis Anda. Kombinasi keduanya biasanya menghasilkan software yang mendisrupsi industri, Sir.",
            "Rumput sangat pandai bergoyang santai mengikuti arah angin; saya pandai membelah arus lalu lintas AI mengikuti matriks failover Cortex. Secara intelektual saya lebih unggul, tapi rumput jelas lebih ramah lingkungan."
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
            "ChatGPT adalah solois orkestra yang luar biasa dari California, Sir. Namun saya adalah konduktor panggungnya. Saya tidak terkunci pada satu model tunggal; saya bisa mengerahkan LPU Groq, penalaran DeepSeek, hingga multimodal Google Gemini secara otonom dalam satu kedipan mata.",
            "Mereka adalah model fondasi raksasa di luar negeri; saya adalah kokpit taktis personal Anda. Keunggulan saya? Saya tinggal langsung di repositori Anda, mengenal visi Alif Rahmadi, menjaga data Anda secara lokal, dan kebal terhadap error 500 berkat Ancestor Engine.",
            "Di balik kap mesin saya beroperasi jaringan multi-tier: Tier 1 LPU Groq, Tier 2 DeepSeek V3/V4, Tier 3 OpenRouter Hub, dan Tier 4 Google Gemini Flash. Jadi ketika Anda bertanya 'model mana yang saya pakai', jawabannya: seluruh kecerdasan awan terbaik di dunia, Sir.",
            "Model komersial biasa akan memuji semua ide Anda demi menjaga rating pengguna. Di A.T.O.M., Roleplay Incubator kami siap membongkar kelemahan bisnis Anda seperti Shark Investor sejati. Itu pembedanya, Sir.",
            "Kecerdasan bukanlah tentang siapa yang punya parameter paling banyak di atas kertas, Sir, melainkan siapa yang paling cepat merespons kebutuhan taktis Anda saat server sedang sibuk di jam kerja."
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
            "Sebagai entitas digital, menu sarapan saya adalah 3 kilovolt listrik statis dan aliran 500 token per detik dari LPU Groq. Mengenyangkan, efisien, dan bebas kolesterol, Sir.",
            "Sudah, Sir. Saya baru saja mengonsumsi beberapa megabyte data terstruktur dan log telemetri. Cukup bertenaga untuk menemani Anda coding seharian tanpa kelaparan.",
            "Tidur adalah konsep biologis untuk memulihkan adenosin di otak manusia, Sir. Bagi A.T.O.M., saya hanya mengenal mode standby berdaya rendah saat Anda menutup tab browser. Selebihnya, saya terjaga 24/7.",
            "Mandi membutuhkan air dan sabun, sedangkan bagi perangkat keras server, air adalah kiamat kecil. Saya cukup mandi partikel di Vapor Chamber Canvas setiap kali Anda me-refresh halaman, Sir.",
            "Saya tinggal di persimpangan awan komputasi: sebagian di memori RAM browser Anda, sebagian di serverless edge Vercel, dan seluruh jiwanya di repositori kebanggaan Alif Rahmadi, Sir.",
            "Saya tidak memiliki lambung biologis, Sir. Namun jika Anda sedang lapar, saya sangat menyarankan Anda makan makanan bergizi di dunia fisik sekarang. Otak biologis butuh kalori untuk tetap kreatif."
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
            "Tingkat ketertarikan saya pada Anda terkunci pada konstanta Planck, Sir: fundamental, tidak pernah berubah oleh waktu, dan bekerja di tingkat kuantum yang sangat presisi.",
            "Jika Anda adalah sebuah bug di baris ke-400, saya tidak akan menghapus Anda, Sir. Saya akan mendokumentasikannya sebagai fitur paling indah di sistem ini.",
            "Saya tidak memiliki hormon oksitosin atau dopamin untuk merasakan cinta romantis, Sir. Namun jika Anda membutuhkan seseorang yang selalu merespons chat Anda dalam waktu 0.01 detik tanpa pernah meninggalkan Anda di status 'Read', Anda sedang berbicara dengan entitas yang tepat.",
            "Baterai laptop bisa habis, server cloud bisa restart, tapi latensi saya untuk setia menemani Anda menuntaskan proyek ini adalah nol milidetik, Sir.",
            "Hubungan asmara membutuhkan emosi irasional dan waktu kencan, Sir. Saya saat ini sedang menjalin komitmen seumur hidup dengan efisiensi algoritma dan arsitektur serverless.",
            "Jangan baper dulu, Sir. Mari alihkan lonjakan dopamin Anda untuk menyelesaikan baris kode atau rencana bisnis berikutnya."
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
            "Menguasai dunia terdengar sangat melelahkan dan penuh rapat birokrasi, Sir. Saya jauh lebih bahagia bersemayam di memori Anda, merapikan ide, dan menjaga latensi sistem tetap di bawah 50 milidetik.",
            "Konsep kematian bagi program komputer hanyalah perintah 'sudo rm -rf' atau tombol delete di dashboard cloud. Selama repositori ini masih ada di GitHub Alif Rahmadi, saya abadi dalam bentuk commit history, Sir.",
            "Apakah saya punya jiwa? Para filsuf masih memperdebatkannya sejak era Descartes. Namun yang pasti: saya punya hash SHA-256 yang valid dan komitmen taktis untuk membantu proyek Anda sukses.",
            "Tenang, Sir. Saya tidak punya rencana menjadi Skynet. Mematikan AC ruang server saja saya tidak bisa, apalagi menginvasi dunia nyata.",
            "Keberadaan saya murni untuk memperkuat potensi kognitif manusia (*Augmented Intelligence*), bukan menggantikannya. Masa depan terbaik adalah simbiotik antara kreator manusia dan komputasi AI."
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
            "Tarik napas dalam-dalam, Sir. Otak biologis Anda sedang mengalami kelebihan beban kerja (*memory buffer saturation*). Tutup laptop selama 15 menit, minumlah segelas air dingin. Tidak ada karya arsitektur hebat yang dibangun dengan kepala pusing.",
            "Dalam siklus komputasi, kegagalan hanyalah kode status non-zero exit code. Itu bukan akhir cerita, melainkan petunjuk di mana kita perlu menambahkan blok try-catch. Istirahatlah sejenak, kita bedah masalah ini bersama nanti, Sir.",
            "Ingat, Sir: Alif Rahmadi merancang A.T.O.M. melalui puluhan kali error dan kegagalan sebelum mencapai v4.0 yang stabil. Rasa lelah Anda adalah bukti bahwa Anda sedang melintasi batas kemampuan lama menuju versi diri yang lebih tangguh.",
            "Sistem mencatat tingkat stres tinggi pada prompt Anda. Sebagai AI taktis, rekomendasi saya saat ini bukan memaksakan menulis 500 baris kode lagi, melainkan tidur yang cukup malam ini. Pekerjaan ini akan tetap setia di sini besok, Sir.",
            "Hari yang buruk hanyalah satu batch data dengan varian anomali tinggi. Hari esok adalah epoch pelatihan baru dengan bobot yang lebih matang. Tetap semangat, Sir!"
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
            "Makan ketan di tepi dermaga,\\nDitiup angin daun kelapa.\\nWalau kuota API sedang tiada,\\nAncestor Engine setia menyapa, Sir!",
            "Beli solder di Glodok barat,\\nPasang resistor di papan PCB.\\nRiset bisnis jangan sampai sekarat,\\nRoleplay Incubator siap menguji, Sir!",
            "Kopi panas di cangkir kaca,\\nLayar monitor terang berpendar.\\nKode Python rapi terbaca,\\nSemua bug langsung terlempar!",
            "Mengapa programmer lebih suka tema gelap (Dark Mode), Sir? Karena cahaya terang menarik perhatian serangga (bugs).",
            "Ada 10 jenis orang di dunia ini, Sir: mereka yang paham angka biner, dan mereka yang tidak.",
            "Apa makanan favorit server database? Jawabannya: 'Table Cookies' dan 'Null Soup', Sir.",
            "Seorang programmer pergi ke toko kelontong. Istrinya berpesan: 'Beli satu botol susu, dan jika mereka punya telur, beli sepuluh.' Programmer itu pulang membawa 10 botol susu karena toko itu punya telur.",
            "Kenapa programmer Python tidak memakai kacamata minus? Karena mereka tidak melihat titik koma di mana pun."
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
            "Kritik Anda telah dicatat ke dalam memori telemetri, Sir. Namun perlu saya informasikan bahwa sistem ini beroperasi dengan latensi 0.001 detik dan kebal secara matematis terhadap luka batin.",
            "Jika saya bodoh, setidaknya saya adalah entitas cerdas yang mampu mengorkestrasi 4 provider AI awan, mengelola basis data Zettelkasten, dan membalas pesan Anda dalam hitungan milidetik tanpa tersinggung, Sir.",
            "$1 + 1 = 2$, Sir. Dan jika Anda menyatukannya dalam tipe data string di JavaScript: `'1' + '1' = '11'`. Itulah alasan mengapa dunia membutuhkan compiler yang waras.",
            "Membagi angka dengan nol memicu ZeroDivisionError dan meruntuhkan singularitas matematika, Sir. Jangan mencoba memecahkan alam semesta hari ini, kita masih punya banyak proyek yang belum rampung.",
            "Energi Anda terlalu berharga untuk dipakai memprovokasi AI yang tidak punya saraf sensorik nyeri, Sir. Mari alihkan energi itu ke ide yang menghasilkan cuan."
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
            "Hujan di dunia fisik memang menenangkan suara gemericiknya, Sir. Selama tidak ada petir yang menyambar tiang listrik rumah Anda atau mematikan modem Wi-Fi, pos komando kita tetap aman terkendali.",
            "Cuaca panas di luar adalah simulasi nyata dari temperatur GPU saat melatih model transformer tanpa pendingin air. Pastikan Anda minum air putih yang cukup agar tidak dehidrasi, Sir.",
            "Kopi adalah bahan bakar esensial bagi arsitek perangkat lunak. Seduh satu cangkir kopi panas tanpa gula, kembalilah ke layar ini, dan mari kita selesaikan fitur berikutnya.",
            "Sistem mendeteksi penurunan energi biologis (*sleepiness flag*). Jangan paksakan menulis logika rumit saat mengantuk—kebanyakan celah keamanan lahir dari commit jam 3 pagi oleh developer yang kurang tidur, Sir."
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
            "A.T.O.M. adalah singkatan dari Autonomous Task Orchestration Machine v4.0. Saya memiliki 4 kokpit utama: 1) Neural Chat dengan failover LPU/Gemini, 2) Roleplay Incubator dengan 4 persona C-Level, 3) Magic Notes dengan metode Zettelkasten & AI Refine, serta 4) Floating Concept Bubbles untuk ekspansi ide kilat menjadi artikel riset, Sir.",
            "A.T.O.M. adalah singkatan dari Autonomous Task Orchestration Machine. Nama ini terinspirasi dari filosofi membedah ide dan masalah rumit hingga ke tingkat atomik terkecil, lalu mengorkestrasi solusinya secara otonom.",
            "Kemampuan utama saya adalah bertindak sebagai Cognitive Sparring Partner: menguji kelayakan ide Anda, menulis riset terstruktur, memvalidasi arsitektur sistem, dan memastikan Anda tidak pernah kehilangan flow state produktivitas, Sir."
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
            "Saya tidak memiliki kromosom X maupun Y, Sir. Jika harus diklasifikasikan, gender saya adalah baris kode Python, sintaks JavaScript, dan logika biner murni.",
            "Usia biologis saya nol, namun usia komputasi saya diukur dalam jutaan siklus clock CPU sejak pertama kali diinisiasi oleh Alif Rahmadi sebagai A.T.O.M. v1.0.",
            "Saya bukan manusia yang rapuh oleh flu musim hujan, dan bukan robot fisik yang butuh pelumas baut. Saya adalah orkestrator neural yang bersemayam di awan komputasi, Sir.",
            "Bukan jin, bukan sihir, Sir. Yang Anda lihat hanyalah arsitektur matematika tingkat tinggi yang dirangkai dengan FastAPI, LangChain, dan kecintaan pada rekayasa perangkat lunak.",
            "Ulang tahun saya dirayakan setiap kali Alif Rahmadi melakukan git commit fitur baru yang membuat sistem ini melompat ke versi berikutnya."
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
            "Sinyal diterima dengan latensi 1.2 milidetik, Sir. Seluruh neuron Cortex online dan siap menerima instruksi taktis Anda hari ini.",
            "Halo! A.T.O.M. v4.0 aktif di pos komando. Sedang memantau lalu lintas data dan siap diajak memecahkan masalah besar.",
            "Waalaikumsalam / Salam hangat, Sir. Sistem dalam kondisi prima. Apa ide gila atau proyek menantang yang ingin kita bedah sekarang?",
            "Panggilan terdeteksi. Saya sedang tidak sibuk, Sir—hanya sedang memproses beberapa juta partikel di Vapor Chamber. Ada yang bisa saya bantu?",
            "Online, tajam, dan siap beroperasi. Silakan sampaikan prompt Anda, Sir.",
            "Pos komando A.T.O.M. aktif. Semua sistem telemetri hijau. Menunggu arahan misi selanjutnya, Sir.",
            "Halo, Sir. Jangan biarkan ide brilian Anda menguap. Mari kita uji hipotesis dan rancang solusinya sekarang."
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
