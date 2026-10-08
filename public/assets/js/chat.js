/**
 * A.T.O.M. — Chat Logic
 * Handles message sending, API calls, rendering chat bubbles
 */

// ─── State ────────────────────────────────────────────────
let chatSessions  = [];   // [{id: str, title: str, updatedAt: num, messages: [...]}]
let currentSessionId = null;
let chatHistory   = [];   // Active session messages [{role:'user'|'assistant', content:str, thinking:[], model:str}]
let contextFiles  = [];   // [{name:str, content:str}]
let isProcessing  = false;
let activeAbortController = null;

// ─── DOM Elements ─────────────────────────────────────────
const messagesArea     = document.getElementById('messages-area');
const emptyChatDiv     = document.getElementById('empty-chat');
const chatInputEl      = document.getElementById('chat-input');
const btnSend          = document.getElementById('btn-send');
const btnAttach        = document.getElementById('btn-attach');
const fileUploadEl     = document.getElementById('file-upload');
const attachedFilesEl  = document.getElementById('attached-files');
const btnClearChat     = document.getElementById('btn-clear-chat');
const btnNewChat       = document.getElementById('btn-new-chat');
const chatSessionsList = document.getElementById('chat-sessions-list');

// ─── Init ─────────────────────────────────────────────────
function init() {
  loadSessionsFromStorage();
  updateEmptyState();
  updateSendButton();
  initModelModeSwitch();
  renderSessionsSidebar();

  btnNewChat?.addEventListener('click', () => {
    createNewSession();
  });

  // Scroll to bottom on load
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
      sendMessage();
    }
  }
});

btnSend?.addEventListener('click', () => {
  if (isProcessing) {
    abortProcess();
  } else {
    sendMessage();
  }
});

btnClearChat?.addEventListener('click', () => {
  if (confirm('Hapus semua pesan?')) clearChat();
});

// File attachment
btnAttach?.addEventListener('click', () => fileUploadEl?.click());

fileUploadEl?.addEventListener('change', (e) => {
  const files = Array.from(e.target.files || []);
  files.forEach(readAndAttachFile);
  e.target.value = ''; // Reset
});

// Clipboard paste support
chatInputEl?.addEventListener('paste', (e) => {
  const items = e.clipboardData?.items;
  if (!items) return;
  
  // If clipboard contains a file/image, prevent default text pasting behavior entirely
  let hasFile = false;
  for (let i = 0; i < items.length; i++) {
    if (items[i].kind === 'file') {
      hasFile = true;
      break;
    }
  }

  if (hasFile) {
    e.preventDefault();
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          let uniqueName = file.name || 'image.png';
          if (file.type.startsWith('image/') && (!file.name || file.name === 'image.png')) {
            const ts = Math.floor(Date.now() / 1000);
            uniqueName = `screenshot_${ts}.png`;
          }
          const renamedFile = new File([file], uniqueName, { type: file.type });
          readAndAttachFile(renamedFile);
        }
      }
    }
  }
});

// Suggestion chips
document.querySelectorAll('.suggestion-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const suggestion = chip.dataset.suggestion;
    if (suggestion && chatInputEl) {
      chatInputEl.value = suggestion;
      autoResize(chatInputEl);
      updateSendButton();
      chatInputEl.focus();
    }
  });
});

// ─── File Reading ──────────────────────────────────────────
function readAndAttachFile(file) {
  const isImage = file.type?.startsWith('image/');
  const maxSize = isImage ? 10 * 1024 * 1024 : 500 * 1024; // 10MB limit for images, 500KB for text
  if (file.size > maxSize) {
    showToast(`File "${file.name}" terlalu besar (max ${isImage ? '10MB' : '500KB'})`, 'warning');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const existing = contextFiles.find(f => f.name === file.name);
    if (!existing) {
      contextFiles.push({ 
        name: file.name, 
        content: e.target.result,
        type: file.type 
      });
      renderAttachedFiles();
    }
  };
  if (isImage) {
    reader.readAsDataURL(file);
  } else {
    reader.readAsText(file, 'utf-8');
  }
}

