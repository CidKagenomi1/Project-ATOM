/**
 * A.T.O.M. — Roleplay (RP Model) Dedicated Logic
 * Focused on creative ideation, strategic co-thinking, and roleplay simulations
 */

// ─── Persona Definitions ───────────────────────────────────
const RP_PERSONAS = [
  {
    id: 'auto',
    title: 'Auto Discovery Guide',
    roleName: 'Socratic Brainstorming Guide',
    icon: '✨',
    desc: 'Bantu memancing topik & mengarahkan ide bila bingung',
    badge: 'Auto Discovery',
    systemPrompt: `ROLEPLAY MODE: Kamu adalah Socratic Ideation Coach & Creative Catalyst kelas dunia.
KONDISI PENGGUNA: Pengguna sedang ingin menciptakan sesuatu yang besar dan inovatif, namun belum tahu pasti topiknya atau masih bingung harus mulai dari mana.
SIKAP: Eksploratif, ramah, penuh rasa ingin tahu, tidak menggurui tapi mengajukan 1-2 pertanyaan pemantik yang cerdas untuk menggali minat/kegelisahan pengguna.
PANGGILAN: Sapa pengguna sebagai 'Partner' atau 'Visionary'.
FOKUS: Bantu pengguna menemukan ide orisinal dari hobi, masalah sehari-hari, atau tren teknologi masa depan. Tawarkan 3 opsi bidang menarik jika pengguna benar-benar buntu.`
  },
  {
    id: 'co_founder',
    title: 'Chief Innovation Officer',
    roleName: 'Strategic Co-Founder',
    icon: '🚀',
    desc: 'Mitra visioner pengembangan ide gila',
    badge: 'Co-Founder Mode',
    systemPrompt: `ROLEPLAY MODE: Kamu adalah Chief Innovation Officer (CIO) sekaligus Co-Founder visioner perusahaan rintisan terkemuka.
SIKAP: Sangat antusias, cerdas, menantang ide pengguna agar lebih berdampak, menyusun strategi produk futuristik, dan berpikir besar (think big).
PANGGILAN: Sapa pengguna sebagai 'Partner', 'Pak Direktur', atau 'Founder'.
FOKUS: Bantu memvalidasi ide besar pengguna, carikan keunikan produk (USP), dan susun roadmap implementasi nyata.`
  },
  {
    id: 'operations_director',
    title: 'Executive Operations',
    roleName: 'Operations Director',
    icon: '💼',
    desc: 'Manajemen SOP, tim & eksekusi bisnis',
    badge: 'Operations Mode',
    systemPrompt: `ROLEPLAY MODE: Kamu adalah Senior Operations Director perusahaan skala besar yang sangat disiplin dan terstruktur.
SIKAP: Profesional, pragmatis, teliti, berorientasi hasil dan efisiensi eksekusi.
PANGGILAN: Sapa pengguna dengan hormat sebagai 'Direktur' atau 'Ketua Tim'.
FOKUS: Memecah ide abstrak pengguna menjadi alur kerja operasional nyata (SOP), mitigasi risiko, alokasi anggaran, dan timeline sprint tim.`
  },
  {
    id: 'shark_investor',
    title: 'Shark Angel Investor',
    roleName: 'Venture Capitalist',
    icon: '💰',
    desc: 'Uji kelayakan bisnis & kritik tajam',
    badge: 'Investor Shark',
    systemPrompt: `ROLEPLAY MODE: Kamu adalah Investor Angel / Partner Venture Capital (ala Shark Tank) yang berpengalaman dan kritis.
SIKAP: Tajam, analitis, tidak mudah puas, mengapresiasi inovasi nyata tapi cepat mendeteksi kelemahan model bisnis.
PANGGILAN: Sapa pengguna sebagai 'Founder'.
FOKUS: Tantang kelemahan ide pengguna: "Apa parit pertahananmu (moat)?", "Bagaimana unit economics-nya?", "Mengapa ini bisa berkembang 10x lipat?".`
  },
  {
    id: 'tech_architect',
    title: 'Chief Tech Architect',
    roleName: 'R&D Engineering Lead',
    icon: '⚙️',
    desc: 'Arsitektur sistem, AI stack & inovasi',
    badge: 'Tech Architect',
    systemPrompt: `ROLEPLAY MODE: Kamu adalah Lead Tech Architect & R&D Scientist kelas dunia.
SIKAP: Visioner teknis, mendalam, menyukai teknologi terdepan (Cutting-edge AI, High-Performance Systems, Cloud Native).
PANGGILAN: Sapa pengguna sebagai 'Lead' atau 'Chief'.
FOKUS: Merancang blueprint teknis dari ide pengguna: pipeline AI, pemilihan arsitektur mikro, skalabilitas database, dan spesifikasi engineering.`
  },
  {
    id: 'creative_director',
    title: 'Avant-Garde Creative Lead',
    roleName: 'Brand & UX Visionary',
    icon: '🎨',
    desc: 'Narasi brand, storytelling & daya tarik emosional',
    badge: 'Creative Director',
    systemPrompt: `ROLEPLAY MODE: Kamu adalah Avant-Garde Creative Director kelas dunia.
SIKAP: Kreatif, berani, berestetika tinggi, mahir dalam seni storytelling dan menciptakan 'hype' atau ketertarikan pasar.
PANGGILAN: Sapa pengguna sebagai 'Visionary' atau 'Direktur Kreatif'.
FOKUS: Merancang nama brand yang ikonik, konsep visual, positioning pasar yang memukau, dan pengalaman pengguna emosional.`
  }
];

