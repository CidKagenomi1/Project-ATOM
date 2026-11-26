/**
 * A.T.O.M. — App Utilities & Shared Logic
 * Sidebar toggle, toast notifications, navigation
 */

// ─── Sidebar Toggle (Desktop & Mobile) ────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const appMain = document.querySelector('.app-main');
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
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  sidebar?.classList.remove('open');
  overlay?.classList.remove('visible');
  document.body.style.overflow = '';
}

window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;

// Auto-close sidebar on any session selection or mobile action
document.addEventListener('click', (e) => {
  if (window.innerWidth <= 768) {
    if (e.target.closest('.session-item') || e.target.closest('.btn-new-chat') || e.target.closest('.sidebar-nav a')) {
      closeSidebar();
    }
  }
});

// Restore sidebar state & inject/bind close button
function initSidebarSystem() {
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const menuBtn = document.getElementById('mobile-menu-btn');
  const appMain = document.querySelector('.app-main');

  menuBtn?.removeEventListener('click', toggleSidebar);
  menuBtn?.addEventListener('click', toggleSidebar);

  overlay?.removeEventListener('click', closeSidebar);
  overlay?.addEventListener('click', closeSidebar);

  // Close on nav link click (mobile only)
  document.querySelectorAll('.sidebar-nav a').forEach(link => {
    link.onclick = () => {
      if (window.innerWidth <= 768) closeSidebar();
    };
  });

  // Restore sidebar state
  if (window.innerWidth > 768) {
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
      sidebar?.classList.add('collapsed');
      appMain?.classList.add('sidebar-collapsed');
    }
  }

  // Inject or bind close/collapse button in sidebar header (desktop & mobile)
  const sidebarHeader = document.querySelector('.sidebar-header');
  if (sidebarHeader) {
    let closeBtn = sidebarHeader.querySelector('.sidebar-close-btn') || document.getElementById('sidebar-close-btn');
    if (!closeBtn) {
      closeBtn = document.createElement('button');
      closeBtn.className = 'sidebar-close-btn';
      closeBtn.id = 'sidebar-close-btn';
      closeBtn.innerHTML = `
        <span class="desktop-icon">◀</span>
        <span class="mobile-icon">✕</span>
      `;
      closeBtn.title = 'Tutup / Ciutkan Sidebar';
      closeBtn.type = 'button';
      closeBtn.setAttribute('aria-label', 'Tutup Sidebar');
      sidebarHeader.appendChild(closeBtn);
    }
    closeBtn.onclick = (e) => {
      if (e) e.stopPropagation();
      if (window.innerWidth <= 768) {
        closeSidebar();
      } else {
        toggleSidebar();
      }
    };
  }
}