function renderAttachedFiles() {
  if (!attachedFilesEl) return;
  attachedFilesEl.innerHTML = contextFiles.map((f, i) => {
    const isImg = f.type?.startsWith('image/') || f.content?.startsWith('data:image/');
    if (isImg) {
      return `
        <div class="attached-file image-preview-chip" style="position: relative; display: inline-block; margin: 4px; padding: 0; background: none; border: none; border-radius: 8px;">
          <img src="${f.content}" style="width: 56px; height: 56px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border-color);" alt="${escapeHtml(f.name)}">
          <button onclick="removeFile(${i})" style="position: absolute; top: -6px; right: -6px; background: #ea6060; color: white; border-radius: 50%; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; font-size: 11px; border: 1px solid var(--border-color); cursor: pointer;" aria-label="Remove ${f.name}">×</button>
        </div>
      `;
    }
    return `
      <div class="attached-file">
        <span>📄 ${escapeHtml(f.name)}</span>
        <button onclick="removeFile(${i})" aria-label="Remove ${f.name}">×</button>
      </div>
    `;
  }).join('');
  updateSendButton();
}

window.removeFile = function(index) {
  contextFiles.splice(index, 1);
  renderAttachedFiles();
};

// ─── Abort Process ─────────────────────────────────────────
function abortProcess() {
  if (activeAbortController) {
    activeAbortController.abort();
    activeAbortController = null;
  }
  isProcessing = false;
  updateSendButton();
}

// ─── Send Message ──────────────────────────────────────────
async function sendMessage() {
  if (isProcessing) {
    abortProcess();
    return;
  }
  const prompt = chatInputEl?.value.trim();
  const hasFiles = contextFiles.length > 0;
  if (!prompt && !hasFiles) return;

  isProcessing = true;
  chatInputEl.value = '';
  autoResize(chatInputEl);
  updateSendButton();

  // Add user message to UI
  const displayPrompt = prompt || (hasFiles ? (contextFiles.some(f => f.type?.startsWith('image/')) ? '[Gambar Terlampir]' : '[Dokumen Terlampir]') : '');
  renderMessage('user', displayPrompt);
  chatHistory.push({ role: 'user', content: displayPrompt });
  updateEmptyState();
  scrollToBottom(messagesArea);

  // Show typing indicator
  const typingEl = showTypingIndicator();
  activeAbortController = new AbortController();

  try {
    const response = await callChatAPI(prompt, chatHistory.slice(0, -1), contextFiles, activeAbortController.signal);

    typingEl?.remove();

    // Render assistant response
    renderMessage('assistant', response.response, response.thinking || [], response.model || '');
    chatHistory.push({
      role: 'assistant',
      content: response.response,
      thinking: response.thinking || [],
      model: response.model || ''
    });

    // Log to telemetry
    const logPrompt = prompt || displayPrompt;
    logTelemetry({
      user_input: logPrompt,
      model_used: response.model || 'unknown',
      response_time: response.duration || 0,
      status: 'SUCCESS',
      ai_response: response.response
    });

    // Save history
    saveHistory();

    // Clear files after sending
    contextFiles = [];
    renderAttachedFiles();

  } catch (err) {
    typingEl?.remove();
    if (err.name === 'AbortError') {
      const abortMsg = '_⚠️ Respon AI dihentikan oleh pengguna (Request aborted)._';
      renderMessage('assistant', abortMsg, [], 'Aborted');
      chatHistory.push({
        role: 'assistant',
        content: abortMsg,
        thinking: [],
        model: 'Aborted'
      });
      saveHistory();

      const logPrompt = prompt || displayPrompt;
      logTelemetry({
        user_input: logPrompt,
        model_used: 'Aborted',
        response_time: 0,
        status: 'ABORTED',
        ai_response: abortMsg
      });
      showToast('Proses dibatalkan oleh pengguna.', 'warning');
    } else {
      const errorMsg = `[ERROR] ${err.message || 'Gagal menghubungi API. Periksa koneksi.'}`;
      renderMessage('assistant', errorMsg);

      const logPrompt = prompt || displayPrompt;
      logTelemetry({
        user_input: logPrompt,
        model_used: 'ERROR',
        response_time: 0,
        status: 'ERROR',
        ai_response: errorMsg
      });
    }
  } finally {
    isProcessing = false;
    activeAbortController = null;
    updateSendButton();
    scrollToBottom(messagesArea);
  }
}

