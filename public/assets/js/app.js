/**
 * A.T.O.M. — App Utilities & Shared Logic
 * Sidebar toggle, toast notifications, navigation
 */

// ─── Sidebar Toggle (Desktop & Mobile) ────────────────────
const sidebar = document.getElementById('app-sidebar');
const overlay = document.getElementById('sidebar-overlay');
const menuBtn = document.getElementById('mobile-menu-btn');
const appMain = document.querySelector('.app-main');

function toggleSidebar() {
  const isMobile = window.innerWidth <= 768;
  if (isMobile) {
    sidebar?.classList.toggle('open');
    overlay?.classList.toggle('visible');
    if (sidebar?.classList.contains('open')) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  } else {
    sidebar?.classList.toggle('collapsed');
    appMain?.classList.toggle('sidebar-collapsed');
    
    // Save state to localStorage
    const isCollapsed = sidebar?.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isCollapsed ? 'true' : 'false');
  }
}

function closeSidebar() {
  sidebar?.classList.remove('open');
  overlay?.classList.remove('visible');
  document.body.style.overflow = '';
}

menuBtn?.addEventListener('click', toggleSidebar);
overlay?.addEventListener('click', closeSidebar);

// Close on nav link click (mobile only)
document.querySelectorAll('.sidebar-nav a').forEach(link => {
  link.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
      closeSidebar();
    }
  });
});

// Auto-close sidebar on any session selection or mobile action
document.addEventListener('click', (e) => {
  if (window.innerWidth <= 768) {
    if (e.target.closest('.session-item') || e.target.closest('.btn-new-chat') || e.target.closest('.sidebar-nav a')) {
      closeSidebar();
    }
  }
});

// Restore sidebar state on load & inject close button
document.addEventListener('DOMContentLoaded', () => {
  // Restore sidebar state
  if (window.innerWidth > 768) {
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
      sidebar?.classList.add('collapsed');
      appMain?.classList.add('sidebar-collapsed');
    }
  }

  // Inject close/collapse button in sidebar header (desktop & mobile)
  const sidebarHeader = document.querySelector('.sidebar-header');
  if (sidebarHeader && !sidebarHeader.querySelector('.sidebar-close-btn')) {
    const closeBtn = document.createElement('button');
    closeBtn.className = 'sidebar-close-btn';
    closeBtn.innerHTML = `
      <span class="desktop-icon">◀</span>
      <span class="mobile-icon">✕</span>
    `;
    closeBtn.title = 'Tutup / Ciutkan Sidebar';
    closeBtn.type = 'button';
    closeBtn.setAttribute('aria-label', 'Tutup Sidebar');
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (window.innerWidth <= 768) {
        closeSidebar();
      } else {
        toggleSidebar();
      }
    });
    sidebarHeader.appendChild(closeBtn);
  }

  // Initialize Vapor Chamber particle system if canvas is present
  if (document.getElementById('vapor-canvas') && window.VaporChamber) {
    window.vaporChamberInstance = new window.VaporChamber('vapor-canvas');
  }
});

// ─── Flashlight Cursor Glow ──────────────────────────────
const cursorGlow = document.createElement('div');
cursorGlow.className = 'cursor-glow';
document.body.appendChild(cursorGlow);

let mouseX = -999, mouseY = -999;
let glowRaf = null;

document.addEventListener('mousemove', (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;
  if (!glowRaf) {
    glowRaf = requestAnimationFrame(() => {
      cursorGlow.style.setProperty('--mouse-x', `${mouseX}px`);
      cursorGlow.style.setProperty('--mouse-y', `${mouseY}px`);
      glowRaf = null;
    });
  }
}, { passive: true });


// ─── Toast Notifications ────────────────────────────────
const toastContainer = document.getElementById('toast-container');