// Run immediately AND when DOM is ready
initSidebarSystem();
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSidebarSystem);
}

  // Initialize Vapor Chamber particle system only if explicitly enabled
  const isParticlesEnabled = localStorage.getItem('atom_setting_particles') === 'true';
  if (isParticlesEnabled && document.getElementById('vapor-canvas') && window.VaporChamber) {
    window.vaporChamberInstance = new window.VaporChamber('vapor-canvas');
  }

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
    const chatKey = window.ATOM_Account ? window.ATOM_Account.getChatStorageKey() : 'atom_chat_sessions';
    const rawChat = localStorage.getItem(chatKey) || localStorage.getItem('atom_chat_sessions');
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

    const services = ['local', 'groq', 'crew', 'openrouter'];
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

  // Atom spin animation (default enabled)
  const savedSpin = localStorage.getItem('atom_spin') !== 'false' ? 'true' : 'false';
  document.documentElement.setAttribute('data-atom-spin', savedSpin);

  // Canvas particles (default disabled)
  const savedParticles = localStorage.getItem('atom_setting_particles');
  if (savedParticles !== 'true') {
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

// ─── Per-Account Authentication & Sidebar Account Widget ──────────────
(function initAccountModule() {
  const AUTH_USER_KEY = 'atom_auth_user';
  const AUTH_TOKEN_KEY = 'atom_auth_token';
  const GUEST_SESSIONS_KEY = 'atom_chat_sessions_guest';
  const GUEST_ACTIVE_KEY = 'atom_active_session_id_guest';
  const LEGACY_SESSIONS_KEY = 'atom_chat_sessions';
  const LEGACY_ACTIVE_KEY = 'atom_active_session_id';

  let _sessionVerifiedOnce = false;

  function safeParseJson(raw, fallback) {
    try {
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }

  function hasAnyMessages(sessions) {
    return Array.isArray(sessions) && sessions.some(s => Array.isArray(s?.messages) && s.messages.length > 0);
  }

  function mergeSessionsLists(primaryList, secondaryList) {
    const map = new Map();
    const applyList = (list) => {
      if (!Array.isArray(list)) return;
      list.forEach(sess => {
        if (!sess || !sess.id) return;
        const existing = map.get(sess.id);
        if (!existing) {
          map.set(sess.id, sess);
          return;
        }
        const exMsgs = Array.isArray(existing.messages) ? existing.messages : [];
        const newMsgs = Array.isArray(sess.messages) ? sess.messages : [];
        if (newMsgs.length > exMsgs.length || (newMsgs.length === exMsgs.length && (sess.updatedAt || 0) > (existing.updatedAt || 0))) {
          map.set(sess.id, sess);
        }
      });
    };
    applyList(primaryList);
    applyList(secondaryList);
    return Array.from(map.values()).sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
  }

  const AccountManager = {
    getUser() {
      const parsed = safeParseJson(localStorage.getItem(AUTH_USER_KEY), null);
      if (parsed && typeof parsed === 'object' && parsed.username) {
        return parsed;
      }
      return null;
    },

    getToken() {
      return localStorage.getItem(AUTH_TOKEN_KEY) || null;
    },

    isLoggedIn() {
      return Boolean(this.getUser()?.username && this.getToken());
    },

    getChatStorageKey() {
      const user = this.getUser();
      if (user && this.getToken()) {
        return `atom_chat_sessions__${user.username}`;
      }
      return GUEST_SESSIONS_KEY;
    },

    getActiveSessionStorageKey() {
      const user = this.getUser();
      if (user && this.getToken()) {
        return `atom_active_session_id__${user.username}`;
      }
      return GUEST_ACTIVE_KEY;
    },

    migrateLegacyGuestStorage() {
      try {
        if (localStorage.getItem(GUEST_SESSIONS_KEY) === null) {
          const legacyRaw = localStorage.getItem(LEGACY_SESSIONS_KEY);
          if (legacyRaw) {
            const parsed = safeParseJson(legacyRaw, []);
            if (hasAnyMessages(parsed)) {
              localStorage.setItem(GUEST_SESSIONS_KEY, JSON.stringify(parsed));
              const legacyActive = localStorage.getItem(LEGACY_ACTIVE_KEY);
              if (legacyActive && localStorage.getItem(GUEST_ACTIVE_KEY) === null) {
                localStorage.setItem(GUEST_ACTIVE_KEY, legacyActive);
              }
            }
          }
        }
      } catch (err) {
        console.warn('[ATOM] Legacy guest migration warning:', err);
      }
    },

    renderSidebarAccountWidget() {
      const sidebar = document.getElementById('app-sidebar');
      if (!sidebar) return;

      let box = document.getElementById('sidebar-account-box');
      if (!box) {
        box = document.createElement('div');
        box.id = 'sidebar-account-box';
        box.className = 'sidebar-account-box';
        const creditEl = sidebar.querySelector('.sidebar-credit');
        if (creditEl) {
          sidebar.insertBefore(box, creditEl);
        } else {
          sidebar.appendChild(box);
        }
      }

      const user = this.getUser();
      const loggedIn = this.isLoggedIn();
      box.classList.toggle('is-authenticated', loggedIn);

      if (loggedIn && user) {
        const displayName = user.display_name || user.username;
        const avatarChar = (displayName || user.username || 'A').charAt(0).toUpperCase();
        box.innerHTML = `
          <div class="sidebar-account-info" title="Masuk sebagai @${escapeHtml(user.username)} (Sinkronisasi Cloud Aktif)">
            <div class="sidebar-account-avatar">${escapeHtml(avatarChar)}</div>
            <div class="sidebar-account-meta">
              <div class="sidebar-account-name">@${escapeHtml(user.username)}</div>
              <div class="sidebar-account-sub">
                <span class="account-sync-led"></span>
                <span>Cloud Sync</span>
              </div>
            </div>
          </div>
          <div class="sidebar-account-actions">
            <button type="button" class="sidebar-account-btn btn-logout-icon" id="btn-sidebar-logout" title="Keluar (Logout)">Keluar</button>
          </div>
        `;
        box.querySelector('#btn-sidebar-logout')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.logout();
        });
      } else {
        box.innerHTML = `
          <div class="sidebar-account-info" style="cursor:pointer;" id="sidebar-guest-info" title="Mode Guest: Riwayat hanya tersimpan lokal di browser ini">
            <div class="sidebar-account-avatar">G</div>
            <div class="sidebar-account-meta">
              <div class="sidebar-account-name">Mode Guest</div>
              <div class="sidebar-account-sub">
                <span class="account-sync-led"></span>
                <span>Lokal Saja</span>
              </div>
            </div>
          </div>
          <div class="sidebar-account-actions">
            <button type="button" class="sidebar-account-btn" id="btn-sidebar-login">Masuk</button>
          </div>
        `;
        box.querySelector('#btn-sidebar-login')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.openAuthModal('login');
        });
        box.querySelector('#sidebar-guest-info')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.openAuthModal('login');
        });
      }
    },

    openAuthModal(initialTab = 'login') {
      document.getElementById('atom-auth-modal-overlay')?.remove();

      let activeTab = initialTab === 'register' ? 'register' : 'login';

      const overlayEl = document.createElement('div');
      overlayEl.className = 'privacy-disclaimer-overlay';
      overlayEl.id = 'atom-auth-modal-overlay';

      overlayEl.innerHTML = `
        <div class="privacy-disclaimer-card atom-auth-modal-card" role="dialog" aria-modal="true" aria-labelledby="auth-modal-title">
          <div class="disclaimer-card-header">
            <div class="disclaimer-title-wrap">
              <div class="disclaimer-icon-shield">👤</div>
              <div>
                <div class="disclaimer-title" id="auth-modal-title">AKUN & SINKRONISASI</div>
                <div style="font-size:0.65rem;color:var(--text-muted);font-family:var(--font-mono);letter-spacing:0.06em;">A.T.O.M. ACCOUNT VAULT</div>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <div class="disclaimer-lang-tabs">
                <button type="button" class="disclaimer-tab-btn ${activeTab === 'login' ? 'active' : ''}" data-auth-tab="login">Masuk</button>
                <button type="button" class="disclaimer-tab-btn ${activeTab === 'register' ? 'active' : ''}" data-auth-tab="register">Buat Akun</button>
              </div>
              <button type="button" id="btn-close-auth-modal" style="background:none;border:none;color:var(--text-muted);font-size:1.15rem;cursor:pointer;padding:2px 6px;" aria-label="Tutup">✕</button>
            </div>
          </div>

          <div class="disclaimer-card-body">
            <div class="auth-error-banner" id="auth-error-banner"></div>
            <form class="auth-form" id="atom-auth-form">
              <div class="auth-form-group">
                <label class="auth-label" for="auth-username">Username</label>
                <input type="text" class="auth-input" id="auth-username" placeholder="contoh: alif" autocomplete="username" required minlength="3" maxlength="32">
                <div class="auth-hint">3–32 karakter: huruf kecil, angka, titik, garis bawah, atau tanda hubung.</div>
              </div>

              <div class="auth-form-group" id="auth-displayname-group" style="display:${activeTab === 'register' ? 'flex' : 'none'};">
                <label class="auth-label" for="auth-displayname">Nama Tampilan (Opsional)</label>
                <input type="text" class="auth-input" id="auth-displayname" placeholder="Contoh: Alif Rahmadi" maxlength="48">
              </div>

              <div class="auth-form-group">
                <label class="auth-label" for="auth-password">Password / PIN</label>
                <input type="password" class="auth-input" id="auth-password" placeholder="Minimal 4 karakter atau PIN" autocomplete="${activeTab === 'register' ? 'new-password' : 'current-password'}" required minlength="4">
              </div>

              <label class="auth-merge-box">
                <input type="checkbox" id="auth-merge-guest" checked>
                <span>Simpan / gabungkan riwayat chat Guest saat ini ke akun saya</span>
              </label>

              <button type="submit" class="btn btn-primary auth-submit-btn" id="btn-auth-submit">
                ${activeTab === 'register' ? 'Buat Akun & Sinkronkan' : 'Masuk ke Akun'}
              </button>
            </form>
          </div>

          <div class="disclaimer-card-footer" style="justify-content:space-between;">
            <span style="font-size:0.72rem;color:var(--text-muted);line-height:1.4;">
              Mode Guest hanya menyimpan di browser ini. Login mengaktifkan penyimpanan cloud per akun.
            </span>
          </div>
        </div>
      `;

      document.body.appendChild(overlayEl);

      const closeModal = () => {
        overlayEl.style.opacity = '0';
        overlayEl.style.transition = 'opacity 0.2s ease';
        setTimeout(() => overlayEl.remove(), 210);
      };

      overlayEl.querySelector('#btn-close-auth-modal')?.addEventListener('click', closeModal);
      overlayEl.addEventListener('click', (e) => {
        if (e.target === overlayEl) closeModal();
      });

      const tabBtns = overlayEl.querySelectorAll('[data-auth-tab]');
      const displayGroup = overlayEl.querySelector('#auth-displayname-group');
      const submitBtn = overlayEl.querySelector('#btn-auth-submit');
      const passInput = overlayEl.querySelector('#auth-password');
      const errBanner = overlayEl.querySelector('#auth-error-banner');

      const setTab = (tab) => {
        activeTab = tab === 'register' ? 'register' : 'login';
        tabBtns.forEach(b => b.classList.toggle('active', b.dataset.authTab === activeTab));
        if (displayGroup) displayGroup.style.display = activeTab === 'register' ? 'flex' : 'none';
        if (submitBtn) submitBtn.textContent = activeTab === 'register' ? 'Buat Akun & Sinkronkan' : 'Masuk ke Akun';
        if (passInput) passInput.autocomplete = activeTab === 'register' ? 'new-password' : 'current-password';
        if (errBanner) {
          errBanner.textContent = '';
          errBanner.classList.remove('visible');
        }
      };

      tabBtns.forEach(btn => {
        btn.addEventListener('click', () => setTab(btn.dataset.authTab));
      });

      const form = overlayEl.querySelector('#atom-auth-form');
      form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = overlayEl.querySelector('#auth-username')?.value.trim() || '';
        const password = passInput?.value || '';
        const displayName = overlayEl.querySelector('#auth-displayname')?.value.trim() || '';
        const shouldMergeGuest = Boolean(overlayEl.querySelector('#auth-merge-guest')?.checked);

        if (errBanner) {
          errBanner.textContent = '';
          errBanner.classList.remove('visible');
        }

        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.textContent = 'Memproses...';
        }

        try {
          const endpoint = activeTab === 'register' ? '/api/accounts/register' : '/api/accounts/login';
          const bodyPayload = activeTab === 'register'
            ? { username, password, display_name: displayName || null }
            : { username, password };

          const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyPayload)
          });
          const data = await res.json().catch(() => ({}));

          if (!res.ok || !data.user || !data.token) {
            throw new Error(data.detail || 'Gagal memproses autentikasi akun.');
          }

          const user = data.user;
          let mergedGuest = false;

          if (shouldMergeGuest) {
            this.migrateLegacyGuestStorage();
            const guestRaw = localStorage.getItem(GUEST_SESSIONS_KEY) || localStorage.getItem(LEGACY_SESSIONS_KEY);
            const guestSessions = safeParseJson(guestRaw, []).filter(
              s => s && s.id && Array.isArray(s.messages) && s.messages.length > 0
            );
            if (guestSessions.length > 0) {
              const acctKey = `atom_chat_sessions__${user.username}`;
              const acctActiveKey = `atom_active_session_id__${user.username}`;
              const existingAcct = safeParseJson(localStorage.getItem(acctKey), []);
              const merged = mergeSessionsLists(existingAcct, guestSessions);
              localStorage.setItem(acctKey, JSON.stringify(merged));
              if (!localStorage.getItem(acctActiveKey) && merged[0]?.id) {
                localStorage.setItem(acctActiveKey, merged[0].id);
              }
              mergedGuest = true;
            }
          }

          localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
          localStorage.setItem(AUTH_TOKEN_KEY, data.token);

          this.renderSidebarAccountWidget();
          closeModal();

          window.dispatchEvent(new CustomEvent('atom:auth-changed', {
            detail: { user, mergedGuest }
          }));

          showToast(`Selamat datang, ${user.display_name || user.username}! Sinkronisasi akun aktif.`, 'success');
        } catch (err) {
          if (errBanner) {
            errBanner.textContent = err.message || 'Terjadi kesalahan saat masuk.';
            errBanner.classList.add('visible');
          }
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = activeTab === 'register' ? 'Buat Akun & Sinkronkan' : 'Masuk ke Akun';
          }
        }
      });

      setTimeout(() => overlayEl.querySelector('#auth-username')?.focus(), 50);
    },

    logout() {
      localStorage.removeItem(AUTH_USER_KEY);
      localStorage.removeItem(AUTH_TOKEN_KEY);
      this.renderSidebarAccountWidget();
      window.dispatchEvent(new CustomEvent('atom:auth-changed', {
        detail: { user: null }
      }));
      showToast('Anda telah keluar. Beralih ke Mode Guest (penyimpanan lokal).', 'info');
    },

    async verifySession() {
      if (_sessionVerifiedOnce) return;
      _sessionVerifiedOnce = true;
      const token = this.getToken();
      if (!token) return;
      try {
        const res = await fetch('/api/accounts/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        if (data && data.authenticated === false) {
          localStorage.removeItem(AUTH_USER_KEY);
          localStorage.removeItem(AUTH_TOKEN_KEY);
          this.renderSidebarAccountWidget();
          window.dispatchEvent(new CustomEvent('atom:auth-changed', { detail: { user: null } }));
        } else if (data && data.authenticated === true && data.user) {
          localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
          this.renderSidebarAccountWidget();
        }
      } catch {
        // Offline-safe: do not clear token on network error
      }
    }
  };

  AccountManager.migrateLegacyGuestStorage();
  window.ATOM_Account = AccountManager;
})();