// ─── API Call ──────────────────────────────────────────────
async function callChatAPI(prompt, history, files, signal) {
  const isAdvance = document.getElementById('mode-btn-advance')?.classList.contains('active');
  const modelSelectEl = document.getElementById('model-select');
  const selectedModel = (isAdvance && modelSelectEl) ? modelSelectEl.value : 'auto';

  const body = {
    prompt,
    history: history.map(m => ({ role: m.role, content: m.content })),
    files: files.map(f => ({ name: f.name, content: f.content })),
    model_preference: selectedModel
  };

  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: signal
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
    throw new Error(err.error || `HTTP ${resp.status}`);
  }

  return resp.json();
}

// ─── Render Message ────────────────────────────────────────
function renderMessage(role, content, thinking = [], model = '', personaBadge = '') {
  if (!messagesArea) return;

  const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
  const isUser = role === 'user';

  const avatarHtml = isUser
    ? '<div class="message-avatar">👤</div>'
    : '<div class="message-avatar">⚛️</div>';

  const bubbleContent = isUser
    ? `<p style="margin:0;color:inherit;">${escapeHtml(content).replace(/\n/g, '<br>')}</p>`
    : renderMarkdown(content);

  // Reasoning steps
  let reasoningHtml = '';
  if (!isUser && thinking && thinking.length > 0) {
    const stepsHtml = thinking.map(s => `
      <div class="reasoning-step">
        <span class="step-label">${escapeHtml(s.step || '')}</span>
        <span class="step-detail">${escapeHtml(s.detail || '')}</span>
      </div>
    `).join('');

    reasoningHtml = `
      <button class="reasoning-toggle" onclick="toggleReasoning('${msgId}')">
        <span class="arrow">▶</span>
        🧠 View Reasoning (${thinking.length} steps)
      </button>
      <div class="reasoning-steps" id="reasoning-${msgId}">
        ${stepsHtml}
      </div>
    `;
  }

  // Model & Persona badges
  const modelBadge = (!isUser && model)
    ? `<span class="model-badge ${model.toLowerCase().includes('groq') ? 'groq' : 'gemini'}">${escapeHtml(model)}</span>`
    : '';

  const personaTag = (!isUser && personaBadge && personaBadge !== 'ATOM Standard')
    ? `<span class="persona-badge-tag">🎭 ${escapeHtml(personaBadge)}</span>`
    : '';

  // Message Action Buttons for Assistant (Copy, Repeat, Like, Dislike)
  let actionsBarHtml = '';
  if (!isUser) {
    actionsBarHtml = `
      <div class="message-actions-bar" id="actions-${msgId}">
        <button type="button" class="msg-action-btn btn-copy" title="Salin teks jawaban" onclick="copyAssistantMessage('${msgId}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          <span class="action-btn-text">Salin</span>
        </button>
        <button type="button" class="msg-action-btn btn-repeat" title="Ulangi generasi respon ini" onclick="repeatAssistantMessage('${msgId}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
          <span>Ulangi</span>
        </button>
        <button type="button" class="msg-action-btn btn-like" title="Bagus / Puas (Like)" onclick="rateAssistantMessage('${msgId}', 'like')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
        </button>
        <button type="button" class="msg-action-btn btn-dislike" title="Kurang Bagus / Kritik (Dislike)" onclick="rateAssistantMessage('${msgId}', 'dislike')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path></svg>
        </button>
      </div>
    `;
  }

  const msgEl = document.createElement('div');
  msgEl.className = `chat-message ${role}`;
  msgEl.id = msgId;
  msgEl.dataset.rawContent = content;
  msgEl.dataset.model = model;
  msgEl.innerHTML = `
    ${avatarHtml}
    <div class="message-body">
      ${personaTag}
      ${reasoningHtml}
      <div class="message-bubble">${bubbleContent}</div>
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;width:100%;">
        ${modelBadge}
        ${actionsBarHtml}
      </div>
    </div>
  `;

  messagesArea.appendChild(msgEl);
}

// ─── Assistant Message Action Handlers ─────────────────────
window.copyAssistantMessage = function(msgId) {
  const msgEl = document.getElementById(msgId);
  if (!msgEl) return;
  const content = msgEl.dataset.rawContent || msgEl.querySelector('.message-bubble')?.innerText || '';
  navigator.clipboard.writeText(content).then(() => {
    const btn = msgEl.querySelector('.btn-copy');
    if (btn) {
      btn.classList.add('copied');
      const textSpan = btn.querySelector('.action-btn-text');
      if (textSpan) textSpan.textContent = '✓ Tersalin!';
      setTimeout(() => {
        btn.classList.remove('copied');
        if (textSpan) textSpan.textContent = 'Salin';
      }, 2000);
    }
    showToast('Teks respon berhasil disalin ke clipboard.', 'success');
  }).catch(() => {
    showToast('Gagal menyalin teks ke clipboard.', 'error');
  });
};

