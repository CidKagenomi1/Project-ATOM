/**
 * A.T.O.M. — Chat Logic
 * Handles message sending, API calls, rendering chat bubbles
 */

// ─── State ────────────────────────────────────────────────
let chatHistory   = [];   // [{role:'user'|'assistant', content:str}]
let contextFiles  = [];   // [{name:str, content:str}]
let isProcessing  = false;

// ─── DOM Elements ─────────────────────────────────────────
const messagesArea    = document.getElementById('messages-area');
const emptyChatDiv    = document.getElementById('empty-chat');
const chatInputEl     = document.getElementById('chat-input');
const btnSend         = document.getElementById('btn-send');
const btnAttach       = document.getElementById('btn-attach');
const fileUploadEl    = document.getElementById('file-upload');
const attachedFilesEl = document.getElementById('attached-files');
const btnClearChat    = document.getElementById('btn-clear-chat');

// ─── Init ─────────────────────────────────────────────────
function init() {
  // Load history from localStorage
  try {
    const saved = localStorage.getItem('atom_chat_history');
    if (saved) {
      chatHistory = JSON.parse(saved);
      chatHistory.forEach(msg => renderMessage(msg.role, msg.content, msg.thinking || [], msg.model || ''));
    }
  } catch { chatHistory = []; }

  updateEmptyState();
  updateSendButton();

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
  const maxSize = 100 * 1024; // 100KB limit
  if (file.size > maxSize) {
    showToast(`File "${file.name}" terlalu besar (max 100KB)`, 'warning');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const existing = contextFiles.find(f => f.name === file.name);
    if (!existing) {
      contextFiles.push({ name: file.name, content: e.target.result });
      renderAttachedFiles();
    }
  };
  reader.readAsText(file, 'utf-8');
}

function renderAttachedFiles() {
  if (!attachedFilesEl) return;
  attachedFilesEl.innerHTML = contextFiles.map((f, i) => `
    <div class="attached-file">
      <span>📄 ${escapeHtml(f.name)}</span>
      <button onclick="removeFile(${i})" aria-label="Remove ${f.name}">×</button>
    </div>
  `).join('');
}

window.removeFile = function(index) {
  contextFiles.splice(index, 1);
  renderAttachedFiles();
};

// ─── Send Message ──────────────────────────────────────────
async function sendMessage() {
  if (isProcessing) return;
  const prompt = chatInputEl?.value.trim();
  if (!prompt) return;

  isProcessing = true;
  chatInputEl.value = '';
  autoResize(chatInputEl);
  updateSendButton();

  // Add user message to UI
  renderMessage('user', prompt);
  chatHistory.push({ role: 'user', content: prompt });
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
    logTelemetry({
      user_input: prompt.substring(0, 50) + (prompt.length > 50 ? '...' : ''),
      model_used: response.model || 'unknown',
      response_time: response.duration || 0,
      status: 'SUCCESS'
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

    logTelemetry({
      user_input: prompt.substring(0, 50),
      model_used: 'ERROR',
      response_time: 0,
      status: 'ERROR'
    });
  }

  isProcessing = false;
  updateSendButton();
  scrollToBottom(messagesArea);
}

// ─── API Call ──────────────────────────────────────────────
async function callChatAPI(prompt, history, files) {
  const body = {
    prompt,
    history: history.map(m => ({ role: m.role, content: m.content })),
    files: files.map(f => ({ name: f.name, content: f.content }))
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
function renderMessage(role, content, thinking = [], model = '') {
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

  // Model badge
  const modelBadge = (!isUser && model)
    ? `<span class="model-badge ${model.toLowerCase().includes('groq') ? 'groq' : 'gemini'}">${escapeHtml(model)}</span>`
    : '';

  const msgEl = document.createElement('div');
  msgEl.className = `chat-message ${role}`;
  msgEl.id = msgId;
  msgEl.innerHTML = `
    ${avatarHtml}
    <div class="message-body">
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
  btnSend.disabled = !hasText || isProcessing;
}

function saveHistory() {
  try {
    // Save last 50 messages
    const toSave = chatHistory.slice(-50);
    localStorage.setItem('atom_chat_history', JSON.stringify(toSave));
  } catch { /* ignore quota errors */ }
}

function clearChat() {
  chatHistory = [];
  contextFiles = [];
  if (messagesArea) messagesArea.innerHTML = '';
  if (emptyChatDiv) messagesArea?.appendChild(emptyChatDiv);
  emptyChatDiv.style.display = '';
  renderAttachedFiles();
  localStorage.removeItem('atom_chat_history');
  showToast('Chat dihapus', 'success');
}

// ─── Start ─────────────────────────────────────────────────
init();
