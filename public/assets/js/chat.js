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
  buildCustomModelSelect();

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
  const hasFiles = typeof contextFiles !== 'undefined' && contextFiles.length > 0;
  btnSend.disabled = !(hasText || hasFiles) || isProcessing;
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