window.repeatAssistantMessage = function(msgId) {
  if (isProcessing) {
    showToast('Harap tunggu atau hentikan proses saat ini terlebih dahulu.', 'warning');
    return;
  }
  const msgEl = document.getElementById(msgId);
  if (!msgEl) return;

  // Cari prompt user sebelum pesan ini
  let promptText = '';
  let prevEl = msgEl.previousElementSibling;
  while (prevEl) {
    if (prevEl.classList.contains('user')) {
      promptText = prevEl.dataset.rawContent || prevEl.querySelector('.message-bubble')?.innerText || '';
      break;
    }
    prevEl = prevEl.previousElementSibling;
  }

  if (!promptText && chatHistory.length > 0) {
    const lastUser = [...chatHistory].reverse().find(m => m.role === 'user');
    if (lastUser) promptText = lastUser.content;
  }

  if (promptText) {
    if (chatInputEl) {
      chatInputEl.value = promptText;
      autoResize(chatInputEl);
    }
    sendMessage();
  } else {
    showToast('Tidak dapat menemukan prompt user sebelumnya.', 'info');
  }
};

window.rateAssistantMessage = function(msgId, ratingType) {
  const msgEl = document.getElementById(msgId);
  if (!msgEl) return;

  const modelUsed = msgEl.dataset.model || 'Cortex Model';
  const responseExcerpt = (msgEl.dataset.rawContent || '').slice(0, 150);

  // Cari prompt user terkait
  let promptText = '';
  let prevEl = msgEl.previousElementSibling;
  while (prevEl) {
    if (prevEl.classList.contains('user')) {
      promptText = prevEl.dataset.rawContent || prevEl.querySelector('.message-bubble')?.innerText || '';
      break;
    }
    prevEl = prevEl.previousElementSibling;
  }

  const btnLike = msgEl.querySelector('.btn-like');
  const btnDislike = msgEl.querySelector('.btn-dislike');

  if (ratingType === 'like') {
    btnLike?.classList.add('active-like');
    btnDislike?.classList.remove('active-dislike');

    logTelemetry({
      user_input: promptText,
      model_used: modelUsed,
      response_time: 0,
      status: 'FEEDBACK_LIKE',
      feedback_type: 'LIKE',
      ai_response: responseExcerpt
    });

    showToast('Terima kasih atas apresiasi Anda! (Dicatat ke Telemetry)', 'success');
  } else if (ratingType === 'dislike') {
    if (typeof window.openCritiqueModal === 'function') {
      window.openCritiqueModal({
        modelUsed,
        promptText,
        responseExcerpt,
        onSubmitted: () => {
          btnDislike?.classList.add('active-dislike');
          btnLike?.classList.remove('active-like');
        }
      });
    } else {
      btnDislike?.classList.add('active-dislike');
      btnLike?.classList.remove('active-like');
      logTelemetry({
        user_input: promptText,
        model_used: modelUsed,
        response_time: 0,
        status: 'FEEDBACK_DISLIKE',
        feedback_type: 'DISLIKE',
        ai_response: responseExcerpt
      });
      showToast('Kritik dicatat ke Telemetry.', 'info');
    }
  }
};

// Toggle reasoning steps
window.toggleReasoning = function(msgId) {
  const steps = document.getElementById(`reasoning-${msgId}`);
  const btn = steps?.previousElementSibling;
  if (!steps || !btn) return;

  const isOpen = steps.classList.contains('open');
  steps.classList.toggle('open', !isOpen);
  btn.classList.toggle('open', !isOpen);
};

// ─── Thinking / Loading Phrases (Proses Berpikir Bertahap yang Jelas) ───
const THINKING_PHRASES = [
  'Membaca pesan Anda...',
  'Menganalisis pertanyaan...',
  'Memproses informasi...',
  'Menyusun jawaban...',
  'Memeriksa detail jawaban...',
  'Menyelesaikan respons...'
];