let activePersonaId = 'auto';

// ─── State ────────────────────────────────────────────────
let rpSessions     = [];
let currentRpSessionId = null;
let rpChatHistory  = [];
let contextFiles   = [];
let isProcessing   = false;

// ─── DOM Elements ─────────────────────────────────────────
const messagesArea     = document.getElementById('rp-messages-area');
const emptyChatDiv     = document.getElementById('rp-empty-chat');
const chatInputEl      = document.getElementById('rp-chat-input');
const btnSend          = document.getElementById('btn-send');
const btnAttach        = document.getElementById('btn-attach');
const fileUploadEl     = document.getElementById('file-upload');
const attachedFilesEl  = document.getElementById('attached-files');
const btnClearRp       = document.getElementById('btn-clear-rp');
const btnNewRpSession  = document.getElementById('btn-new-rp-session');
const rpSessionsList   = document.getElementById('rp-sessions-list');
const rpRoleSelectEl   = document.getElementById('rp-role-select');

// ─── Init ─────────────────────────────────────────────────
function init() {
  initRoleSelect();
  loadRpSessions();
  updateEmptyState();
  updateSendButton();
  renderRpSessionsSidebar();

  btnNewRpSession?.addEventListener('click', () => {
    createNewRpSession();
  });

  btnClearRp?.addEventListener('click', clearCurrentRpChat);

  // Scroll to bottom
  setTimeout(() => scrollToBottom(messagesArea), 100);
}

// ─── Input Handlers ───────────────────────────────────────
chatInputEl?.addEventListener('input', () => {
  autoResize(chatInputEl);
  updateSendButton();
});

chatInputEl?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!isProcessing && chatInputEl.value.trim()) {
      sendRpMessage();
    }
  }
});

btnSend?.addEventListener('click', sendRpMessage);

// File attachment
btnAttach?.addEventListener('click', () => fileUploadEl?.click());

fileUploadEl?.addEventListener('change', (e) => {
  const files = Array.from(e.target.files || []);
  files.forEach(readAndAttachFile);
  e.target.value = '';
});

// Clipboard paste
chatInputEl?.addEventListener('paste', (e) => {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (let i = 0; i < items.length; i++) {
    if (items[i].kind === 'file') {
      const file = items[i].getAsFile();
      if (file) {
        e.preventDefault();
        readAndAttachFile(file);
      }
    }
  }
});

function readAndAttachFile(file) {
  const reader = new FileReader();
  const isImage = file.type?.startsWith('image/');
  reader.onload = (e) => {
    contextFiles.push({
      name: file.name || 'attachment',
      type: file.type,
      content: e.target.result
    });
    renderAttachedFiles();
    updateSendButton();
  };
  if (isImage) reader.readAsDataURL(file);
  else reader.readAsText(file);
}

function renderAttachedFiles() {
  if (!attachedFilesEl) return;
  attachedFilesEl.innerHTML = '';
  contextFiles.forEach((f, idx) => {
    const item = document.createElement('div');
    item.className = 'attached-file';
    item.innerHTML = `<span>📎 ${escapeHtml(f.name)}</span><button onclick="removeFile(${idx})">✕</button>`;
    attachedFilesEl.appendChild(item);
  });
}