// ─── Background Chat Bridge (Cross-Tab & Cross-Page Continuity) ──────────────
(function initChatBackgroundModule() {
  const DB_NAME = 'atom_bg_db';
  const DB_VERSION = 1;
  const STORE_NAME = 'chat_jobs';
  const CHANNEL_NAME = 'atom_chat_bg';
  const COMMITTED_KEY = 'atom_committed_chat_jobs';
  const UNREAD_SESSIONS_KEY = 'atom_chat_unread_sessions';

  let _initialized = false;
  let _readyResolve = null;
  const _readyPromise = new Promise(resolve => {
    _readyResolve = resolve;
  });

  let _swReg = null;
  let _bc = null;
  const _inPageControllers = new Map();
  const _inPageRunningJobs = new Map();
  const _ackResolvers = new Map();

  function isChatPage() {
    return Boolean(document.getElementById('messages-area'));
  }

  function safeJsonParse(raw, fallback) {
    try {
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }

  function openBgDb() {
    if (typeof indexedDB === 'undefined') return Promise.resolve(null);
    return new Promise((resolve) => {
      try {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = () => {
          const db = req.result;
          if (!db.objectStoreNames.contains(STORE_NAME)) {
            db.createObjectStore(STORE_NAME, { keyPath: 'jobId' });
          }
        };
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => resolve(null);
      } catch {
        resolve(null);
      }
    });
  }

  async function idbGetAllJobs() {
    const db = await openBgDb();
    if (!db) return [];
    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const req = tx.objectStore(STORE_NAME).getAll();
        req.onsuccess = () => {
          db.close();
          resolve(Array.isArray(req.result) ? req.result : []);
        };
        req.onerror = () => {
          db.close();
          resolve([]);
        };
      } catch {
        db.close();
        resolve([]);
      }
    });
  }

  async function idbDeleteJob(jobId) {
    const db = await openBgDb();
    if (!db) return;
    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).delete(jobId);
        tx.oncomplete = () => {
          db.close();
          resolve();
        };
        tx.onerror = () => {
          db.close();
          resolve();
        };
      } catch {
        db.close();
        resolve();
      }
    });
  }

  function isJobCommitted(jobId) {
    const list = safeJsonParse(localStorage.getItem(COMMITTED_KEY), []);
    return Array.isArray(list) && list.includes(jobId);
  }

  function markJobCommittedLocally(jobId) {
    const list = safeJsonParse(localStorage.getItem(COMMITTED_KEY), []);
    const next = Array.isArray(list) ? list.filter(id => id !== jobId) : [];
    next.unshift(jobId);
    try {
      localStorage.setItem(COMMITTED_KEY, JSON.stringify(next.slice(0, 60)));
    } catch {}
  }

  function getUnreadSessionIds() {
    const list = safeJsonParse(localStorage.getItem(UNREAD_SESSIONS_KEY), []);
    return Array.isArray(list) ? list : [];
  }

  function addUnreadSession(sessionId) {
    if (!sessionId) return;
    const list = getUnreadSessionIds();
    if (!list.includes(sessionId)) {
      list.push(sessionId);
      try {
        localStorage.setItem(UNREAD_SESSIONS_KEY, JSON.stringify(list));
      } catch {}
    }
  }

  function markSessionRead(sessionId) {
    if (!sessionId) return;
    const list = getUnreadSessionIds().filter(id => id !== sessionId);
    try {
      localStorage.setItem(UNREAD_SESSIONS_KEY, JSON.stringify(list));
    } catch {}
    refreshNavChatIndicator();
  }

  function buildAssistantMessage(job) {
    if (job.status === 'completed') {
      const res = job.result || {};
      return {
        role: 'assistant',
        content: res.response || '',
        thinking: Array.isArray(res.thinking) ? res.thinking : [],
        model: res.model || '',
        jobId: job.jobId
      };
    }
    if (job.status === 'aborted') {
      return {
        role: 'assistant',
        content: '_⚠️ Respon AI dihentikan oleh pengguna (Request aborted)._',
        thinking: [],
        model: 'Aborted',
        jobId: job.jobId
      };
    }
    return {
      role: 'assistant',
      content: `[ERROR] ${job.error || 'Gagal menghubungi API. Periksa koneksi.'}`,
      thinking: [],
      model: '',
      jobId: job.jobId
    };
  }

  async function commitFinishedJob(job) {
    if (!job || !job.jobId || job.status === 'running') return false;
    if (isJobCommitted(job.jobId)) {
      await idbDeleteJob(job.jobId);
      return false;
    }

    // Reserve jobId immediately to prevent duplicate commits across tabs/navigations
    markJobCommittedLocally(job.jobId);

    const assistantMsg = buildAssistantMessage(job);
    const storageKey = job.storageKey || window.ATOM_Account?.getChatStorageKey() || 'atom_chat_sessions_guest';
    let sessions = safeJsonParse(localStorage.getItem(storageKey), []);
    if (!Array.isArray(sessions)) sessions = [];

    let targetSession = sessions.find(s => s && s.id === job.sessionId);
    if (!targetSession) {
      const rawTitle = (job.displayPrompt || 'Percakapan Baru').trim();
      const title = rawTitle.length > 30 ? rawTitle.slice(0, 30) + '...' : (rawTitle || 'Percakapan Baru');
      targetSession = {
        id: job.sessionId,
        title,
        updatedAt: Date.now(),
        messages: []
      };
      sessions.unshift(targetSession);
    }

    if (!Array.isArray(targetSession.messages)) {
      targetSession.messages = [];
    }

    const alreadyInMessages = targetSession.messages.some(m => m && m.jobId === job.jobId);
    if (!alreadyInMessages) {
      targetSession.messages.push(assistantMsg);
      targetSession.updatedAt = Date.now();
      sessions = [targetSession, ...sessions.filter(s => s && s.id !== job.sessionId)];
      try {
        localStorage.setItem(storageKey, JSON.stringify(sessions));
        if (storageKey === 'atom_chat_sessions_guest') {
          localStorage.setItem('atom_chat_history', JSON.stringify(targetSession.messages.slice(-50)));
        }
      } catch (e) {
        console.warn('[ATOM] Background commit localStorage error:', e);
      }
    }

    // Sync to backend if authenticated
    const token = job.authToken || window.ATOM_Account?.getToken();
    if (token) {
      try {
        fetch('/api/sessions/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            sessions,
            active_id: job.sessionId,
            token,
            force_overwrite: false
          }),
          keepalive: true
        }).catch(() => {});
      } catch {}
    }

    // Telemetry logging
    const logPrompt = job.logPrompt || job.displayPrompt || '';
    if (typeof window.logTelemetry === 'function') {
      if (job.status === 'completed') {
        window.logTelemetry({
          user_input: logPrompt,
          model_used: job.result?.model || 'unknown',
          response_time: job.result?.duration || 0,
          status: 'SUCCESS',
          ai_response: assistantMsg.content
        });
      } else if (job.status === 'aborted') {
        window.logTelemetry({
          user_input: logPrompt,
          model_used: 'Aborted',
          response_time: 0,
          status: 'ABORTED',
          ai_response: assistantMsg.content
        });
      } else {
        window.logTelemetry({
          user_input: logPrompt,
          model_used: 'ERROR',
          response_time: 0,
          status: 'ERROR',
          ai_response: assistantMsg.content
        });
      }
    }

    await idbDeleteJob(job.jobId);
    postToServiceWorker({ type: 'CHAT_MARK_COMMITTED', jobId: job.jobId }).catch(() => {});

    if (!isChatPage()) {
      addUnreadSession(job.sessionId);
      if (typeof window.showToast === 'function') {
        if (job.status === 'completed') {
          window.showToast('✅ A.T.O.M. selesai menjawab di tab Chat!', 'success', 4500);
        } else if (job.status === 'error') {
          window.showToast('⚠️ Proses chat mengalami kendala. Cek tab Chat.', 'warning', 4500);
        }
      }
    }

    window.dispatchEvent(new CustomEvent('atom:chat-job-committed', {
      detail: { job, assistantMsg }
    }));

    await refreshNavChatIndicator();
    return true;
  }

  async function pingServiceWorker() {
    const sw = await getActiveServiceWorker(400);
    if (!sw) return null;
    return new Promise((resolve) => {
      let settled = false;
      const timer = setTimeout(() => {
        if (!settled) {
          settled = true;
          resolve(null);
        }
      }, 600);
      try {
        const mc = new MessageChannel();
        mc.port1.onmessage = (ev) => {
          if (!settled) {
            settled = true;
            clearTimeout(timer);
            resolve(ev.data || null);
          }
        };
        sw.postMessage({ type: 'CHAT_PING' }, [mc.port2]);
      } catch {
        if (!settled) {
          settled = true;
          clearTimeout(timer);
          resolve(null);
        }
      }
    });
  }

  async function getRunningJobs(verifyWithSw = false) {
    if (verifyWithSw) {
      await pingServiceWorker();
    }
    const idbJobs = await idbGetAllJobs();
    const runningMap = new Map();
    idbJobs.forEach(j => {
      if (j && j.status === 'running') {
        runningMap.set(j.jobId, j);
      }
    });
    _inPageRunningJobs.forEach((j, id) => {
      if (j && j.status === 'running') {
        runningMap.set(id, j);
      }
    });
    return Array.from(runningMap.values());
  }

  async function reconcileFinishedJobs() {
    await pingServiceWorker();
    const allJobs = await idbGetAllJobs();
    for (const job of allJobs) {
      if (job && job.status && job.status !== 'running') {
        await commitFinishedJob(job);
      }
    }
    await refreshNavChatIndicator();
  }

  async function refreshNavChatIndicator() {
    const chatNavLink = document.getElementById('nav-chat') || document.querySelector('.sidebar-nav a[href="index.html"]');
    if (!chatNavLink) return;

    const running = await getRunningJobs(false);
    const unread = getUnreadSessionIds();

    let badge = chatNavLink.querySelector('.nav-chat-bg-badge');
    if (running.length > 0) {
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'nav-chat-bg-badge';
        chatNavLink.appendChild(badge);
      }
      badge.className = 'nav-chat-bg-badge is-processing';
      badge.innerHTML = `<span class="nav-chat-bg-dot"></span><span>Proses</span>`;
      chatNavLink.classList.add('has-bg-activity');
    } else if (!isChatPage() && unread.length > 0) {
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'nav-chat-bg-badge';
        chatNavLink.appendChild(badge);
      }
      badge.className = 'nav-chat-bg-badge is-unread';
      badge.innerHTML = `<span class="nav-chat-bg-dot"></span><span>Selesai</span>`;
      chatNavLink.classList.add('has-bg-activity');
    } else {
      badge?.remove();
      chatNavLink.classList.remove('has-bg-activity');
    }
  }

  async function getActiveServiceWorker(timeoutMs = 1500) {
    if (!('serviceWorker' in navigator)) return null;
    try {
      if (!_swReg) {
        _swReg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
      }
      if (_swReg.active) return _swReg.active;

      const readyPromise = navigator.serviceWorker.ready.then(reg => {
        _swReg = reg;
        return reg.active || navigator.serviceWorker.controller || null;
      });
      const timeoutPromise = new Promise(resolve => setTimeout(() => resolve(null), timeoutMs));
      return await Promise.race([readyPromise, timeoutPromise]);
    } catch {
      return null;
    }
  }

  async function postToServiceWorker(message) {
    const sw = await getActiveServiceWorker(800);
    if (!sw) return false;
    try {
      sw.postMessage(message);
      return true;
    } catch {
      return false;
    }
  }

  function handleBgMessage(data) {
    if (!data || !data.type) return;
    if (data.type === 'CHAT_JOB_ACK' && data.jobId) {
      const resolver = _ackResolvers.get(data.jobId);
      if (resolver) {
        _ackResolvers.delete(data.jobId);
        resolver(true);
      }
    } else if (data.type === 'CHAT_JOB_STARTED' && data.job) {
      refreshNavChatIndicator();
      window.dispatchEvent(new CustomEvent('atom:chat-job-started', { detail: { job: data.job } }));
    } else if (data.type === 'CHAT_JOB_DONE' && data.job) {
      commitFinishedJob(data.job);
    }
  }

  async function runInPageFallback(job) {
    const controller = new AbortController();
    _inPageControllers.set(job.jobId, controller);
    const runningRecord = { ...job, status: 'running', startedAt: Date.now() };
    _inPageRunningJobs.set(job.jobId, runningRecord);
    refreshNavChatIndicator();
    window.dispatchEvent(new CustomEvent('atom:chat-job-started', { detail: { job: runningRecord } }));

    let finishedRecord;
    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(job.body),
        signal: controller.signal
      });
      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.error || errJson.message || `HTTP ${resp.status}`);
      }
      const result = await resp.json();
      finishedRecord = { ...runningRecord, status: 'completed', result, finishedAt: Date.now() };
    } catch (err) {
      if (err && err.name === 'AbortError') {
        finishedRecord = { ...runningRecord, status: 'aborted', finishedAt: Date.now() };
      } else {
        finishedRecord = {
          ...runningRecord,
          status: 'error',
          error: (err && err.message) ? err.message : 'Gagal menghubungi API. Periksa koneksi.',
          finishedAt: Date.now()
        };
      }
    } finally {
      _inPageControllers.delete(job.jobId);
      _inPageRunningJobs.delete(job.jobId);
    }

    await commitFinishedJob(finishedRecord);
  }

  async function startJob(job) {
    const sw = await getActiveServiceWorker(1500);
    if (sw) {
      const acked = await new Promise((resolve) => {
        const timer = setTimeout(() => {
          _ackResolvers.delete(job.jobId);
          resolve(false);
        }, 900);
        _ackResolvers.set(job.jobId, (ok) => {
          clearTimeout(timer);
          resolve(ok);
        });
        try {
          sw.postMessage({ type: 'CHAT_START', job });
        } catch {
          clearTimeout(timer);
          _ackResolvers.delete(job.jobId);
          resolve(false);
        }
      });

      if (acked) {
        refreshNavChatIndicator();
        return { mode: 'sw', jobId: job.jobId };
      }
    }

    // Fallback: in-page fetch if Service Worker is unavailable (e.g. non-HTTPS LAN IP)
    runInPageFallback(job);
    return { mode: 'page', jobId: job.jobId };
  }

  async function abortJob(jobId) {
    if (!jobId) return;
    const ctrl = _inPageControllers.get(jobId);
    if (ctrl) {
      ctrl.abort();
    }
    await postToServiceWorker({ type: 'CHAT_ABORT', jobId });
  }

  async function init() {
    if (_initialized) return _readyPromise;
    _initialized = true;

    if (typeof BroadcastChannel !== 'undefined') {
      _bc = new BroadcastChannel(CHANNEL_NAME);
      _bc.onmessage = (event) => handleBgMessage(event.data);
    }

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => handleBgMessage(event.data));
      await getActiveServiceWorker(1200);
    }

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        reconcileFinishedJobs();
      }
    });

    window.addEventListener('storage', (e) => {
      if (e.key === UNREAD_SESSIONS_KEY || e.key === COMMITTED_KEY) {
        refreshNavChatIndicator();
      }
    });

    await reconcileFinishedJobs();
    _readyResolve?.();
    return _readyPromise;
  }

  window.ATOM_ChatBackground = {
    init,
    readyPromise: _readyPromise,
    startJob,
    abortJob,
    getRunningJobs,
    reconcileFinishedJobs,
    refreshNavChatIndicator,
    getUnreadSessionIds,
    markSessionRead
  };
})();

function initGlobalShellWidgets() {
  applySavedPreferences();
  window.ATOM_Account?.renderSidebarAccountWidget();
  window.ATOM_Account?.verifySession();
  window.ATOM_ChatBackground?.init();
  // Tampilkan Disclaimer Privasi jika belum pernah ditutup dengan opsi "Do not show again"
  showPrivacyDisclaimerModal(false);
}

document.addEventListener('DOMContentLoaded', initGlobalShellWidgets);
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  initGlobalShellWidgets();
}

console.log('%c⚛️ A.T.O.M. v4.0 CORTEX INITIALIZED', 'color:#C9A227;font-size:14px;font-weight:bold;');