// ─── Typing Indicator with Dynamic Progressive Loading Text ──
function showTypingIndicator() {
  const el = document.createElement('div');
  el.className = 'typing-indicator';
  el.innerHTML = `
    <div class="message-avatar">⚛️</div>
    <div class="typing-bubble">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
      <div class="typing-status-text">${THINKING_PHRASES[0]}</div>
    </div>
  `;
  messagesArea?.appendChild(el);
  scrollToBottom(messagesArea);

  const statusTextEl = el.querySelector('.typing-status-text');
  let phraseIndex = 0;

  // Progressive thinking text rotator (rotasi dinamis setiap 2.4 detik)
  const intervalId = setInterval(() => {
    phraseIndex = (phraseIndex + 1) % THINKING_PHRASES.length;
    if (statusTextEl) {
      statusTextEl.classList.add('fade-out');
      setTimeout(() => {
        statusTextEl.textContent = THINKING_PHRASES[phraseIndex];
        statusTextEl.classList.remove('fade-out');
        scrollToBottom(messagesArea);
      }, 250);
    }
  }, 2400);

  // Hook remove method to safely clear interval timer
  const originalRemove = el.remove.bind(el);
  el.remove = () => {
    clearInterval(intervalId);
    originalRemove();
  };

  return el;
}

// ─── Helpers ───────────────────────────────────────────────
function updateEmptyState() {
  if (!emptyChatDiv || !messagesArea) return;
  const hasMessages = chatHistory.length > 0;
  emptyChatDiv.style.display = hasMessages ? 'none' : '';
}

function updateSendButton() {
  if (!btnSend || !chatInputEl) return;
  if (isProcessing) {
    btnSend.disabled = false;
    btnSend.classList.add('btn-abort');
    btnSend.setAttribute('title', 'Hentikan proses respon (Stop / Abort)');
    btnSend.setAttribute('aria-label', 'Stop generating');
    btnSend.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
        <rect x="4" y="4" width="16" height="16" rx="2"></rect>
      </svg>
    `;
  } else {
    btnSend.classList.remove('btn-abort');
    btnSend.setAttribute('title', 'Kirim Pesan (Enter)');
    btnSend.setAttribute('aria-label', 'Send message');
    btnSend.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
      </svg>
    `;
    const hasText = chatInputEl.value.trim().length > 0;
    const hasFiles = typeof contextFiles !== 'undefined' && contextFiles.length > 0;
    btnSend.disabled = !(hasText || hasFiles);
  }
}

// ─── Multi-Session Storage & Management ─────────────────────
function loadSessionsFromStorage() {
  try {
    const rawSessions = localStorage.getItem('atom_chat_sessions');
    if (rawSessions) {
      chatSessions = JSON.parse(rawSessions);
    } else {
      // Migrasi data lama dari atom_chat_history jika ada
      const oldHistory = localStorage.getItem('atom_chat_history');
      if (oldHistory) {
        const parsedOld = JSON.parse(oldHistory);
        if (parsedOld && parsedOld.length > 0) {
          const firstUserMsg = parsedOld.find(m => m.role === 'user');
          const title = firstUserMsg ? firstUserMsg.content.slice(0, 32) : 'Percakapan Sebelumnya';
          const defaultSession = {
            id: 'sess_' + Date.now(),
            title: title,
            updatedAt: Date.now(),
            messages: parsedOld
          };
          chatSessions = [defaultSession];
          saveSessionsToStorage();
        }
      }
    }
  } catch {
    chatSessions = [];
  }

  // Set active session
  const lastActiveId = localStorage.getItem('atom_active_session_id');
  const found = chatSessions.find(s => s.id === lastActiveId);
  if (found) {
    currentSessionId = found.id;
    chatHistory = found.messages || [];
  } else if (chatSessions.length > 0) {
    currentSessionId = chatSessions[0].id;
    chatHistory = chatSessions[0].messages || [];
  } else {
    // Buat sesi baru kosong jika belum ada
    createNewSession(false);
    return;
  }

  renderCurrentSessionMessages();
  syncSessionsWithBackend();
}

let chatSyncTimer = null;