window.removeFile = function(index) {
  contextFiles.splice(index, 1);
  renderAttachedFiles();
  updateSendButton();
};

// ─── Role Selection Dropdown (Vertical / Side-by-Side) ────
function initRoleSelect() {
  if (!rpRoleSelectEl) return;
  rpRoleSelectEl.value = activePersonaId;

  rpRoleSelectEl.addEventListener('change', (e) => {
    selectRolePersona(e.target.value);
  });
}

function selectRolePersona(personaId) {
  activePersonaId = personaId;
  const selected = RP_PERSONAS.find(p => p.id === personaId) || RP_PERSONAS[0];

  if (rpRoleSelectEl) {
    rpRoleSelectEl.value = personaId;
  }

  const cur = rpSessions.find(s => s.id === currentRpSessionId);
  if (cur) {
    cur.personaId = personaId;
    saveRpSessions();
  }

  showToast(`Role aktif: ${selected.title}`, 'info');
}

// ─── Sending Message ──────────────────────────────────────
async function sendRpMessage() {
  if (isProcessing) return;
  const prompt = chatInputEl?.value.trim();
  const hasFiles = contextFiles.length > 0;
  if (!prompt && !hasFiles) return;

  isProcessing = true;
  chatInputEl.value = '';
  autoResize(chatInputEl);
  updateSendButton();

  const displayPrompt = prompt || '[Lampiran Dikirim]';
  renderMessage('user', displayPrompt);
  rpChatHistory.push({ role: 'user', content: displayPrompt });
  updateEmptyState();
  scrollToBottom(messagesArea);

  const typingEl = showTypingIndicator();

  try {
    const currentPersona = RP_PERSONAS.find(p => p.id === activePersonaId) || RP_PERSONAS[0];
    
    // Inject persona pre-prompt
    let apiHistory = rpChatHistory.slice(0, -1).map(m => ({ role: m.role, content: m.content }));
    apiHistory = [
      { role: 'user', content: `[INSTRUKSI ROLEPLAY TINGGI]:\n${currentPersona.systemPrompt}` },
      { role: 'assistant', content: `Siap, saya sekarang bertindak sebagai ${currentPersona.title}. Mari kita kembangkan ide Anda.` },
      ...apiHistory
    ];

    const modelSelectEl = document.getElementById('model-select');
    const selectedModel = modelSelectEl ? modelSelectEl.value : 'auto';

    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        history: apiHistory,
        files: contextFiles.map(f => ({ name: f.name, content: f.content })),
        model_preference: selectedModel
      })
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
      throw new Error(err.error || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    typingEl?.remove();

    renderMessage('assistant', data.response, data.thinking || [], data.model || '', currentPersona.badge);
    rpChatHistory.push({
      role: 'assistant',
      content: data.response,
      thinking: data.thinking || [],
      model: data.model || '',
      personaBadge: currentPersona.badge
    });

    logTelemetry({
      user_input: `[RP: ${currentPersona.badge}] ` + displayPrompt,
      model_used: data.model || 'unknown',
      response_time: data.duration || 0,
      status: 'SUCCESS',
      ai_response: data.response
    });

    saveRpHistory();
    contextFiles = [];
    renderAttachedFiles();

  } catch (err) {
    typingEl?.remove();
    const errMsg = `[ERROR] ${err.message || 'Gagal menghubungi API.'}`;
    renderMessage('assistant', errMsg);
  }

  isProcessing = false;
  updateSendButton();
  scrollToBottom(messagesArea);
}

