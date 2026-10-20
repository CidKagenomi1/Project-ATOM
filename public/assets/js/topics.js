/**
 * A.T.O.M. — Topics & Intel Hub Controller (topics.js)
 * Manages live transmissions, multi-category topics, reader drawer, bookmarks, and AI insights.
 */

let allArticles = [];
let bookmarkedIds = new Set();
let currentArticle = null;
let currentCategory = 'technology';
let currentScope = 'international'; // 'international' | 'national'
let currentQuery = '';
let isBookmarkView = false;
let searchDebounceTimer = null;

// Scope Configurations & Categories with crisp SVG icons (Vercel/Linear tactical precision)
const SCOPE_CONFIG = {
    international: {
        defaultCategory: 'technology',
        placeholder: 'Cari topik global, biologi, bumi, antariksa, sains, teknologi...',
        categories: [
            {
                id: 'technology',
                label: 'All Tech',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>'
            },
            {
                id: 'biology',
                label: 'Biologi & Alam',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>'
            },
            {
                id: 'geography',
                label: 'Geografi & Bumi',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>'
            },
            {
                id: 'astronomy',
                label: 'Astronomi & Fisika',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><circle cx="12" cy="12" r="3"></circle><path d="M3 12a9 9 0 0 1 18 0"></path><path d="M5.6 5.6a9 9 0 0 1 12.8 12.8"></path></svg>'
            },
            {
                id: 'discoveries',
                label: 'Wawasan & Arkeologi',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>'
            },
            {
                id: 'business',
                label: 'Bisnis Global',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>'
            }
        ]
    },
    national: {
        defaultCategory: 'general',
        placeholder: 'Cari isu nasional, kebijakan, ekonomi, pendidikan, nusantara...',
        categories: [
            {
                id: 'general',
                label: 'Semua Nasional',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg>'
            },
            {
                id: 'politics',
                label: 'Politik & Kebijakan',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><line x1="3" y1="22" x2="21" y2="22"></line><line x1="6" y1="18" x2="6" y2="11"></line><line x1="10" y1="18" x2="10" y2="11"></line><line x1="14" y1="18" x2="14" y2="11"></line><line x1="18" y1="18" x2="18" y2="11"></line><polygon points="12 2 20 7 4 7"></polygon></svg>'
            },
            {
                id: 'business',
                label: 'Ekonomi & Bisnis',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
            },
            {
                id: 'culture',
                label: 'Edukasi & Budaya',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>'
            },
            {
                id: 'technology',
                label: 'Teknologi Nusantara',
                svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>'
            }
        ]
    }
};

// DOM Elements
const feedGrid = document.getElementById('topicsGrid');
const spotlightCard = document.getElementById('spotlightCard');
const spotlightWrapper = document.getElementById('spotlightWrapper');
const readerDrawer = document.getElementById('readerDrawer');
const searchInput = document.getElementById('topicsSearch');
const clearSearchBtn = document.getElementById('clearSearch');
const bookmarkFilterChip = document.getElementById('bookmarkFilterChip');
const liveCountEl = document.getElementById('liveCount');
const activeCategoryLabel = document.getElementById('activeCategoryLabel');

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    renderCategoryChips();
    setupEventListeners();
    updateActiveCategoryHeader();
    await loadBookmarks();
    await loadTopics();
});

function renderCategoryChips() {
    const container = document.getElementById('topicsChipsContainer');
    if (!container) return;

    const config = SCOPE_CONFIG[currentScope] || SCOPE_CONFIG.international;
    container.innerHTML = '';

    config.categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `filter-chip ${(!isBookmarkView && currentCategory === cat.id) ? 'active' : ''}`;
        btn.dataset.category = cat.id;
        btn.dataset.label = cat.label;
        btn.innerHTML = `${cat.svg} <span>${cat.label}</span>`;

        btn.addEventListener('click', () => {
            isBookmarkView = false;
            currentCategory = cat.id;
            currentQuery = '';
            if (searchInput) searchInput.value = '';
            if (clearSearchBtn) clearSearchBtn.style.display = 'none';

            container.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            if (bookmarkFilterChip) bookmarkFilterChip.classList.remove('active');
            btn.classList.add('active');

            updateActiveCategoryHeader();
            loadTopics();
        });

        container.appendChild(btn);
    });

    if (searchInput) {
        searchInput.placeholder = config.placeholder;
    }
}

