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
  buildCustomModelSelect();
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

btnSend?.addEventListener('click', sendMessage);

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

// ─── Send Message ──────────────────────────────────────────
async function sendMessage() {
  if (isProcessing) return;
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

  try {
    const response = await callChatAPI(prompt, chatHistory.slice(0, -1), contextFiles);

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

  isProcessing = false;
  updateSendButton();
  scrollToBottom(messagesArea);
}

// ─── API Call ──────────────────────────────────────────────
async function callChatAPI(prompt, history, files) {
  const modelSelectEl = document.getElementById('model-select');
  const selectedModel = modelSelectEl ? modelSelectEl.value : 'auto';

  const body = {
    prompt,
    history: history.map(m => ({ role: m.role, content: m.content })),
    files: files.map(f => ({ name: f.name, content: f.content })),
    model_preference: selectedModel
  };

  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
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

  const msgEl = document.createElement('div');
  msgEl.className = `chat-message ${role}`;
  msgEl.id = msgId;
  msgEl.innerHTML = `
    ${avatarHtml}
    <div class="message-body">
      ${personaTag}
      ${reasoningHtml}
      <div class="message-bubble">${bubbleContent}</div>
      ${modelBadge}
    </div>
  `;

  messagesArea.appendChild(msgEl);
}

// Toggle reasoning steps
window.toggleReasoning = function(msgId) {
  const steps = document.getElementById(`reasoning-${msgId}`);
  const btn = steps?.previousElementSibling;
  if (!steps || !btn) return;

  const isOpen = steps.classList.contains('open');
  steps.classList.toggle('open', !isOpen);
  btn.classList.toggle('open', !isOpen);
};

// ─── Typing Indicator ──────────────────────────────────────
function showTypingIndicator() {
  const el = document.createElement('div');
  el.className = 'typing-indicator';
  el.innerHTML = `
    <div class="message-avatar">⚛️</div>
    <div class="typing-dots">
      <span></span><span></span><span></span>
    </div>
  `;
  messagesArea?.appendChild(el);
  scrollToBottom(messagesArea);
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
  const hasText = chatInputEl.value.trim().length > 0;
  const hasFiles = typeof contextFiles !== 'undefined' && contextFiles.length > 0;
  btnSend.disabled = !(hasText || hasFiles) || isProcessing;
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

// ─── Custom Model Select Dropdown Generator ────────────────
function buildCustomModelSelect() {
  const select = document.getElementById('model-select');
  const wrapper = document.querySelector('.model-select-wrapper');
  if (!select || !wrapper) return;

  // Hide native select
  select.style.display = 'none';

  // Create trigger button
  const trigger = document.createElement('button');
  trigger.className = 'custom-select-trigger';
  trigger.type = 'button';
  trigger.textContent = select.options[select.selectedIndex]?.textContent || 'Select Model';

  // Create options container
  const optionsContainer = document.createElement('div');
  optionsContainer.className = 'custom-select-options';

  // Create option elements
  Array.from(select.options).forEach((opt, idx) => {
    const customOpt = document.createElement('div');
    customOpt.className = `custom-select-option${idx === select.selectedIndex ? ' selected' : ''}`;
    customOpt.textContent = opt.textContent;
    customOpt.dataset.value = opt.value;

    customOpt.addEventListener('click', (e) => {
      e.stopPropagation();
      select.value = opt.value;
      trigger.textContent = opt.textContent;
      
      // Update active option styles
      optionsContainer.querySelectorAll('.custom-select-option').forEach(o => o.classList.remove('selected'));
      customOpt.classList.add('selected');

      // Close dropdown
      wrapper.classList.remove('open');
      
      // Trigger native change event if needed
      select.dispatchEvent(new Event('change'));
    });

    optionsContainer.appendChild(customOpt);
  });

  // Toggle trigger click
  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    wrapper.classList.toggle('open');
  });

  // Close when clicking outside wrapper
  document.addEventListener('click', (e) => {
    if (!wrapper.contains(e.target)) {
      wrapper.classList.remove('open');
    }
  });

  wrapper.appendChild(trigger);
  wrapper.appendChild(optionsContainer);
}

// ─── Start ─────────────────────────────────────────────────
init();