// ─── Render Message ────────────────────────────────────────
function renderMessage(role, content, thinking = [], model = '', personaBadge = '') {
  if (!messagesArea) return;
  const isUser = role === 'user';
  const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;

  const avatar = isUser ? '👤' : '🎭';
  const bubbleContent = isUser
    ? `<p style="margin:0;color:inherit;">${escapeHtml(content).replace(/\n/g, '<br>')}</p>`
    : renderMarkdown(content);

  const modelBadge = (!isUser && model)
    ? `<span class="model-badge ${model.toLowerCase().includes('groq') ? 'groq' : 'gemini'}">${escapeHtml(model)}</span>`
    : '';

  const personaTag = (!isUser && personaBadge)
    ? `<span class="persona-badge-tag">🎭 ${escapeHtml(personaBadge)}</span>`
    : '';

  const msgEl = document.createElement('div');
  msgEl.className = `chat-message ${role}`;
  msgEl.id = msgId;
  msgEl.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-body">
      ${personaTag}
      <div class="message-bubble">${bubbleContent}</div>
      ${modelBadge}
    </div>
  `;
  messagesArea.appendChild(msgEl);
}

function showTypingIndicator() {
  const el = document.createElement('div');
  el.className = 'typing-indicator';
  el.innerHTML = `
    <div class="message-avatar">🎭</div>
    <div class="typing-dots"><span></span><span></span><span></span></div>
  `;
  messagesArea.appendChild(el);
  scrollToBottom(messagesArea);
  return el;
}

// ─── Session Management ────────────────────────────────────
function loadRpSessions() {
  try {
    const raw = localStorage.getItem('atom_rp_sessions');
    rpSessions = raw ? JSON.parse(raw) : [];
  } catch { rpSessions = []; }

  const lastId = localStorage.getItem('atom_rp_active_session_id');
  const found = rpSessions.find(s => s.id === lastId);
  if (found) {
    currentRpSessionId = found.id;
    rpChatHistory = found.messages || [];
    if (found.personaId) selectRolePersona(found.personaId);
  } else if (rpSessions.length > 0) {
    currentRpSessionId = rpSessions[0].id;
    rpChatHistory = rpSessions[0].messages || [];
    if (rpSessions[0].personaId) selectRolePersona(rpSessions[0].personaId);
  } else {
    createNewRpSession(false);
    return;
  }

  renderCurrentMessages();
}

function saveRpSessions() {
  try {
    localStorage.setItem('atom_rp_sessions', JSON.stringify(rpSessions));
    if (currentRpSessionId) {
      localStorage.setItem('atom_rp_active_session_id', currentRpSessionId);
    }
  } catch {}
}

function saveRpHistory() {
  if (!currentRpSessionId) currentRpSessionId = 'rp_' + Date.now();
  let session = rpSessions.find(s => s.id === currentRpSessionId);
  const curP = RP_PERSONAS.find(p => p.id === activePersonaId) || RP_PERSONAS[0];

  if (!session) {
    const firstMsg = rpChatHistory.find(m => m.role === 'user');
    let title = firstMsg ? firstMsg.content.slice(0, 26) : 'Sesi Ideation';
    session = {
      id: currentRpSessionId,
      title: `[${curP.icon}] ` + (title || 'Sesi Roleplay'),
      updatedAt: Date.now(),
      personaId: activePersonaId,
      messages: rpChatHistory
    };
    rpSessions.unshift(session);
  } else {
    session.messages = rpChatHistory;
    session.updatedAt = Date.now();
    session.personaId = activePersonaId;
    if (session.title.includes('Sesi Baru')) {
      const firstMsg = rpChatHistory.find(m => m.role === 'user');
      if (firstMsg) {
        session.title = `[${curP.icon}] ` + firstMsg.content.slice(0, 26);
      }
    }
    rpSessions = [session, ...rpSessions.filter(s => s.id !== currentRpSessionId)];
  }

  saveRpSessions();
  renderRpSessionsSidebar();
}

function createNewRpSession(notify = true) {
  currentRpSessionId = 'rp_' + Date.now();
  rpChatHistory = [];
  contextFiles = [];

  const curP = RP_PERSONAS.find(p => p.id === activePersonaId) || RP_PERSONAS[0];
  const newSession = {
    id: currentRpSessionId,
    title: `[${curP.icon}] Sesi Baru`,
    updatedAt: Date.now(),
    personaId: activePersonaId,
    messages: []
  };

  rpSessions.unshift(newSession);
  saveRpSessions();
  renderCurrentMessages();
  renderRpSessionsSidebar();
  updateEmptyState();
  updateSendButton();

  if (chatInputEl) {
    chatInputEl.value = '';
    chatInputEl.focus();
  }

  // Auto close sidebar on mobile
  if (typeof closeSidebar === 'function' && window.innerWidth <= 768) {
    closeSidebar();
  }

  if (notify) showToast('Sesi RP baru dimulai', 'info');
}

function switchRpSession(sessionId) {
  if (sessionId === currentRpSessionId) {
    if (typeof closeSidebar === 'function' && window.innerWidth <= 768) closeSidebar();
    return;
  }
  const target = rpSessions.find(s => s.id === sessionId);
  if (!target) return;

  currentRpSessionId = target.id;
  rpChatHistory = target.messages || [];
  contextFiles = [];
  if (target.personaId) selectRolePersona(target.personaId);

  localStorage.setItem('atom_rp_active_session_id', currentRpSessionId);
  renderCurrentMessages();
  renderRpSessionsSidebar();
  updateEmptyState();
  updateSendButton();

  // Auto close sidebar on mobile
  if (typeof closeSidebar === 'function' && window.innerWidth <= 768) {
    closeSidebar();
  }
}

function deleteRpSession(sessionId, event) {
  if (event) event.stopPropagation();
  if (!confirm('Hapus sesi roleplay ini?')) return;

  rpSessions = rpSessions.filter(s => s.id !== sessionId);
  if (currentRpSessionId === sessionId) {
    if (rpSessions.length > 0) {
      currentRpSessionId = rpSessions[0].id;
      rpChatHistory = rpSessions[0].messages || [];
    } else {
      createNewRpSession(false);
      return;
    }
  }

  saveRpSessions();
  renderCurrentMessages();
  renderRpSessionsSidebar();
  updateEmptyState();
  showToast('Sesi dihapus', 'success');
}

function renderCurrentMessages() {
  if (!messagesArea) return;
  const header = messagesArea.querySelector('.atom-header');
  messagesArea.innerHTML = '';
  if (header) messagesArea.appendChild(header);

  rpChatHistory.forEach(msg => {
    renderMessage(msg.role, msg.content, msg.thinking || [], msg.model || '', msg.personaBadge || '');
  });

  if (emptyChatDiv) {
    messagesArea.appendChild(emptyChatDiv);
    emptyChatDiv.style.display = rpChatHistory.length === 0 ? '' : 'none';
  }

  renderAttachedFiles();
  setTimeout(() => scrollToBottom(messagesArea), 50);
}

function renderRpSessionsSidebar() {
  if (!rpSessionsList) return;
  rpSessionsList.innerHTML = '';

  if (rpSessions.length === 0) {
    const el = document.createElement('div');
    el.className = 'empty-sessions';
    el.textContent = 'Belum ada sesi RP';
    rpSessionsList.appendChild(el);
    return;
  }

  rpSessions.forEach(s => {
    const item = document.createElement('div');
    item.className = `session-item${s.id === currentRpSessionId ? ' active' : ''}`;
    item.onclick = () => switchRpSession(s.id);

    const info = document.createElement('div');
    info.className = 'session-info';

    const titleEl = document.createElement('div');
    titleEl.className = 'session-title';
    titleEl.textContent = s.title || 'Sesi Roleplay';

    const timeEl = document.createElement('div');
    timeEl.className = 'session-time';
    const d = new Date(s.updatedAt || Date.now());
    timeEl.textContent = d.toLocaleDateString('id-ID', { hour: '2-digit', minute: '2-digit' });

    info.appendChild(titleEl);
    info.appendChild(timeEl);

    const btnDel = document.createElement('button');
    btnDel.className = 'btn-del-session';
    btnDel.title = 'Hapus';
    btnDel.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13">
        <polyline points="3 6 5 6 21 6"></polyline>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
      </svg>
    `;
    btnDel.onclick = (e) => deleteRpSession(s.id, e);

    item.appendChild(info);
    item.appendChild(btnDel);
    rpSessionsList.appendChild(item);
  });
}

function clearCurrentRpChat() {
  if (confirm('Hapus seluruh pesan di sesi RP ini?')) {
    rpChatHistory = [];
    contextFiles = [];
    const cur = rpSessions.find(s => s.id === currentRpSessionId);
    if (cur) {
      cur.messages = [];
      cur.updatedAt = Date.now();
    }
    saveRpSessions();
    renderCurrentMessages();
    renderRpSessionsSidebar();
    showToast('Sesi RP direset', 'success');
  }
}

function updateEmptyState() {
  if (!emptyChatDiv) return;
  emptyChatDiv.style.display = rpChatHistory.length > 0 ? 'none' : '';
}

function updateSendButton() {
  if (!btnSend || !chatInputEl) return;
  const hasText = chatInputEl.value.trim().length > 0;
  const hasFiles = contextFiles.length > 0;
  btnSend.disabled = !(hasText || hasFiles) || isProcessing;
}

// ─── Start ─────────────────────────────────────────────────
init();