function updateActiveCategoryHeader() {
    if (!activeCategoryLabel) return;
    if (isBookmarkView) {
        activeCategoryLabel.textContent = 'Bookmarks';
        return;
    }
    const scopeLabel = currentScope === 'national' ? 'Nasional' : 'Internasional';
    const config = SCOPE_CONFIG[currentScope] || SCOPE_CONFIG.international;
    const catObj = config.categories.find(c => c.id === currentCategory);
    const catLabel = catObj ? catObj.label : currentCategory;
    activeCategoryLabel.textContent = `${scopeLabel} • ${catLabel}`;
}

function setupEventListeners() {
    // Scope Switcher (Internasional vs Nasional)
    const scopeBtns = document.querySelectorAll('.scope-toggle-btn');
    scopeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const scope = btn.dataset.scope;
            if (scope === currentScope && !isBookmarkView) return;
            currentScope = scope;
            scopeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Switch default category for this scope
            const config = SCOPE_CONFIG[currentScope] || SCOPE_CONFIG.international;
            currentCategory = config.defaultCategory;
            isBookmarkView = false;
            currentQuery = '';
            if (searchInput) searchInput.value = '';
            if (clearSearchBtn) clearSearchBtn.style.display = 'none';

            if (bookmarkFilterChip) bookmarkFilterChip.classList.remove('active');

            renderCategoryChips();
            updateActiveCategoryHeader();
            loadTopics();
        });
    });

    // Bookmark Filter Chip
    if (bookmarkFilterChip) {
        bookmarkFilterChip.addEventListener('click', () => {
            isBookmarkView = true;
            const container = document.getElementById('topicsChipsContainer');
            if (container) {
                container.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            }
            bookmarkFilterChip.classList.add('active');
            updateActiveCategoryHeader();
            loadBookmarksView();
        });
    }

    // Search input
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const val = e.target.value.trim();
            if (clearSearchBtn) clearSearchBtn.style.display = val ? 'block' : 'none';

            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                currentQuery = val;
                if (isBookmarkView) {
                    filterBookmarksLocal(val);
                } else {
                    loadTopics();
                }
            }, 500);
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            currentQuery = '';
            if (isBookmarkView) {
                loadBookmarksView();
            } else {
                loadTopics();
            }
        });
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeReader();
        }
    });
}

// ─── Data Fetching ───

async function loadBookmarks() {
    try {
        const res = await fetch('/api/bulletin/marked');
        const data = await res.json();
        if (data.status === 'success' && Array.isArray(data.articles)) {
            bookmarkedIds = new Set(data.articles.map(a => a.id));
            const badge = document.getElementById('bookmarkCountBadge');
            if (badge) badge.textContent = bookmarkedIds.size;
        }
    } catch (err) {
        console.warn('[TOPICS] Could not load bookmarks:', err);
    }
}

async function loadTopics() {
    renderLoadingSkeleton();
    try {
        let url = `/api/bulletin/fetch?category=${encodeURIComponent(currentCategory)}&scope=${encodeURIComponent(currentScope)}`;
        if (currentQuery) {
            url += `&q=${encodeURIComponent(currentQuery)}`;
        }

        const res = await fetch(url);
        const data = await res.json();

        if (data.status === 'success' && Array.isArray(data.articles)) {
            allArticles = data.articles;
            if (liveCountEl) {
                const scopeLabel = currentScope === 'national' ? 'Nasional' : 'Global';
                liveCountEl.textContent = `${allArticles.length} Berita (${scopeLabel})`;
            }
            renderFeed(allArticles);
        } else {
            renderEmptyState(data.message || 'Tidak ada berita untuk topik ini saat ini.');
        }
    } catch (err) {
        renderEmptyState(`Koneksi gagal terhubung ke server satelit: ${err.message}`);
    }
}

async function loadBookmarksView() {
    renderLoadingSkeleton();
    try {
        const res = await fetch('/api/bulletin/marked');
        const data = await res.json();
        if (data.status === 'success' && Array.isArray(data.articles)) {
            allArticles = data.articles;
            bookmarkedIds = new Set(allArticles.map(a => a.id));
            const badge = document.getElementById('bookmarkCountBadge');
            if (badge) badge.textContent = bookmarkedIds.size;
            if (liveCountEl) liveCountEl.textContent = `${allArticles.length} Tersimpan`;
            renderFeed(allArticles, true);
        } else {
            renderEmptyState('Belum ada artikel yang kamu tandai atau simpan.');
        }
    } catch (err) {
        renderEmptyState(`Gagal memuat bookmark: ${err.message}`);
    }
}