function showToast(message, type = 'info', duration = 3500) {
  if (!toastContainer) return;

  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span style="font-size:1.1rem;flex-shrink:0;">${icons[type] || 'ℹ️'}</span>
    <span style="flex:1;font-size:0.85rem;color:var(--text-primary);">${message}</span>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1rem;padding:0;line-height:1;">×</button>
  `;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Global toast function
window.showToast = showToast;


// ─── Resilient Telemetry Logger (Client-First + Background Sync) ────
const TELEM_STORAGE_KEY = 'atom_telemetry_logs';

function logTelemetry(entry) {
  try {
    const timestampStr = new Date().toISOString();
    const promptLen = (entry.user_input || '').length;
    const respLen = (entry.ai_response || '').length;
    
    // Estimasi token standar (~4 chars/token)
    const promptTokens = Math.max(1, Math.ceil(promptLen / 4));
    const completionTokens = Math.max(1, Math.ceil(respLen / 4));
    const totalTokens = promptTokens + completionTokens;

    const fullEntry = {
      id: 'telem_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
      timestamp: timestampStr,
      user_input: entry.user_input || '',
      model_used: entry.model_used || 'Cortex Route',
      response_time: parseFloat(entry.response_time) || 0,
      status: entry.status || 'SUCCESS',
      ai_response: entry.ai_response || '',
      feedback_type: entry.feedback_type || (entry.status === 'FEEDBACK_LIKE' ? 'LIKE' : (entry.status === 'FEEDBACK_DISLIKE' ? 'DISLIKE' : null)),
      critique_category: entry.critique_category || null,
      critique_note: entry.critique_note || null,
      tokens: {
        prompt: promptTokens,
        completion: completionTokens,
        total: totalTokens
      }
    };

    // 1. Simpan langsung ke localStorage (Instan 0ms, zero-latency, anti-putus!)
    let logs = [];
    try {
      const raw = localStorage.getItem(TELEM_STORAGE_KEY);
      logs = raw ? JSON.parse(raw) : [];
    } catch {}

    logs.unshift(fullEntry);
    if (logs.length > 500) logs = logs.slice(0, 500);
    localStorage.setItem(TELEM_STORAGE_KEY, JSON.stringify(logs));

    // 2. Kirim ke backend secara asinkron tanpa memblokir UI
    fetch('/api/telemetry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_input: fullEntry.user_input,
        model_used: fullEntry.model_used,
        response_time: fullEntry.response_time,
        status: fullEntry.status,
        ai_response: fullEntry.ai_response,
        feedback_type: fullEntry.feedback_type,
        critique_category: fullEntry.critique_category,
        critique_note: fullEntry.critique_note
      })
    }).catch(() => {
      // Disconnect-safe: tidak pernah memicu error di frontend
    });
  } catch (err) {
    console.warn('[ATOM] Local telemetry save error:', err);
  }
}

// Ekstrak telemetri dari riwayat percakapan yang ada (Auto Backfill jika log kosong)
function backfillTelemetryFromSessions() {
  const syntheticLogs = [];
  try {
    // 1. Ambil dari chat sessions
    const rawChat = localStorage.getItem('atom_chat_sessions');
    if (rawChat) {
      const sessions = JSON.parse(rawChat);
      sessions.forEach(sess => {
        const msgs = sess.messages || [];
        for (let i = 0; i < msgs.length; i++) {
          if (msgs[i].role === 'user' && msgs[i + 1] && msgs[i + 1].role === 'assistant') {
            const userMsg = msgs[i];
            const aiMsg = msgs[i + 1];
            const pLen = (userMsg.content || '').length;
            const rLen = (aiMsg.content || '').length;
            const model = aiMsg.model || 'Groq (Llama 3.3 70B)';
            syntheticLogs.push({
              id: 'bf_' + (userMsg.timestamp || sess.updatedAt || Date.now()) + '_' + i,
              timestamp: new Date(sess.updatedAt || Date.now()).toISOString(),
              user_input: userMsg.content || '',
              model_used: model,
              response_time: 1.15,
              status: 'SUCCESS',
              ai_response: aiMsg.content || '',
              tokens: {
                prompt: Math.max(1, Math.ceil(pLen / 4)),
                completion: Math.max(1, Math.ceil(rLen / 4)),
                total: Math.max(2, Math.ceil((pLen + rLen) / 4))
              }
            });
          }
        }
      });
    }

    // 2. Ambil dari roleplay sessions
    const rawRp = localStorage.getItem('atom_rp_sessions');
    if (rawRp) {
      const rpSessions = JSON.parse(rawRp);
      rpSessions.forEach(sess => {
        const msgs = sess.messages || [];
        for (let i = 0; i < msgs.length; i++) {
          if (msgs[i].role === 'user' && msgs[i + 1] && msgs[i + 1].role === 'assistant') {
            const userMsg = msgs[i];
            const aiMsg = msgs[i + 1];
            const pLen = (userMsg.content || '').length;
            const rLen = (aiMsg.content || '').length;
            const model = aiMsg.model || 'DeepSeek V3 (Cloud)';
            syntheticLogs.push({
              id: 'bfrp_' + (userMsg.timestamp || sess.updatedAt || Date.now()) + '_' + i,
              timestamp: new Date(sess.updatedAt || Date.now()).toISOString(),
              user_input: userMsg.content || '',
              model_used: model,
              response_time: 1.65,
              status: 'SUCCESS',
              ai_response: aiMsg.content || '',
              tokens: {
                prompt: Math.max(1, Math.ceil(pLen / 4)),
                completion: Math.max(1, Math.ceil(rLen / 4)),
                total: Math.max(2, Math.ceil((pLen + rLen) / 4))
              }
            });
          }
        }
      });
    }
  } catch (e) {
    console.warn('[ATOM] Backfill calculation error:', e);
  }
  return syntheticLogs;
}

window.logTelemetry = logTelemetry;
window.backfillTelemetryFromSessions = backfillTelemetryFromSessions;
window.TELEM_STORAGE_KEY = TELEM_STORAGE_KEY;


// ─── Auto-resize Textarea ────────────────────────────────
function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
}

document.querySelectorAll('textarea').forEach(ta => {
  ta.addEventListener('input', () => autoResize(ta));
});


// ─── Smooth Scroll to Bottom ────────────────────────────
function scrollToBottom(container) {
  if (!container) return;
  container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}
window.scrollToBottom = scrollToBottom;


// ─── Markdown Renderer (via marked.js) ──────────────────
function renderMarkdown(text) {
  if (typeof marked === 'undefined') return escapeHtml(text).replace(/\n/g, '<br>');
  try {
    marked.setOptions({
      gfm: true,
      breaks: true,
      sanitize: false,
    });
    return marked.parse(text);
  } catch {
    return escapeHtml(text).replace(/\n/g, '<br>');
  }
}
window.renderMarkdown = renderMarkdown;

function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;


// ─── Status Indicators ─────────────────────────────────
async function updateStatusIndicators() {
  try {
    const resp = await fetch('/api/status');
    if (!resp.ok) return;
    const status = await resp.json();

    const services = ['local', 'groq', 'crew', 'gemini'];
    services.forEach(srv => {
      const isOnline = status[srv] === 'online';
      
      const dot = document.getElementById(`dot-${srv}`);
      if (dot) {
        dot.className = `status-dot ${isOnline ? 'online' : 'offline'}`;
      }
      
      const pill = document.getElementById(`pill-${srv}`);
      if (pill) {
        pill.className = `status-pill ${isOnline ? 'online' : 'offline'}`;
      }
    });
  } catch (e) {
    console.warn('[ATOM] Failed to fetch dynamic status:', e);
  }
}

updateStatusIndicators();

// ─── Settings & Customization Application ───────────────────
function applySavedPreferences() {
  // UI Theme (Default, ChatGPT, Claude, WhatsApp, Retro)
  const savedUiTheme = localStorage.getItem('atom_ui_theme') || 'default';
  document.documentElement.setAttribute('data-ui-theme', savedUiTheme);

  // Accent Color (for Default theme: gold, cyan, violet, emerald, crimson, monolith)
  const savedAccent = localStorage.getItem('atom_accent') || localStorage.getItem('atom_theme') || 'gold';
  document.documentElement.setAttribute('data-accent', savedAccent);
  document.documentElement.setAttribute('data-theme', savedAccent);

  // Layout density
  const savedDensity = localStorage.getItem('atom_density') || 'normal';
  document.documentElement.setAttribute('data-density', savedDensity);

  // Atom spin animation
  const savedSpin = localStorage.getItem('atom_spin');
  if (savedSpin !== null) {
    document.documentElement.setAttribute('data-atom-spin', savedSpin);
  }

  // Canvas particles
  const savedParticles = localStorage.getItem('atom_setting_particles');
  if (savedParticles === 'false') {
    const canvas = document.getElementById('vapor-canvas');
    if (canvas) canvas.style.display = 'none';
  }

  // Cursor flashlight glow
  const savedGlow = localStorage.getItem('atom_setting_glow');
  if (savedGlow === 'false' && cursorGlow) {
    cursorGlow.style.display = 'none';
  }
}

// Global functions for customization
window.setAtomUiTheme = function(uiTheme) {
  localStorage.setItem('atom_ui_theme', uiTheme);
  document.documentElement.setAttribute('data-ui-theme', uiTheme);
};

window.setAtomAccent = function(accent) {
  localStorage.setItem('atom_accent', accent);
  localStorage.setItem('atom_theme', accent);
  document.documentElement.setAttribute('data-accent', accent);
  document.documentElement.setAttribute('data-theme', accent);
};

window.setAtomTheme = function(theme) {
  window.setAtomAccent(theme);
};

window.setAtomDensity = function(density) {
  localStorage.setItem('atom_density', density);
  document.documentElement.setAttribute('data-density', density);
};

window.setAtomSpin = function(enabled) {
  localStorage.setItem('atom_spin', enabled ? 'true' : 'false');
  document.documentElement.setAttribute('data-atom-spin', enabled ? 'true' : 'false');
};

// ─── Bilingual Privacy Disclaimer Modal ──────────────────────────────
const PRIVACY_STORAGE_KEY = 'atom_hide_privacy_disclaimer';

function showPrivacyDisclaimerModal(force = false) {
  if (!force && localStorage.getItem(PRIVACY_STORAGE_KEY) === 'true') {
    return;
  }

  // Cegah duplikasi modal jika sudah ada
  if (document.getElementById('privacy-disclaimer-modal-overlay')) return;

  let currentLang = 'id'; // default 'id', toggleable to 'en'

  const overlayEl = document.createElement('div');
  overlayEl.className = 'privacy-disclaimer-overlay';
  overlayEl.id = 'privacy-disclaimer-modal-overlay';

  const modalHtml = `
    <div class="privacy-disclaimer-card" role="dialog" aria-modal="true" aria-labelledby="disclaimer-modal-title">
      <div class="disclaimer-card-header">
        <div class="disclaimer-title-wrap">
          <div class="disclaimer-icon-shield">🛡️</div>
          <div>
            <div class="disclaimer-title" id="disclaimer-modal-title">PEMBERITAHUAN PRIVASI</div>
            <div style="font-size:0.65rem;color:var(--text-muted);font-family:var(--font-mono);letter-spacing:0.06em;">A.T.O.M. SECURITY PROTOCOL</div>
          </div>
        </div>
        <div class="disclaimer-lang-tabs">
          <button type="button" class="disclaimer-tab-btn active" id="tab-lang-id" data-lang="id">🇮🇩 Indonesia</button>
          <button type="button" class="disclaimer-tab-btn" id="tab-lang-en" data-lang="en">🇬🇧 English</button>
        </div>
      </div>

      <div class="disclaimer-card-body">
        <div class="disclaimer-warning-banner">
          <span class="warning-icon">⚠️</span>
          <div>
            <strong id="disclaimer-banner-title">Jangan Kirim Informasi Sensitif atau Data Penting ke Chat</strong>
            <p id="disclaimer-banner-desc">Demi keamanan privasi Anda, mohon untuk <b>TIDAK</b> memasukkan informasi rahasia, nomor identitas pribadi, kata sandi, rekening/data finansial, atau data penting perusahaan ke dalam percakapan.</p>
          </div>
        </div>

        <div class="disclaimer-info-list" id="disclaimer-info-bullets">
          <div class="disclaimer-info-item">
            <span class="item-bullet">✦</span>
            <span>Input percakapan diproses oleh model kecerdasan buatan (Cloud LPU & Local LLM).</span>
          </div>
          <div class="disclaimer-info-item">
            <span class="item-bullet">✦</span>
            <span>Jangan pernah membagikan API key rahasia, kredensial server, atau data sensitif pribadi.</span>
          </div>
          <div class="disclaimer-info-item">
            <span class="item-bullet">✦</span>
            <span>Anda memiliki kendali penuh untuk menghapus riwayat obrolan sewaktu-waktu.</span>
          </div>
        </div>
      </div>

      <div class="disclaimer-card-footer">
        <label class="disclaimer-checkbox-label">
          <input type="checkbox" id="chk-dont-show-disclaimer">
          <span id="disclaimer-chk-label">Jangan tampilkan lagi (Do not show again)</span>
        </label>
        <button type="button" class="btn btn-primary" id="btn-accept-disclaimer" style="padding:8px 18px;font-size:0.85rem;">
          <span id="disclaimer-btn-label">Saya Mengerti & Lanjutkan</span>
        </button>
      </div>
    </div>
  `;

  overlayEl.innerHTML = modalHtml;
  document.body.appendChild(overlayEl);

  // Bahasa Translation Data
  const translations = {
    id: {
      title: 'PEMBERITAHUAN PRIVASI',
      bannerTitle: 'Jangan Kirim Informasi Sensitif atau Data Penting ke Chat',
      bannerDesc: 'Demi keamanan privasi Anda, mohon untuk <b>TIDAK</b> memasukkan informasi rahasia, nomor identitas pribadi, kata sandi, rekening/data finansial, atau data penting perusahaan ke dalam percakapan.',
      bullets: [
        'Input percakapan diproses oleh model kecerdasan buatan (Cloud LPU & Local LLM).',
        'Jangan pernah membagikan API key rahasia, kredensial server, atau data sensitif pribadi.',
        'Anda memiliki kendali penuh untuk menghapus riwayat obrolan sewaktu-waktu.'
      ],
      chkLabel: 'Jangan tampilkan lagi (Do not show again)',
      btnLabel: 'Saya Mengerti & Lanjutkan'
    },
    en: {
      title: 'PRIVACY NOTICE',
      bannerTitle: 'Do Not Send Sensitive Information or Important Data to the Chat',
      bannerDesc: 'For your security and privacy, please <b>DO NOT</b> enter confidential records, personal identification numbers, passwords, financial/banking details, or critical company data into the conversation.',
      bullets: [
        'Conversation inputs are processed by Artificial Intelligence models (Cloud LPU & Local LLM).',
        'Never share secret API keys, server credentials, or critical personal identifiers.',
        'You have full autonomy to clear and reset your chat history at any time.'
      ],
      chkLabel: 'Do not show again (Jangan tampilkan lagi)',
      btnLabel: 'I Understand & Continue'
    }
  };

  const applyLang = (lang) => {
    currentLang = lang;
    const t = translations[lang];
    const titleEl = overlayEl.querySelector('#disclaimer-modal-title');
    const bTitleEl = overlayEl.querySelector('#disclaimer-banner-title');
    const bDescEl = overlayEl.querySelector('#disclaimer-banner-desc');
    const bulletsEl = overlayEl.querySelector('#disclaimer-info-bullets');
    const chkLabelEl = overlayEl.querySelector('#disclaimer-chk-label');
    const btnLabelEl = overlayEl.querySelector('#disclaimer-btn-label');

    if (titleEl) titleEl.textContent = t.title;
    if (bTitleEl) bTitleEl.textContent = t.bannerTitle;
    if (bDescEl) bDescEl.innerHTML = t.bannerDesc;
    if (chkLabelEl) chkLabelEl.textContent = t.chkLabel;
    if (btnLabelEl) btnLabelEl.textContent = t.btnLabel;

    if (bulletsEl) {
      bulletsEl.innerHTML = t.bullets.map(b => `
        <div class="disclaimer-info-item">
          <span class="item-bullet">✦</span>
          <span>${b}</span>
        </div>
      `).join('');
    }

    overlayEl.querySelectorAll('.disclaimer-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });
  };

  overlayEl.querySelector('#tab-lang-id')?.addEventListener('click', () => applyLang('id'));
  overlayEl.querySelector('#tab-lang-en')?.addEventListener('click', () => applyLang('en'));

  const btnAccept = overlayEl.querySelector('#btn-accept-disclaimer');
  const chkDontShow = overlayEl.querySelector('#chk-dont-show-disclaimer');

  btnAccept?.addEventListener('click', () => {
    if (chkDontShow?.checked) {
      localStorage.setItem(PRIVACY_STORAGE_KEY, 'true');
    }
    overlayEl.style.opacity = '0';
    overlayEl.style.transition = 'opacity 0.25s ease';
    setTimeout(() => overlayEl.remove(), 260);
  });
}

window.showPrivacyDisclaimerModal = showPrivacyDisclaimerModal;

// ─── Modal Kritik Jawaban AI (Dislike Feedback Flow) ─────────────────
window.openCritiqueModal = function({ modelUsed = '', promptText = '', responseExcerpt = '', onSubmitted }) {
  // Cegah duplikasi modal
  const existing = document.getElementById('critique-modal-overlay');
  if (existing) existing.remove();

  const overlayEl = document.createElement('div');
  overlayEl.className = 'critique-modal-overlay';
  overlayEl.id = 'critique-modal-overlay';

  let selectedCategory = 'Jawaban Tidak Akurat / Halusinasi';

  const modalHtml = `
    <div class="critique-modal-card" role="dialog" aria-modal="true">
      <div class="critique-modal-header">
        <div class="critique-modal-title">
          <span>👎</span>
          <span>Kritik & Masukan Respon AI</span>
        </div>
        <button type="button" id="btn-close-critique" style="background:none;border:none;color:var(--text-muted);font-size:1.2rem;cursor:pointer;">✕</button>
      </div>

      <div style="padding:var(--space-4) var(--space-5);">
        <p style="font-size:0.8rem;color:var(--text-secondary);margin:0 0 10px 0;line-height:1.45;">
          Bantu kami mengevaluasi kualitas model. Kritik ini akan otomatis dicatat ke dashboard <b>Telemetry</b>.
        </p>

        <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:6px;">
          Model: <span class="model-badge" style="font-size:0.7rem;">${escapeHtml(modelUsed || 'AI Model')}</span>
        </div>

        <div style="font-size:0.75rem;color:var(--text-muted);margin-top:10px;">Pilih masalah utama:</div>
        <div class="critique-category-pills" id="critique-pills-wrap">
          <button type="button" class="critique-pill-btn active" data-cat="Jawaban Tidak Akurat / Halusinasi">❌ Tidak Akurat / Salah</button>
          <button type="button" class="critique-pill-btn" data-cat="Terlalu Bertele-tele / Panjang">🔄 Bertele-tele / Panjang</button>
          <button type="button" class="critique-pill-btn" data-cat="Menyimpang dari Instruksi">⚠️ Abaikan Instruksi</button>
          <button type="button" class="critique-pill-btn" data-cat="Bahasa Kaku / Alasan Lain">💡 Alasan Lainnya</button>
        </div>

        <div style="font-size:0.75rem;color:var(--text-muted);margin:10px 0 6px 0;">Catatan kritik / perbaikan yang diharapkan (opsional):</div>
        <textarea class="critique-textarea" id="critique-note-text" placeholder="Jelaskan secara singkat apa yang perlu diperbaiki dari jawaban AI ini..."></textarea>
      </div>

      <div style="padding:var(--space-3) var(--space-5);background:rgba(0,0,0,0.3);border-top:1px solid rgba(255,255,255,0.08);display:flex;justify-content:flex-end;gap:10px;">
        <button type="button" class="btn btn-secondary btn-sm" id="btn-cancel-critique">Batal</button>
        <button type="button" class="btn btn-danger btn-sm" id="btn-submit-critique" style="background:#dc2626;border-color:#b91c1c;color:#fff;">
          Kirim ke Telemetry
        </button>
      </div>
    </div>
  `;

  overlayEl.innerHTML = modalHtml;
  document.body.appendChild(overlayEl);

  const pillsWrap = overlayEl.querySelector('#critique-pills-wrap');
  pillsWrap?.querySelectorAll('.critique-pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      pillsWrap.querySelectorAll('.critique-pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedCategory = btn.dataset.cat || 'Lainnya';
    });
  });

  const closeModal = () => {
    overlayEl.style.opacity = '0';
    overlayEl.style.transition = 'opacity 0.2s ease';
    setTimeout(() => overlayEl.remove(), 210);
  };

  overlayEl.querySelector('#btn-close-critique')?.addEventListener('click', closeModal);
  overlayEl.querySelector('#btn-cancel-critique')?.addEventListener('click', closeModal);

  overlayEl.querySelector('#btn-submit-critique')?.addEventListener('click', () => {
    const noteText = overlayEl.querySelector('#critique-note-text')?.value.trim() || '';

    // Log ke telemetry
    logTelemetry({
      user_input: promptText,
      model_used: modelUsed || 'Cortex Model',
      response_time: 0,
      status: 'FEEDBACK_DISLIKE',
      feedback_type: 'DISLIKE',
      critique_category: selectedCategory,
      critique_note: noteText,
      ai_response: responseExcerpt
    });

    if (typeof onSubmitted === 'function') {
      onSubmitted(selectedCategory, noteText);
    }

    showToast('Kritik & masukan Anda telah dicatat ke Telemetry.', 'info');
    closeModal();
  });
};

document.addEventListener('DOMContentLoaded', () => {
  applySavedPreferences();
  // Tampilkan Disclaimer Privasi jika belum pernah ditutup dengan opsi "Do not show again"
  showPrivacyDisclaimerModal(false);
});
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  applySavedPreferences();
  showPrivacyDisclaimerModal(false);
}

console.log('%c⚛️ A.T.O.M. v4.0 CORTEX INITIALIZED', 'color:#C9A227;font-size:14px;font-weight:bold;');