async function syncSessionsWithBackend() {
  try {
    const res = await fetch('/api/sessions/chat');
    if (!res.ok) return;
    const data = await res.json();
    const serverSessions = data.sessions || [];
    
    if (serverSessions.length > 0) {
      const isClientEmpty = chatSessions.length === 0 || 
        (chatSessions.length === 1 && chatSessions[0].title === 'Percakapan Baru' && (!chatSessions[0].messages || chatSessions[0].messages.length === 0));
      
      if (isClientEmpty || serverSessions.length >= chatSessions.length) {
        chatSessions = serverSessions;
        currentSessionId = data.active_id || serverSessions[0].id;
        const active = chatSessions.find(s => s.id === currentSessionId) || chatSessions[0];
        chatHistory = active.messages || [];
        try {
          localStorage.setItem('atom_chat_sessions', JSON.stringify(chatSessions));
          localStorage.setItem('atom_active_session_id', currentSessionId);
        } catch {}
        renderCurrentSessionMessages();
        renderSessionsSidebar();
        updateEmptyState();
        return;
      }
    }
    
    if (chatSessions.length > 0 && serverSessions.length === 0) {
      saveSessionsToBackend();
    }
  } catch {
    // Offline / fallback to localStorage
  }
}

function saveSessionsToBackend() {
  clearTimeout(chatSyncTimer);
  chatSyncTimer = setTimeout(async () => {
    try {
      await fetch('/api/sessions/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessions: chatSessions,
          active_id: currentSessionId
        })
      });
    } catch {}
  }, 400);
}

function saveSessionsToStorage() {
  try {
    localStorage.setItem('atom_chat_sessions', JSON.stringify(chatSessions));
    if (currentSessionId) {
      localStorage.setItem('atom_active_session_id', currentSessionId);
    }
    // Backward compatibility
    localStorage.setItem('atom_chat_history', JSON.stringify(chatHistory.slice(-50)));
  } catch { /* quota limit handling */ }
  saveSessionsToBackend();
}

function saveHistory() {
  if (!currentSessionId) {
    currentSessionId = 'sess_' + Date.now();
  }

  let session = chatSessions.find(s => s.id === currentSessionId);
  if (!session) {
    const firstUserMsg = chatHistory.find(m => m.role === 'user');
    let title = firstUserMsg ? firstUserMsg.content.trim().slice(0, 30) : 'Percakapan Baru';
    if (firstUserMsg && firstUserMsg.content.length > 30) title += '...';
    session = {
      id: currentSessionId,
      title: title || 'Percakapan Baru',
      updatedAt: Date.now(),
      messages: chatHistory
    };
    chatSessions.unshift(session);
  } else {
    session.messages = chatHistory;
    session.updatedAt = Date.now();
    // Update title jika judul masih default dan user baru mengirim pesan pertama
    if (session.title === 'Percakapan Baru') {
      const firstUserMsg = chatHistory.find(m => m.role === 'user');
      if (firstUserMsg) {
        let title = firstUserMsg.content.trim().slice(0, 30);
        if (firstUserMsg.content.length > 30) title += '...';
        session.title = title;
      }
    }
    // Pindahkan sesi yang baru aktif ke urutan paling atas
    chatSessions = [session, ...chatSessions.filter(s => s.id !== currentSessionId)];
  }

  saveSessionsToStorage();
  renderSessionsSidebar();
}

function createNewSession(notify = true) {
  currentSessionId = 'sess_' + Date.now();
  chatHistory = [];
  contextFiles = [];

  const newSession = {
    id: currentSessionId,
    title: 'Percakapan Baru',
    updatedAt: Date.now(),
    messages: []
  };

  chatSessions.unshift(newSession);
  saveSessionsToStorage();
  renderCurrentSessionMessages();
  renderSessionsSidebar();
  updateEmptyState();
  updateSendButton();

  if (chatInputEl) {
    chatInputEl.value = '';
    chatInputEl.focus();
  }

  // Tutup sidebar otomatis di mobile setelah memilih/membuat sesi baru
  if (typeof closeSidebar === 'function' && window.innerWidth <= 768) {
    closeSidebar();
  }

  if (notify) {
    showToast('Sesi baru dibuat', 'info');
  }
}

function switchSession(sessionId) {
  if (sessionId === currentSessionId) {
    if (typeof closeSidebar === 'function' && window.innerWidth <= 768) {
      closeSidebar();
    }
    return;
  }
  const target = chatSessions.find(s => s.id === sessionId);
  if (!target) return;

  currentSessionId = target.id;
  chatHistory = target.messages || [];
  contextFiles = [];

  // Sinkronkan persona sesi yang dipilih
  if (target.personaId) {
    activePersonaId = target.personaId;
    updateActivePersonaUI();
    personaCardsContainer?.querySelectorAll('.persona-card').forEach((c, idx) => {
      c.classList.toggle('active', PERSONAS[idx]?.id === activePersonaId);
    });
  }

  localStorage.setItem('atom_active_session_id', currentSessionId);
  renderCurrentSessionMessages();
  renderSessionsSidebar();
  updateEmptyState();
  updateSendButton();

  // Tutup sidebar otomatis di mobile setelah memilih sesi
  if (typeof closeSidebar === 'function' && window.innerWidth <= 768) {
    closeSidebar();
  }
}