function filterBookmarksLocal(query) {
    if (!query) {
        renderFeed(allArticles, true);
        return;
    }
    const q = query.toLowerCase();
    const filtered = allArticles.filter(a => 
        (a.title && a.title.toLowerCase().includes(q)) || 
        (a.content && a.content.toLowerCase().includes(q)) ||
        (a.source && a.source.toLowerCase().includes(q))
    );
    renderFeed(filtered, true);
}

// ─── Rendering ───

function renderLoadingSkeleton() {
    if (spotlightWrapper) spotlightWrapper.style.display = 'none';
    if (!feedGrid) return;
    feedGrid.innerHTML = `
        <div class="skeleton-grid">
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
        </div>
    `;
}

function renderEmptyState(message) {
    if (spotlightWrapper) spotlightWrapper.style.display = 'none';
    if (!feedGrid) return;
    feedGrid.innerHTML = `
        <div class="topics-empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48" style="opacity: 0.4;">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <div style="font-size: 1.05rem; font-weight: 600; color: var(--text-primary);">${escapeHtml(message)}</div>
            <div style="font-size: 0.85rem;">Coba gunakan kata kunci lain atau pilih kanal topik berbeda.</div>
        </div>
    `;
}

function renderFeed(articles, isBookmarks = false) {
    if (!feedGrid) return;

    if (!articles || articles.length === 0) {
        renderEmptyState(isBookmarks ? 'Belum ada artikel yang kamu bookmark.' : 'Tidak ditemukan artikel transmisi.');
        return;
    }

    // 1. Render Spotlight if we have articles and not searching
    if (!currentQuery && articles.length > 0 && spotlightWrapper && spotlightCard) {
        const topArticle = articles[0];
        spotlightWrapper.style.display = 'block';
        spotlightCard.onclick = () => openReader(topArticle);

        const topScope = topArticle.scope === 'national' ? 'Nasional' : 'Global';
        document.getElementById('spotlightTitle').textContent = topArticle.title || 'Untitled';
        document.getElementById('spotlightDesc').textContent = topArticle.description || topArticle.content || '';
        document.getElementById('spotlightSource').textContent = `${topArticle.source || 'Intel Feed'} • ${topScope}`;
        document.getElementById('spotlightTime').textContent = formatRelativeTime(topArticle.published_at);
    } else if (spotlightWrapper) {
        spotlightWrapper.style.display = 'none';
    }

    // 2. Render Grid Cards
    const cardsToRender = (!currentQuery && spotlightWrapper && articles.length > 1) ? articles.slice(1) : articles;
    feedGrid.innerHTML = '';

    cardsToRender.forEach(article => {
        const isMarked = bookmarkedIds.has(article.id);
        const card = document.createElement('div');
        card.className = 'article-card';

        let coverImgHtml = '';
        if (article.image_url && article.image_url.startsWith('http')) {
            coverImgHtml = `<img class="article-card-cover" src="${escapeHtml(article.image_url)}" alt="${escapeHtml(article.title)}" loading="lazy" onerror="this.style.display='none'">`;
        }

        const scopeBadgeHtml = article.scope === 'national' 
            ? `<span class="scope-tag scope-tag-nat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="11" height="11"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg> Nasional</span>` 
            : `<span class="scope-tag scope-tag-intl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="11" height="11"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg> Global</span>`;

        card.innerHTML = `
            ${coverImgHtml}
            <div>
                <div class="article-header" style="margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                        <span class="source-badge">${escapeHtml(article.source || 'News')}</span>
                        ${scopeBadgeHtml}
                    </div>
                    <span class="time-badge">${formatRelativeTime(article.published_at)}</span>
                </div>
                <h3 class="article-title">${escapeHtml(article.title || 'Untitled')}</h3>
                <p class="article-excerpt">${escapeHtml(article.description || article.content || '')}</p>
            </div>
            <div class="article-actions">
                <button class="btn-read-article">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13">
                        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                    </svg>
                    Baca
                </button>
                <div class="article-btn-group">
                    <button class="btn-icon-action btn-ai-summary" title="Bedah AI Ringkas">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path>
                        </svg>
                    </button>
                    <button class="btn-icon-action btn-bookmark ${isMarked ? 'marked' : ''}" title="${isMarked ? 'Hapus Bookmark' : 'Simpan Bookmark'}">
                        <svg viewBox="0 0 24 24" fill="${isMarked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" width="14" height="14">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        // Card events
        card.querySelector('.article-title').onclick = () => openReader(article);
        card.querySelector('.btn-read-article').onclick = (e) => {
            e.stopPropagation();
            openReader(article);
        };
        card.querySelector('.btn-bookmark').onclick = (e) => {
            e.stopPropagation();
            toggleBookmark(article, card.querySelector('.btn-bookmark'));
        };
        card.querySelector('.btn-ai-summary').onclick = (e) => {
            e.stopPropagation();
            openReader(article, true);
        };

        feedGrid.appendChild(card);
    });
}

// ─── Reader Drawer ───

function openReader(article, autoSummarize = false) {
    currentArticle = article;
    if (!readerDrawer) return;

    document.getElementById('readerTitle').textContent = article.title || 'Untitled';
    document.getElementById('readerSource').textContent = article.source || 'News Source';
    document.getElementById('readerAuthor').textContent = article.author ? `Oleh: ${article.author}` : '';
    document.getElementById('readerTime').textContent = formatRelativeTime(article.published_at);
    document.getElementById('readerBody').textContent = article.content || article.description || 'Konten tidak tersedia.';

    const heroImg = document.getElementById('readerHeroImg');
    if (article.image_url && article.image_url.startsWith('http')) {
        heroImg.src = article.image_url;
        heroImg.style.display = 'block';
    } else {
        heroImg.style.display = 'none';
    }

    const extLink = document.getElementById('readerExternalLink');
    if (extLink) {
        extLink.href = (article.url && article.url !== '#') ? article.url : '#';
        extLink.style.display = (article.url && article.url !== '#') ? 'inline-flex' : 'none';
    }

    // Reset AI Box
    const aiBox = document.getElementById('readerAiBox');
    const aiContent = document.getElementById('readerAiContent');
    if (aiBox && aiContent) {
        aiBox.style.display = 'none';
        aiContent.innerHTML = '';
    }

    // Update bookmark button state in reader
    updateReaderBookmarkBtn();

    readerDrawer.classList.add('open');

    if (autoSummarize) {
        triggerAiSummary();
    }
}

function closeReader() {
    if (readerDrawer) {
        readerDrawer.classList.remove('open');
    }
    currentArticle = null;
}

function updateReaderBookmarkBtn() {
    const btn = document.getElementById('readerBookmarkBtn');
    if (!btn || !currentArticle) return;
    const isMarked = bookmarkedIds.has(currentArticle.id);
    if (isMarked) {
        btn.classList.add('marked');
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg> Tersimpan`;
    } else {
        btn.classList.remove('marked');
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg> Simpan`;
    }
}

// ─── Actions: Bookmark, AI Summary, Magic Notes, Chat ───

async function toggleBookmark(article, btnElement = null) {
    const isMarked = bookmarkedIds.has(article.id);
    if (isMarked) {
        // Unmark
        try {
            await fetch('/api/bulletin/unmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: article.id })
            });
            bookmarkedIds.delete(article.id);
            if (btnElement) {
                btnElement.classList.remove('marked');
                btnElement.querySelector('svg').setAttribute('fill', 'none');
            }
            showToast('Bookmark dihapus');
        } catch (err) {
            showToast('Gagal menghapus bookmark');
        }
    } else {
        // Mark
        try {
            await fetch('/api/bulletin/mark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: article.id,
                    title: article.title,
                    content: article.content,
                    source: article.source,
                    url: article.url,
                    image_url: article.image_url,
                    author: article.author,
                    published_at: article.published_at
                })
            });
            bookmarkedIds.add(article.id);
            if (btnElement) {
                btnElement.classList.add('marked');
                btnElement.querySelector('svg').setAttribute('fill', 'currentColor');
            }
            showToast('Artikel berhasil disimpan ke Bookmark!');
        } catch (err) {
            showToast('Gagal menyimpan bookmark');
        }
    }

    const badge = document.getElementById('bookmarkCountBadge');
    if (badge) badge.textContent = bookmarkedIds.size;
    updateReaderBookmarkBtn();

    if (isBookmarkView) {
        loadBookmarksView();
    }
}

function toggleCurrentReaderBookmark() {
    if (!currentArticle) return;
    toggleBookmark(currentArticle);
}

async function triggerAiSummary() {
    if (!currentArticle) return;
    const aiBox = document.getElementById('readerAiBox');
    const aiContent = document.getElementById('readerAiContent');
    const btnSummary = document.getElementById('btnTriggerSummary');

    if (aiBox) aiBox.style.display = 'block';
    if (aiContent) {
        aiContent.innerHTML = `<div style="display:flex;align-items:center;gap:8px;color:#c4b5fd;">
            <div class="pulse-dot" style="background:#a78bfa;box-shadow:0 0 8px #a78bfa;"></div>
            <span>A.T.O.M. sedang membedah poin kunci transmisi berita...</span>
        </div>`;
    }

    try {
        const res = await fetch('/api/bulletin/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: currentArticle.title,
                content: currentArticle.content || currentArticle.description || '',
                source: currentArticle.source || 'News'
            })
        });
        const data = await res.json();
        if (data.status === 'success' && data.summary) {
            if (typeof marked !== 'undefined') {
                aiContent.innerHTML = marked.parse(data.summary);
            } else {
                aiContent.innerHTML = escapeHtml(data.summary).replace(/\n/g, '<br>');
            }
        } else {
            aiContent.innerHTML = `<span style="color:#f87171;">Tidak dapat merangkum: ${escapeHtml(data.message || 'Unknown error')}</span>`;
        }
    } catch (err) {
        if (aiContent) {
            aiContent.innerHTML = `<span style="color:#f87171;">Koneksi AI gagal: ${escapeHtml(err.message)}</span>`;
        }
    }
}

function sendCurrentToNotes() {
    if (!currentArticle) return;
    try {
        const notePayload = {
            title: `[INTEL] ${currentArticle.title}`,
            content: `## ${currentArticle.title}\n\n**Sumber:** ${currentArticle.source} | **Tanggal:** ${currentArticle.published_at || '-'}\n**URL Asli:** ${currentArticle.url || '-'}\n\n### Ringkasan & Kutipan\n${currentArticle.content || currentArticle.description || ''}\n\n---\n*Disimpan otomatis dari A.T.O.M. Topics Feed*`,
            tags: ['intel', 'news', (currentArticle.source || 'media').toLowerCase().replace(/\s+/g, '-')]
        };
        localStorage.setItem('atom_draft_imported_note', JSON.stringify(notePayload));
        showToast('Tersimpan! Mengalihkan ke Magic Notes...');
        setTimeout(() => {
            window.location.href = 'notes.html?action=import';
        }, 800);
    } catch (err) {
        showToast('Gagal mentransfer ke Magic Notes');
    }
}

