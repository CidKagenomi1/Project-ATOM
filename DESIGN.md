# ⚛️ A.T.O.M. Design System & Style Guide (`DESIGN.md`)

> **"I am not just a chatbot, Sir. I am a Neural Orchestrator."**  
> *Versi Desain: 4.8 (Midnight Matte-Glassmorphism, Vercel/Linear Precision & Anti-Glow)*  
> *Status: Official Design Standard & Blueprint*

---

## 📑 Daftar Isi
1. [Filosofi & Root Design DNA](#1-filosofi--root-design-dna)
2. [Prinsip Anti-Glow & Presisi Taktis (The Low-Glow Rule)](#2-prinsip-anti-glow--presisi-taktis-the-low-glow-rule)
3. [Standar Visual Vercel & Linear Precision (The Modern Monolith)](#3-standar-visual-vercel--linear-precision-the-modern-monolith)
4. [Design Tokens & Sistem Variabel](#4-design-tokens--sistem-variabel)
5. [Palet Warna & Spektrum Reaktor](#5-palet-warna--spektrum-reaktor)
6. [Tipografi & Font Hierarchy](#6-tipografi--font-hierarchy)
7. [Formula Glassmorphism, Elevasi & Kedalaman](#7-formula-glassmorphism-elevasi--kedalaman)
8. [Sistem Spacing, Grid & Density Modes](#8-sistem-spacing-grid--density-modes)
9. [Standar Komponen Inti (UI Component Library)](#9-standar-komponen-inti-ui-component-library)
10. [Gerak, Partikel & Mikro-Animasi (Motion Principles)](#10-gerak-partikel--mikro-animasi-motion-principles)
11. [Bespoke Theme Modes (Skins Matrix)](#11-bespoke-theme-modes-skins-matrix)
12. [Panduan Desain Responsif & Kepadatan Layar](#12-panduan-desain-responsif--kepadatan-layar)
13. [Aturan Emas: Do's & Don'ts (Anti-Patterns)](#13-aturan-emas-dos--donts-anti-patterns)
14. [Checklist Verifikasi Implementasi Baru (QA)](#14-checklist-verifikasi-implementasi-baru-qa)

---

## 1. Filosofi & Root Design DNA

A.T.O.M. (Autonomous Task Orchestration Machine) dirancang dengan metafora **Konsol Laboratorium Fisika Presisi & Neural AI Cockpit**. 

Bukan aplikasi fiksi ilmiah murahan yang penuh efek lampu neon menyilaukan (*tacky sci-fi glow*), A.T.O.M. mengadopsi estetika **Tactical Luxury & Stealth Hardware**: tenang, berwibawa, tajam, dan tidak melelahkan mata (*zero visual fatigue*).

```
┌────────────────────────────────────────────────────────────────────────┐
│                          A.T.O.M. DESIGN DNA                           │
├────────────────────┬───────────────────┬───────────────┬───────────────┤
│ 1. MIDNIGHT VOID   │ 2. TACTICAL CORE  │ 3. VERCEL /   │ 4. CLASSICAL  │
│    (Deep Stealth)  │    (Matte Accent) │    LINEAR PREC│    HUMAN TOUCH│
├────────────────────┼───────────────────┼───────────────┼───────────────┤
│ Latar hitam pekat  │ Garis aksen emas  │ Hairline      │ Tipografi     │
│ (#000000) dengan   │ reaktor presisi   │ border 1px,   │ kaligrafi     │
│ akrilik satin matte│ tanpa kabut glow  │ tight font,   │ anggun untuk  │
│ yang tenang        │ menyilaukan       │ monokrom rapi │ sentuhan jiwa │
└────────────────────┴───────────────────┴───────────────┴───────────────┘
```

---

## 2. Prinsip Anti-Glow & Presisi Taktis (The Low-Glow Rule)

Salah satu kesalahan umum desain dark-mode bernuansa futuristik adalah **kebocoran efek glow berlebihan** (*box-shadow fuzzy halo*, *text-shadow* menyala, *cursor flashlight* yang mengganggu konsentrasi). Hal tersebut membuat antarmuka terasa kekanak-kanakan, mengaburkan keterbacaan teks, dan membuat mata perih.

### 2.1. Hirarki Cahaya: Kapan Glow Boleh Digunakan?
| Kategori Elemen | Status Glow | Pengganti / Solusi yang Benar |
| :--- | :--- | :--- |
| **Kartu & Panel (Cards)** | ❌ **DILARANG KERAS** | Gunakan *hairline border* (`rgba(255,255,255,0.08)`) dan transisi warna border tajam saat hover. |
| **Judul & Teks (Typography)** | ❌ **DILARANG KERAS** | Tidak boleh ada `text-shadow` glow. Kontras warna teks murni (`#ffffff` / `#E6EDF3`) jauh lebih bersih dan tajam. |
| **Tombol (Buttons)** | ❌ **TIDAK ADA HALO** | Gunakan gradien solid halus dan perubahan elevasi (`translateY(-1px)`), bukan kabut cahaya di sekeliling tombol. |
| **Input Bar Obrolan** | ❌ **MINIMALIS** | Cukup `border-color: var(--gold-primary)` tipis saat fokus, tanpa lingkaran pendar menyebar. |
| **Micro-LED / Status Dot** | ✅ **DIIZINKAN (Micro)** | Boleh memiliki pendar mikro sangat kecil (radius `3px – 6px`) untuk menandakan indikator live status (Ollama/Groq Online). |

### 2.2. Mengapa Tampilan Matte Lebih Berkelas?
* **Ketajaman Informasi:** Mata pengguna langsung fokus pada konten (hasil analisis data, ringkasan riset, baris kode), bukan terdistraksi oleh kabut cahaya buatan.
* **Estetika Hardware Premium:** Menyerupai perangkat audio profesional tingkat studio (seperti Teenage Engineering atau instrumen laboratorium presisi tinggi).

---

## 3. Standar Visual Vercel & Linear Precision (The Modern Monolith)

Mengikuti standar visual **Vercel** dan **Linear Design System**, antarmuka A.T.O.M. mengedepankan presisi monolit, keterbacaan mutlak, dan interaksi taktil yang tenang:

### 3.1. Empat Pilar Visual Vercel & Linear di A.T.O.M.
1. **Latar Matte Pekat (Obsidian Black Depth):**
   * Dasar antarmuka menggunakan hitam pekat `#000000` dengan layer elevasi bernuansa matte dingin (`rgba(14, 18, 24, 0.65)` – `rgba(18, 22, 28, 0.75)`).
   * Efek tembus pandang dikendalikan oleh *heavy backdrop-filter blur* (`blur(24px) saturate(160%)`) yang menghasilkan tekstur kaca satin akrilik, bukan kaca transparan tipis.
2. **Sub-Pixel Hairline Borders:**
   * Garis pembatas kontainer dibuat setipis rambut (`1px solid rgba(255, 255, 255, 0.08)` atau `var(--border-color)`).
   * Hirarki visual dibangun melalui kejernihan garis batas, bukan tumpukan bayangan blur yang keruh.
3. **Tipografi Tajam dengan Spasi Rapat (Geist / Inter Tight Tracking):**
   * Menggunakan tipografi modern sans-serif berpresisi tinggi (`Inter`, `Geist Sans`, `system-ui`).
   * Mengaplikasikan *negative letter-spacing* agar teks terlihat padat, tegas, dan berwibawa:
     * Display Title (`.atom-title`): `letter-spacing: -0.04em` hingga `-0.05em`.
     * Card Title & Headline (`.suggestion-title`, `h3`): `letter-spacing: -0.02em`.
     * Subtitle & Body (`.atom-subtitle`, `p`): `letter-spacing: -0.01em` hingga normal.
   * Judul utama menggunakan gradien vertikal tajam dari putih murni ke putih metalik (`linear-gradient(180deg, #FFFFFF 0%, rgba(255, 255, 255, 0.62) 100%)`) tanpa text-shadow glow.
4. **Interaksi Monokrom & Taktil (Monochrome Minimalism):**
   * Tombol aksi dan kartu saran menggunakan palet monokrom minimalis (bingkai ikon netral, tag kategori abu-abu redup, panah indikator halus).
   * Respon hover mengandalkan:
     * Mikro-elevasi fisik: `transform: translateY(-2px);`
     * Penguatan hairline border: bertransisi ke `rgba(255, 255, 255, 0.22)` atau aksen tema.
     * Animasi pergeseran panah: `transform: translateX(3px);`
     * Pantulan cahaya tepi atas yang halus: `box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.10);`

---

## 4. Design Tokens & Sistem Variabel

Semua nilai visual wajib mengacu pada CSS Variables resmi di `:root` ([`public/assets/css/main.css`](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/public/assets/css/main.css)).

```css
:root {
  /* ── Background Stack (Kedalaman Satin Matte) ── */
  --bg-base:        #000000;                /* Layer 0: Void dasar pekat */
  --bg-surface:     rgba(10, 10, 10, 0.45);  /* Layer 1: Panel & Sidebar */
  --bg-elevated:    rgba(18, 18, 18, 0.55);  /* Layer 2: Kartu, Input, Bubble */
  --bg-hover:       rgba(30, 30, 30, 0.65);  /* State: Interaksi hover */
  --bg-active:      rgba(45, 45, 45, 0.75);  /* State: Aktif / Pressed */

  /* ── Nuclear Gold Core (Tactical Precision) ── */
  --gold-primary:   #ebb338;                /* Aksen emas utama: garis presisi, ikon aktif */
  --gold-light:     #f6d365;                /* Teks aksen tajam (tanpa text-shadow) */
  --gold-dark:      #8a6715;                /* Border halus pembatas */
  --gold-glow:      rgba(235, 179, 56, 0.08);/* Redup & terkontrol (hanya untuk LED status) */
  --text-gold:      #f6d365;
  --border-gold:    rgba(235, 179, 56, 0.35);

  /* ── Tipografi Teks Standar ── */
  --text-primary:   #E6EDF3;                /* Kontras tinggi & tajam */
  --text-secondary: #8B949E;                /* Keterangan, label, meta teks */
  --text-muted:     #6b7280;                /* Placeholder, info sekunder */

  /* ── Hairline Border Presisi ── */
  --border-color:   rgba(255, 255, 255, 0.08);

  /* ── Warna Semantik Status ── */
  --success:        #3FB950;
  --success-bg:     rgba(63, 185, 80, 0.08);
  --error:          #F85149;
  --error-bg:       rgba(248, 81, 73, 0.08);
  --warning:        #E3B341;
  --warning-bg:     rgba(227, 179, 65, 0.08);
  --info:           #58A6FF;
  --info-bg:        rgba(88, 166, 255, 0.08);

  /* ── Skala Kelengkungan (Border Radius) ── */
  --radius-sm:      6px;                    /* Chip kecil, tag, badge */
  --radius-md:      8px;                    /* Tombol kecil, dropdown menu */
  --radius-lg:      12px;                   /* Kartu saran, bubble chat, input bar */
  --radius-xl:      16px;                   /* Dialog modal, hero card */
  --radius-full:    9999px;                 /* Pills, avatar, circular buttons */

  /* ── Glassmorphism Matte Standar ── */
  --glass-backdrop: blur(24px) saturate(160%);
  --glass-border:   1px solid rgba(255, 255, 255, 0.08);
  --glass-shadow:   0 8px 32px 0 rgba(0, 0, 0, 0.70), inset 0 1px 0 0 rgba(255, 255, 255, 0.08);

  /* ── Dimensi Kerangka (Shell Layout) ── */
  --sidebar-width:  260px;
  --topbar-height:  60px;
  --max-content:    900px;
}
```

---

## 5. Palet Warna & Spektrum Reaktor

### 5.1. Reaktor Inti: Nuclear Gold (Signature)
Aksen emas hadir sebagai penanda fokus (*precision indicator*), bukan lampu neon yang menyilaukan.
* **Hex Primer:** `#ebb338` (Titik fokus, icon, garis aktif).
* **Hex Pijar:** `#f6d365` (Teks judul tajam dan elegan).
* **Hex Pembatas:** `#8a6715` (Garis tepi tipis).

### 5.2. Aksen Spektrum Alternatif (Dynamic Color Modes)
| Nama Tema Aksen | Primary | Light Accent | Karakter Visual |
| :--- | :--- | :--- | :--- |
| **Nuclear Gold** *(Default)* | `#ebb338` | `#f6d365` | Karakter asli A.T.O.M. Hangat, berkelas, reaktor atom. |
| **Quantum Cyan** | `#00d2ff` | `#80e5ff` | Nuansa kriogenik, bersih, dingin dan fokus. |
| **Void Violet** | `#b026ff` | `#d946ef` | Deep intelligence, neural exploration. |
| **Matrix Emerald** | `#00ff9d` | `#6ee7b7` | Terminal presisi, bio-sensorik, status aman. |
| **Crimson Red** | `#ff4757` | `#ff6b81` | Mode audit intensif, parameter kritis. |
| **Platinum Silver** | `#e2e8f0` | `#ffffff` | Stealth monolit murni, minimalis absolut tanpa distorsi warna. |

---

## 6. Tipografi & Font Hierarchy

A.T.O.M. memadukan **ketegasan sans-serif modern** dengan **kaligrafi personal**:

```
   ┌─────────────────────────────────────────────────────────┐
   │                    FONT ROSTER A.T.O.M.                 │
   ├────────────────┬────────────────────────────────────────┤
   │ Brand / Title  │ Palace Script MT / Pinyon Script       │
   │ UI Navigation  │ Outfit (Geometric, Crisp, Tech)        │
   │ Reading / Chat │ Inter / Geist Sans (Tight Tracking)    │
   │ Code & Data    │ JetBrains Mono / Fira Code             │
   │ Retro Mode     │ VT323 (8-bit Monospace Phosphor)       │
   │ Claude Mode    │ Newsreader (Editorial Serif)           │
   └────────────────┴────────────────────────────────────────┘
```

### 6.1. Skala Tipografi & Letter-Spacing Baku
* **Hero Title (Display):** `clamp(2.5rem, 5.5vw, 4.2rem)` — Inter/Geist 800, `letter-spacing: -0.05em`, Line-height `1.02`. **Bebas text-shadow tebal**.
* **Page / Section Title (`h1`, `h2`):** `1.5rem` – `2.0rem` — Outfit 700, `letter-spacing: -0.02em`.
* **Card Header (`h3`, `.suggestion-title`):** `0.88rem` – `1.05rem` — Inter/Outfit 600, `letter-spacing: -0.02em`.
* **Body Text (`p`, `.message-bubble`):** `0.88rem` – `0.90rem` — Inter 400, Line-height `1.6`, `letter-spacing: -0.01em`.
* **Compact / Meta (`.settings-detail`, `.meta-info`):** `0.78rem` – `0.82rem` — Color `--text-muted`.
* **Micro Label / Badge (`.hero-badge`, `.suggestion-tag`):** `0.67rem` – `0.72rem` — Font Mono/UI, Uppercase, Weight 500–600, `letter-spacing: 0.05em–0.08em`.

---

## 7. Formula Glassmorphism, Elevasi & Kedalaman

Karakter kaca A.T.O.M. mengadopsi prinsip **akrilik satin matte**—bukan kaca transparan tembus pandang murahan dengan bayangan glow kabur.

### 7.1. Resep Baku Kaca A.T.O.M. (The Clean Satin Glass Formula)

```css
/* Resep Baku Kartu Kaca ATOM (Bebas Efek Glow Silau) */
.atom-glass-card {
  background: rgba(14, 18, 24, 0.75);           /* Tint gelap dingin */
  border: 1px solid rgba(255, 255, 255, 0.08);  /* Hairline border presisi */
  border-radius: var(--radius-xl);              /* 16px curve */
  backdrop-filter: blur(20px) saturate(160%);   /* Blur tajam + kejernihan optik */
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  box-shadow: 
    0 8px 30px 0 rgba(0, 0, 0, 0.65),           /* Bayangan kedalaman fisik */
    inset 0 1px 0 0 rgba(255, 255, 255, 0.08);  /* Pantulan halus tepi atas */
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Hover State: Responsif Lewat Border, BUKAN Glow Halo */
.atom-glass-card:hover {
  border-color: rgba(235, 179, 56, 0.38);       /* Garis emas mengunci perhatian */
  box-shadow: 
    0 12px 36px 0 rgba(0, 0, 0, 0.75),           /* Sedikit elevasi fisik */
    inset 0 1px 0 0 rgba(255, 255, 255, 0.14);  /* Pantulan tepi menguat tipis */
  transform: translateY(-2px);                  /* Mikro-elevasi taktil */
}
```

---

## 8. Sistem Spacing, Grid & Density Modes

### 8.1. Skala Spasi Baku (8pt Based Grid)
* `--space-1`: `0.25rem` (4px) — micro-gap antar ikon dan teks.
* `--space-2`: `0.5rem` (8px) — padding badge, gap item kecil.
* `--space-3`: `0.75rem` (12px) — padding gelembung chat vertikal.
* `--space-4`: `1.0rem` (16px) — standar padding kartu kecil, margin form.
* `--space-5`: `1.25rem` (20px) — padding kartu utama (`.settings-card`).
* `--space-6`: `1.5rem` (24px) — pemisah section konten.
* `--space-8`: `2.0rem` (32px) — padding header hero.

### 8.2. Dual Density Modes
1. **Standard Mode (Default):** Padding lega untuk layar desktop lebar.
2. **Compact Density Mode (`body.compact-mode`):** Mengurangi padding sebesar 30-35% sehingga laptop resolusi 1366×768 mampu menampilkan lebih banyak baris konten tanpa scrolling konstan.

---

## 9. Standar Komponen Inti (UI Component Library)

### 9.1. Gelembung Obrolan (Chat Bubbles)
* **Pesan Pengguna (`.chat-message.user`):**
  * Posisi: Kanan (*Right-aligned*).
  * Latar: `rgba(235, 179, 56, 0.10)`.
  * Border: `1px solid rgba(235, 179, 56, 0.30)`.
  * Radius: `16px 16px 4px 16px`.
* **Pesan Asisten A.T.O.M. (`.chat-message.assistant`):**
  * Posisi: Kiri (*Left-aligned*).
  * Latar: `rgba(18, 22, 28, 0.65)`.
  * Border: `1px solid rgba(255, 255, 255, 0.08)`.
  * Radius: `16px 16px 16px 4px`.
  * Tanpa bayangan menyala, teks tajam kontras tinggi.

### 9.2. Tombol Aksi (Buttons)
1. **Tombol Primer (`.btn-primary` / `.btn-send`):**
   * Latar: `linear-gradient(135deg, #ebb338, #c99318)`.
   * Teks: `#0a0a0a` (Kontras solid mudah dibaca).
   * Hover: Mikro-elevasi `transform: translateY(-1px)`, border kontras. **Tidak ada kabut glow tebal di sekeliling tombol.**
2. **Tombol Sekunder / Ghost (`.btn-ghost`):**
   * Latar: `rgba(255, 255, 255, 0.04)`.
   * Border: `1px solid rgba(255, 255, 255, 0.10)`.
   * Hover: Latar `rgba(255, 255, 255, 0.08)`, border `var(--gold-primary)`.

### 9.3. Area Input Obrolan Kapsul Melayang (`.chat-input-wrapper`)
* Kapsul kaca satin melayang di bagian bawah dengan backdrop blur tebal (`blur(30px)`).
* Border hairline presisi `1px solid var(--border-color)`.
* **Focus State yang Bersih:** Saat pengguna mengetik, border bertransisi tajam menjadi `rgba(235, 179, 56, 0.6)` secara presisi **tanpa menyebarkan halo cahaya besar** yang mengganggu mata.

### 9.4. Area Sambutan (Hero Welcome & Capabilities Status Bar)
* **Micro-Badge (`.hero-badge`):** Kapsul mono minimalis dengan hairline border dan titik indikator reaktor.
* **Display Title (`.atom-title`):** Huruf A.T.O.M. tebal berspasi rapat (`-0.05em`) dengan gradien putih metalik vertikal dan tanpa text-shadow.
* **Subtitle Deskriptif (`.atom-subtitle`):** Penjelasan fungsional ringkas dengan warna `var(--text-secondary)`.
* **Kapsul Status Model (`.atom-status-bar`):** Status bar horizontal satin matte yang menampung indikator ringkas untuk `Local AI`, `Cloud AI`, `CrewAI`, dan `Fallback Gemini`. Terintegrasi dengan titik mikro LED status.

### 9.5. Kartu Aksi Cepat / Prompt Suggestions (`.suggestions-grid` & `.suggestion-card`)
Mengikuti pola kartu Vercel / Linear untuk memandu interaksi pertama pengguna:
* **Layout:** Grid 2 kolom seimbang (otomatis 1 kolom di layar mobile).
* **Struktur Kartu:**
  1. **Header:** Bingkai ikon kotak monokrom (`26×26px`) + Label kategori monospace (`.suggestion-tag`) + Panah aksi interaktif (`.suggestion-arrow`).
  2. **Judul:** Teks tebal tajam (`0.88rem`, `letter-spacing: -0.02em`).
  3. **Deskripsi:** Teks ringkas yang menjelaskan hasil yang akan diberikan (`0.77rem`, warna `var(--text-secondary)`).
* **Fisika Hover:** `translateY(-2px)`, border menegas ke `rgba(255, 255, 255, 0.22)`, dan panah bergeser `translateX(3px)` secara mulus.

### 9.6. Status Dots & Provider Indicator
* **Online (Hijau):** `#3FB950`, kedip mikro lembut (*subtle breathing*).
* **Processing (Emas):** `#ebb338`, indikator putaran kecil.
* **Offline (Merah):** `#F85149`, statis tanpa pendar.

---

## 10. Gerak, Partikel & Mikro-Animasi (Motion Principles)

Gerakan di A.T.O.M. bersifat **organik, tenang, dan efisien**:
1. **Kurva Gerak Alami:** `cubic-bezier(0.16, 1, 0.3, 1)` untuk seluruh interaksi elemen.
2. **Vapor Chamber Particles:** Simulasi peluruhan latar belakang bergerak halus dan transparan (`opacity: 0.15 – 0.30`) sehingga menjadi tekstur atmosferik yang tenang, bukan kembang api menyala.
3. **Electron Spin:** Orbit elektron pada logo SVG berputar kontinu dengan durasi tidak sinkron (`3.2s`, `4.0s`, `4.8s`).
4. **Performance Toggle:** Animasi partikel dan rotasi atom dapat dimatikan di Halaman Pengaturan untuk penghematan daya penuh.

---

## 11. Bespoke Theme Modes (Skins Matrix)

| Nama Tema UI | Inspirasi Desain | Tipografi Khusus | Karakteristik Visual |
| :--- | :--- | :--- | :--- |
| **ATOM Cyber** *(Default)* | Reaktor Nuklir Taktis | Outfit + Inter | Glassmorphism satin pekat, hairline border presisi, aksen emas matte. |
| **ChatGPT Likes** | OpenAI Dashboard | System Sans-serif | Charcoal minimalis `#212121`, gelembung pil bulat penuh, hijau OpenAI `#10a37f`. |
| **Claude Likes** | Anthropic Claude | Newsreader (Serif) | Warna arang hangat `#262320`, tipografi sastra berbobot, aksen terrakota `#DA7756`. |
| **WhatsApp Likes** | Web Messenger | Segoe UI / System | Dark teal `#0b141a`, bubble dengan ekor (*speech tail*), aksen hijau WA `#25d366`. |
| **Retro Pixelated** | 8-Bit Arcade CRT | VT323 (Monospace) | Sudut tajam 0px, hijau fosfor `#00ff66`, efek scanline arcade. |

---

## 12. Panduan Desain Responsif & Kepadatan Layar

```
Desktop Lebar (> 1200px) ───► Sidebar Statis 260px + Konten Maksimal 900px + Grid Saran 2 Kolom
Laptop Kompak (992px - 1199px)► Layout Merapat, Density Efisien
Tablet (768px - 991px)   ───► Sidebar Collapsible, Toggle via Hamburger
Mobile Smartphone (< 768px) ──► Fullscreen Sheet, Drawer Sidebar, Bottom Floating Input, Grid Saran 1 Kolom
```

---

## 13. Aturan Emas: Do's & Don'ts (Anti-Patterns)

### ✅ Hal yang WAJIB Dilakukan (DO's)
* Gunakan **hairline border** (`1px solid rgba(...)`) untuk mendefinisikan batas elemen.
* Terapkan **tight letter-spacing** (`-0.02em` s/d `-0.05em`) pada display title dan kartu aksi untuk ketajaman modern ala Vercel/Linear.
* Jaga kontras teks tinggi (`#ffffff` / `#E6EDF3`) agar selalu terbaca tajam tanpa perlu bantuan text-shadow.
* Gunakan transisi halus (`0.2s cubic-bezier`) untuk interaksi hover/focus.
* Batasi pendar cahaya hanya pada **indikator mikro LED** status koneksi (radius max 4-6px).
* Pertahankan 100% konsistensi CSS Variables agar pergantian UI Skins tidak rusak.

### ❌ Hal yang DILARANG Keras (DON'Ts)
* **DILARANG** menambahkan efek glow kabur (`box-shadow: 0 0 20px ...` atau lebih besar) pada kartu, panel, atau container.
* **DILARANG** menambahkan `text-shadow` bercahaya pada judul atau teks deskripsi.
* **DILARANG** membuat efek senter kursor (*flashlight cursor glow*) yang menyilaukan layar saat mouse digerakkan.
* **DILARANG** menggunakan warna neon mentah tanpa saturasi terukur (misal `#00ffff` murni atau `#ff00ff` murni yang menusuk mata).
* **DILARANG** menggunakan border solid putih tebal (`border: 2px solid #fff`), selalu gunakan tingkat alpha transparan.

---

## 14. Checklist Verifikasi Implementasi Baru (QA)

Sebelum merilis halaman atau komponen baru, pastikan:

- [ ] **No Unnecessary Glow:** Apakah kartu, tombol, dan teks bebas dari efek glow halo kabur yang tidak perlu?
- [ ] **Vercel / Linear Precision:** Apakah kontainer memakai hairline border tipis `1px solid rgba(255, 255, 255, 0.08)` dan tipografi berspasi rapat?
- [ ] **Legibility First:** Apakah teks dapat dibaca dengan sangat jelas dan tidak membuat mata lelah?
- [ ] **Token Alignment:** Apakah seluruh warna dan padding mengambil variabel resmi dari [`main.css`](file:///d:/Data%20Project/Personal%20Project/PROJECT%20ATOM/public/assets/css/main.css)?
- [ ] **Tactile Hover:** Apakah interaksi hover terasa taktil (mikro-elevasi 1-2px + border accent highlight + pergeseran panah directional)?
- [ ] **Compact Screen Friendly:** Apakah tampilan tidak sesak saat dibuka di layar laptop resolusi 1366×768?
- [ ] **Skin Synchronization:** Apakah komponen tetap tampil harmonis saat UI Skin diubah ke *ChatGPT, Claude, WhatsApp*, atau *Retro*?

---

*Disusun dan dibakukan untuk menghasilkan antarmuka A.T.O.M. yang dewasa, presisi, tenang, dan berwibawa.*  
*Initiated & Orchestrated with Pride.*