function deleteSession(sessionId, event) {
  if (event) event.stopPropagation();
  if (!confirm('Hapus sesi obrolan ini?')) return;

  chatSessions = chatSessions.filter(s => s.id !== sessionId);

  if (currentSessionId === sessionId) {
    if (chatSessions.length > 0) {
      currentSessionId = chatSessions[0].id;
      chatHistory = chatSessions[0].messages || [];
    } else {
      createNewSession(false);
      return;
    }
  }

  saveSessionsToStorage();
  renderCurrentSessionMessages();
  renderSessionsSidebar();
  updateEmptyState();
  updateSendButton();
  showToast('Sesi dihapus', 'success');
}

function renderCurrentSessionMessages() {
  if (!messagesArea) return;
  const header = messagesArea.querySelector('.atom-header');
  messagesArea.innerHTML = '';
  if (header) {
    messagesArea.appendChild(header);
  }

  chatHistory.forEach(msg => {
    renderMessage(msg.role, msg.content, msg.thinking || [], msg.model || '');
  });

  if (emptyChatDiv) {
    messagesArea.appendChild(emptyChatDiv);
    emptyChatDiv.style.display = chatHistory.length === 0 ? '' : 'none';
  }

  renderAttachedFiles();
  setTimeout(() => scrollToBottom(messagesArea), 50);
}