function sendCurrentToChat() {
    if (!currentArticle) return;
    try {
        const chatPrompt = `Tolong analisis dan berikan opini strategis tentang berita ini:\n\nJudul: "${currentArticle.title}"\nSumber: ${currentArticle.source}\nKutipan: "${currentArticle.content || currentArticle.description || ''}"\n\nApa implikasi teknologi dan bisnisnya ke depan?`;
        localStorage.setItem('atom_pending_chat_prompt', chatPrompt);
        showToast('Mengalihkan ke Chat A.T.O.M...');
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 600);
    } catch (err) {
        showToast('Gagal mengalihkan ke chat');
    }
}

function copyCurrentArticle() {
    if (!currentArticle) return;
    const text = `${currentArticle.title}\n\nSumber: ${currentArticle.source}\nTautan: ${currentArticle.url}\n\n${currentArticle.content || currentArticle.description || ''}`;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Teks dan tautan berita berhasil disalin ke clipboard!');
    }).catch(() => {
        showToast('Gagal menyalin ke clipboard');
    });
}

// ─── Helpers ───

function formatRelativeTime(dateStr) {
    if (!dateStr) return 'Terkini';
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return 'Terkini';
        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHours = Math.floor(diffMin / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMin < 2) return 'Baru saja';
        if (diffMin < 60) return `${diffMin}m lalu`;
        if (diffHours < 24) return `${diffHours}j lalu`;
        if (diffDays === 1) return 'Kemarin';
        if (diffDays < 7) return `${diffDays} hari lalu`;
        return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
    } catch {
        return 'Terkini';
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function showToast(msg) {
    let toast = document.getElementById('atom-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'atom-toast';
        toast.style.cssText = `
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(20px);
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(96, 165, 250, 0.4);
            color: #f8fafc;
            padding: 10px 18px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 500;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 15px rgba(96, 165, 250, 0.2);
            backdrop-filter: blur(10px);
            z-index: 9999;
            opacity: 0;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            pointer-events: none;
        `;
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(-50%) translateY(0)';
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(20px)';
    }, 2800);
}