function renderSessionsSidebar() {
  if (!chatSessionsList) return;
  chatSessionsList.innerHTML = '';

  if (chatSessions.length === 0) {
    const emptyEl = document.createElement('div');
    emptyEl.className = 'empty-sessions';
    emptyEl.textContent = 'Belum ada riwayat';
    chatSessionsList.appendChild(emptyEl);
    return;
  }

  chatSessions.forEach(session => {
    const item = document.createElement('div');
    item.className = `session-item${session.id === currentSessionId ? ' active' : ''}`;
    item.onclick = () => switchSession(session.id);

    const info = document.createElement('div');
    info.className = 'session-info';

    const titleEl = document.createElement('div');
    titleEl.className = 'session-title';
    titleEl.textContent = session.title || 'Tanpa Judul';

    const timeEl = document.createElement('div');
    timeEl.className = 'session-time';
    const d = new Date(session.updatedAt || Date.now());
    timeEl.textContent = d.toLocaleDateString('id-ID', { hour: '2-digit', minute: '2-digit' });

    info.appendChild(titleEl);
    info.appendChild(timeEl);

    const btnDel = document.createElement('button');
    btnDel.className = 'btn-del-session';
    btnDel.title = 'Hapus obrolan ini';
    btnDel.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13">
        <polyline points="3 6 5 6 21 6"></polyline>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
      </svg>
    `;
    btnDel.onclick = (e) => deleteSession(session.id, e);

    item.appendChild(info);
    item.appendChild(btnDel);
    chatSessionsList.appendChild(item);
  });
}

function clearChat() {
  if (confirm('Hapus seluruh pesan di sesi obrolan saat ini?')) {
    chatHistory = [];
    contextFiles = [];

    const currentSession = chatSessions.find(s => s.id === currentSessionId);
    if (currentSession) {
      currentSession.messages = [];
      currentSession.title = 'Percakapan Baru';
      currentSession.updatedAt = Date.now();
    }

    saveSessionsToStorage();
    renderCurrentSessionMessages();
    renderSessionsSidebar();
    showToast('Sesi obrolan direset', 'success');
  }
}

// ─── Model Selector (Auto vs Advance categorized by API) ───
const ADVANCE_MODELS_BY_API = {
  groq: [
    { value: 'groq', label: '⚡ Llama 3.3 70B Versatile' }
  ],
  openrouter: [
    { value: 'openrouter', label: '🌐 OpenRouter (Fallback List)' },
    { value: 'openrouter:meta-llama/llama-3.3-70b-instruct:free', label: '🦙 Llama 3.3 70B Instruct (Free)' },
    { value: 'openrouter:qwen/qwen-3-coder-480b:free', label: '💻 Qwen3 Coder 480B (Free)' },
    { value: 'openrouter:nousresearch/hermes-3-405b-instruct:free', label: '🏛️ Hermes 3 405B Instruct (Free)' },
    { value: 'openrouter:google/gemma-4-31b:free', label: '💎 Gemma 4 31B (Free)' },
    { value: 'openrouter:nvidia/nemotron-3-nano-30b:free', label: '🟢 Nemotron 3 Nano 30B (Free)' },
    { value: 'openrouter:nvidia/nemotron-3-nano-omni:free', label: '🔮 Nemotron 3 Nano Omni (Free)' },
    { value: 'openrouter:qwen/qwen-3-next-80b:free', label: '🚀 Qwen3 Next 80B (Free)' },
    { value: 'openrouter:liquid/lfm2.5-1.2b-thinking:free', label: '🧠 LFM 2.5 1.2B Thinking (Free)' },
    { value: 'openrouter:poolside/laguna-xs-2:free', label: '🌊 Laguna XS.2 (Free)' },
    { value: 'openrouter:venice/uncensored:free', label: '🎭 Venice Uncensored (Free)' }
  ],
  gemini: [
    { value: 'gemini', label: '♊ Gemini Flash 2.5 (Multimodal)' }
  ],
  deepseek: [
    { value: 'deepseek', label: '🐳 DeepSeek V3 (Cloud)' }
  ],
  ollama: [
    { value: 'ollama', label: '🧠 DeepSeek V4 (Local/Cloud)' }
  ]
};

function initModelModeSwitch() {
  const modeBtnAuto = document.getElementById('mode-btn-auto');
  const modeBtnAdvance = document.getElementById('mode-btn-advance');
  const autoBadge = document.getElementById('auto-mode-badge');
  const advanceControls = document.getElementById('advance-model-controls');
  const apiProviderSelect = document.getElementById('api-provider-select');
  const modelSelect = document.getElementById('model-select');

  if (!modeBtnAuto || !modeBtnAdvance) return;

  function populateModels(providerKey, selectedModelValue = null) {
    if (!modelSelect) return;
    const models = ADVANCE_MODELS_BY_API[providerKey] || ADVANCE_MODELS_BY_API.groq;
    modelSelect.innerHTML = models.map(m => `
      <option value="${m.value}">${m.label}</option>
    `).join('');

    if (selectedModelValue && models.some(m => m.value === selectedModelValue)) {
      modelSelect.value = selectedModelValue;
    } else {
      modelSelect.value = models[0].value;
    }
  }

  function setMode(mode) {
    if (mode === 'advance') {
      modeBtnAuto.classList.remove('active');
      modeBtnAdvance.classList.add('active');
      autoBadge?.classList.add('hidden');
      advanceControls?.classList.remove('hidden');
      localStorage.setItem('atom_chat_model_mode', 'advance');

      const provider = apiProviderSelect?.value || 'groq';
      const savedModel = localStorage.getItem('atom_advance_model');
      populateModels(provider, savedModel);
    } else {
      modeBtnAdvance.classList.remove('active');
      modeBtnAuto.classList.add('active');
      autoBadge?.classList.remove('hidden');
      advanceControls?.classList.add('hidden');
      localStorage.setItem('atom_chat_model_mode', 'auto');
    }
  }

  // Restore saved state
  const savedMode = localStorage.getItem('atom_chat_model_mode') || 'auto';
  const savedProvider = localStorage.getItem('atom_advance_provider') || 'groq';
  const savedModel = localStorage.getItem('atom_advance_model');

  if (apiProviderSelect) {
    apiProviderSelect.value = savedProvider;
    populateModels(savedProvider, savedModel);

    apiProviderSelect.addEventListener('change', () => {
      const provider = apiProviderSelect.value;
      localStorage.setItem('atom_advance_provider', provider);
      populateModels(provider);
      if (modelSelect) {
        localStorage.setItem('atom_advance_model', modelSelect.value);
      }
    });
  }

  if (modelSelect) {
    modelSelect.addEventListener('change', () => {
      localStorage.setItem('atom_advance_model', modelSelect.value);
    });
  }

  modeBtnAuto.addEventListener('click', () => setMode('auto'));
  modeBtnAdvance.addEventListener('click', () => setMode('advance'));

  setMode(savedMode);
}

// ─── Start ─────────────────────────────────────────────────
init();
