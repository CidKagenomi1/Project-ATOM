/**
 * A.T.O.M. — Notes Logic
 * CRUD operations via backend API /api/notes and /api/bubbles
 */

// ─── State ────────────────────────────────────────────────
let currentNoteId  = null;
let currentNoteMode = 'view'; // 'view' | 'edit' | 'chat'
let noteChatHistory = [];
let currentTab     = 'notes';

// ─── Note API Handlers ─────────────────────────────────────
async function createNote(title = 'Untitled Note', content = '', tags = []) {
  const resp = await fetch('/api/notes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content, tags })
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

async function getNote(id) {
  const resp = await fetch(`/api/notes/${id}`);
  if (!resp.ok) return null;
  return resp.json();
}

async function getAllNotes() {
  const resp = await fetch('/api/notes');
  if (!resp.ok) return [];
  return resp.json();
}

async function updateNote(id, updates) {
  const resp = await fetch(`/api/notes/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

async function deleteNote(id) {
  const resp = await fetch(`/api/notes/${id}`, {
    method: 'DELETE'
  });
  return resp.ok;
}

async function searchNotes(query) {
  const q = encodeURIComponent(query.trim());
  const resp = await fetch(`/api/notes?query=${q}`);
  if (!resp.ok) return [];
  return resp.json();
}

async function getAllTags() {
  const resp = await fetch('/api/notes/tags');
  if (!resp.ok) return [];
  return resp.json();
}

// ─── Bubble API Handlers ───────────────────────────────────
async function loadBubbles() {
  const resp = await fetch('/api/bubbles');
  if (!resp.ok) return [];
  return resp.json();
}

async function addBubble(text) {
  const resp = await fetch('/api/bubbles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

async function deleteBubble(id) {
  const resp = await fetch(`/api/bubbles/${id}`, {
    method: 'DELETE'
  });
  return resp.ok;
}


// ─── Render Notes Sidebar ─────────────────────────────────
async function renderNotesList(query = '') {
  const notesList = document.getElementById('notes-list');
  const statsEl   = document.getElementById('notes-stats');
  if (!notesList) return;

  const notes = await searchNotes(query);
  const allTags = await getAllTags();
  const allNotes = await getAllNotes();

  notesList.innerHTML = notes.length === 0
    ? `<p style="text-align:center;color:var(--text-muted);font-size:0.8rem;padding:var(--space-4);">Tidak ada catatan. Buat baru!</p>`
    : notes.map(note => `
        <div class="note-item ${note.id === currentNoteId ? 'active' : ''}" onclick="openNote(${note.id})">
          <span class="note-item-title">${escapeHtml(note.title)}</span>
          <button class="note-item-delete" onclick="confirmDeleteNote(event, ${note.id})" aria-label="Delete">🗑</button>
        </div>
      `).join('');

  if (statsEl) {
    statsEl.textContent = `${allNotes.length} notes · ${allTags.length} tags`;
  }
}

// ─── Open Note ────────────────────────────────────────────
async function openNote(id) {
  const note = await getNote(id);
  if (!note) return;

  currentNoteId = id;
  noteChatHistory = [];
  setNoteMode('view');
  await renderNotesList(document.getElementById('notes-search')?.value || '');

  // Populate editor
  const titleInput = document.getElementById('note-title-input');
  const textarea   = document.getElementById('note-textarea');
  const tagsInput  = document.getElementById('tags-input');

  if (titleInput) titleInput.value = note.title;
  if (textarea)   textarea.value = note.content;
  if (tagsInput)  tagsInput.value = note.tags?.join(', ') || '';

  renderTagsDisplay(note.tags || []);
  renderMarkdownView(note.content);
  renderNoteChatMessages();

  // Show editor, hide placeholder
  document.getElementById('note-placeholder').style.display = 'none';
  const editorEl = document.getElementById('note-editor');
  editorEl.style.display = 'flex';
  editorEl.classList.remove('hidden');
}

function renderMarkdownView(content) {
  const viewEl = document.getElementById('note-view-content');
  if (!viewEl) return;
  if (!content?.trim()) {
    viewEl.innerHTML = '<p style="color:var(--text-muted);font-style:italic;">Empty note. Switch to Edit mode to start writing.</p>';
    return;
  }
  viewEl.innerHTML = renderMarkdown(content);
}

function renderTagsDisplay(tags) {
  const tagsDisplay = document.getElementById('tags-display');
  if (!tagsDisplay) return;
  tagsDisplay.innerHTML = tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join(' ');
}

// ─── Note Mode ────────────────────────────────────────────
window.setNoteMode = function(mode) {
  currentNoteMode = mode;
  const modes = ['view', 'edit', 'chat'];
  modes.forEach(m => {
    document.getElementById(`note-${m}-content`).style.display = m === mode ? (m === 'chat' ? 'flex' : 'block') : 'none';
    const btn = document.getElementById(`mode-${m}-btn`);
    if (btn) btn.classList.toggle('active', m === mode);
  });
};

// ─── Save Note ────────────────────────────────────────────
document.getElementById('btn-save-note')?.addEventListener('click', async () => {
  if (!currentNoteId) return;

  const title   = document.getElementById('note-title-input')?.value.trim() || 'Untitled';
  const content = document.getElementById('note-textarea')?.value || '';
  const tagsRaw = document.getElementById('tags-input')?.value || '';
  const tags    = tagsRaw.split(',').map(t => t.trim()).filter(Boolean);

  await updateNote(currentNoteId, { title, content, tags });
  renderTagsDisplay(tags);
  renderMarkdownView(content);
  await renderNotesList(document.getElementById('notes-search')?.value || '');
  showToast('Note tersimpan! ✅', 'success');
  setNoteMode('view');
});

// ─── Delete Note ─────────────────────────────────────────
window.confirmDeleteNote = async function(e, id) {
  e.stopPropagation();
  if (!confirm('Hapus catatan ini?')) return;
  await deleteNote(id);
  if (currentNoteId === id) {
    currentNoteId = null;
    document.getElementById('note-placeholder').style.display = 'flex';
    const editorEl = document.getElementById('note-editor');
    editorEl.style.display = 'none';
  }
  await renderNotesList(document.getElementById('notes-search')?.value || '');
  showToast('Note dihapus', 'info');
};

document.getElementById('btn-delete-note')?.addEventListener('click', () => {
  if (!currentNoteId) return;
  confirmDeleteNote({ stopPropagation: () => {} }, currentNoteId);
});

// ─── New Note ─────────────────────────────────────────────
document.getElementById('btn-new-note')?.addEventListener('click', async () => {
  const note = await createNote();
  await openNote(note.id);
  setNoteMode('edit');
  await renderNotesList();
  document.getElementById('note-title-input')?.focus();
});

// ─── Search Notes ─────────────────────────────────────────
document.getElementById('notes-search')?.addEventListener('input', async (e) => {
  await renderNotesList(e.target.value);
});

// ─── AI: Auto-Tag ─────────────────────────────────────────
document.getElementById('btn-autotag')?.addEventListener('click', async () => {
  let content = document.getElementById('note-textarea')?.value;
  if (!content || !content.trim()) {
    const note = await getNote(currentNoteId);
    content = note?.content || '';
  }
  if (!content.trim()) { showToast('Konten note kosong', 'warning'); return; }

  showAIOverlay('🤖 Generating tags...');
  try {
    const result = await callNotesAI('autotag', { content });
    if (Array.isArray(result)) {
      const tagsInput = document.getElementById('tags-input');
      if (tagsInput) tagsInput.value = result.join(', ');
      renderTagsDisplay(result);
      showToast(`Tags: ${result.join(', ')}`, 'success');
    }
  } catch (e) {
    showToast('Gagal generate tags: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
});

// ─── AI: Refine Text ──────────────────────────────────────
document.getElementById('btn-refine')?.addEventListener('click', async () => {
  const textarea = document.getElementById('note-textarea');
  const content  = textarea?.value;
  if (!content?.trim()) { showToast('Konten kosong', 'warning'); return; }

  showAIOverlay('✨ AI merapihkan teks...');
  try {
    const result = await callNotesAI('refine', { content });
    if (textarea && result) {
      textarea.value = result;
      showToast('Teks berhasil dirapihkan! ✨', 'success');
    }
  } catch (e) {
    showToast('Gagal rapihkan: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
});

// ─── AI: Generate Title ───────────────────────────────────
document.getElementById('btn-gen-title')?.addEventListener('click', async () => {
  const content = document.getElementById('note-textarea')?.value || '';
  if (!content.trim()) { showToast('Konten kosong', 'warning'); return; }

  showAIOverlay('🏷️ Generating title...');
  try {
    const result = await callNotesAI('title', { content });
    if (result) {
      const titleInput = document.getElementById('note-title-input');
      if (titleInput) titleInput.value = result;
      showToast(`Title: "${result}"`, 'success');
    }
  } catch (e) {
    showToast('Gagal generate title: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
});

// ─── AI: Generate Metadata (Pydantic AI) ───────────────────
document.getElementById('btn-metadata')?.addEventListener('click', async () => {
  const content = document.getElementById('note-textarea')?.value || '';
  if (!content.trim()) { showToast('Konten kosong', 'warning'); return; }

  showAIOverlay('📊 Pydantic AI mengekstrak metadata...');
  try {
    const result = await callNotesAI('metadata', { content });
    if (result) {
      const titleInput = document.getElementById('note-title-input');
      if (titleInput && result.title) titleInput.value = result.title;
      
      const tagsInput = document.getElementById('tags-input');
      if (tagsInput && result.tags) {
        tagsInput.value = result.tags.join(', ');
        renderTagsDisplay(result.tags);
      }
      
      showToast(`Metadata berhasil diekstrak! Summary: "${result.summary || ''}"`, 'success');
    }
  } catch (e) {
    showToast('Gagal memproses metadata: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
});

// ─── Note Chat ────────────────────────────────────────────
function renderNoteChatMessages() {
  const msgArea = document.getElementById('note-chat-messages');
  if (!msgArea) return;
  if (noteChatHistory.length === 0) {
    msgArea.innerHTML = `<p style="text-align:center;color:var(--text-muted);font-size:0.8rem;padding:var(--space-4);">Tanya tentang isi catatan ini...</p>`;
    return;
  }
  msgArea.innerHTML = noteChatHistory.map(m => `
    <div class="chat-message-item ${m.role === 'user' ? 'chat-user' : 'chat-ai'}">
      <strong class="chat-message-sender">${m.role === 'user' ? '🧑 You' : '⚛️ ATOM'}</strong>
      <div class="chat-message-content">${m.role === 'user' ? escapeHtml(m.content) : renderMarkdown(m.content)}</div>
    </div>
  `).join('');
  msgArea.scrollTop = msgArea.scrollHeight;
}

async function sendNoteChatMessage() {
  const input    = document.getElementById('note-chat-input');
  const question = input?.value.trim();
  if (!question || !currentNoteId) return;

  const note = await getNote(currentNoteId);
  if (!note?.content?.trim()) {
    showToast('Note kosong, tidak ada yang bisa ditanyakan', 'warning');
    return;
  }

  input.value = '';
  noteChatHistory.push({ role: 'user', content: question });
  renderNoteChatMessages();

  try {
    const result = await callNotesAI('chat', { content: note.content, question });
    noteChatHistory.push({ role: 'assistant', content: result });
    renderNoteChatMessages();
  } catch (e) {
    noteChatHistory.push({ role: 'assistant', content: `[ERROR] ${e.message}` });
    renderNoteChatMessages();
  }
}

document.getElementById('btn-note-chat-send')?.addEventListener('click', sendNoteChatMessage);
document.getElementById('note-chat-input')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendNoteChatMessage();
  }
});

document.getElementById('btn-clear-note-chat')?.addEventListener('click', () => {
  noteChatHistory = [];
  renderNoteChatMessages();
});

// ─── API Call Helper ──────────────────────────────────────
async function callNotesAI(action, params) {
  const resp = await fetch('/api/notes_ai', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, ...params })
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${resp.status}`);
  }
  const data = await resp.json();
  return data.result;
}

// ─── AI Overlay ───────────────────────────────────────────
function showAIOverlay(msg = 'AI sedang bekerja...') {
  const el = document.getElementById('ai-overlay');
  const msgEl = document.getElementById('ai-overlay-msg');
  if (el) el.style.display = 'flex';
  if (msgEl) msgEl.textContent = msg;
}

function hideAIOverlay() {
  const el = document.getElementById('ai-overlay');
  if (el) el.style.display = 'none';
}

// ─── Tabs ─────────────────────────────────────────────────
window.switchTab = function(tab) {
  currentTab = tab;
  document.getElementById('tab-notes').style.display    = tab === 'notes'   ? 'flex' : 'none';
  document.getElementById('tab-bubbles').style.display  = tab === 'bubbles' ? 'block' : 'none';
  document.getElementById('tab-notes-btn').classList.toggle('active', tab === 'notes');
  document.getElementById('tab-bubbles-btn').classList.toggle('active', tab === 'bubbles');

  if (tab === 'bubbles') {
    renderBubbles();
    if (!window.bubblesFogInstance && window.BubblesFog) {
      window.bubblesFogInstance = new window.BubblesFog('bubbles-fog-canvas');
    } else if (window.bubblesFogInstance) {
      window.bubblesFogInstance.resize();
    }
  }
};

// ─── Bubbles ──────────────────────────────────────────────
async function renderBubbles() {
  const grid = document.getElementById('bubble-grid');
  if (!grid) return;

  const bubbles = await loadBubbles();

  if (!bubbles.length) {
    grid.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:var(--text-muted);font-size:0.85rem;">Belum ada bubble. Tambah ide pertamamu!</p>`;
    // Resize fog canvas on empty state
    setTimeout(() => {
      if (window.bubblesFogInstance) window.bubblesFogInstance.resize();
    }, 50);
    return;
  }

  grid.innerHTML = bubbles.map(b => `
    <div class="bubble-card" style="
      background: linear-gradient(135deg, ${b.color}33, ${b.color}15);
      border-color: ${b.color}60;
    ">
      <p class="bubble-text">${escapeHtml(b.text)}</p>
      <div class="bubble-footer">
        <span class="bubble-date">${b.created_at.slice(0, 10)} ${b.expanded ? '✨ Expanded' : ''}</span>
        <div class="bubble-actions" style="display:flex;gap:4px;">
          ${!b.expanded 
            ? `<button class="btn btn-primary btn-sm" onclick="expandBubble(${b.id})" title="Expand with CrewAI / LLM">🚀 Expand</button>` 
            : '<span style="font-size:0.75rem;color:var(--success);padding:4px 8px;font-weight:600;">✅ Expanded</span>'}
          <button class="btn btn-danger btn-sm" onclick="removeBubble(${b.id})">🗑</button>
        </div>
      </div>
    </div>
  `).join('');

  // Resize fog canvas to cover new content height
  setTimeout(() => {
    if (window.bubblesFogInstance) window.bubblesFogInstance.resize();
  }, 50);
}

document.getElementById('btn-add-bubble')?.addEventListener('click', async () => {
  const input = document.getElementById('bubble-input');
  const text = input?.value.trim();
  if (!text) return;
  await addBubble(text);
  input.value = '';
  await renderBubbles();
  showToast('Bubble ditambahkan! 🫧', 'success');
});

document.getElementById('bubble-input')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('btn-add-bubble')?.click();
});

window.removeBubble = async function(id) {
  await deleteBubble(id);
  await renderBubbles();
};

window.expandBubble = async function(id) {
  showAIOverlay('CrewAI sedang riset & menulis...');
  try {
    const resp = await fetch(`/api/bubbles/${id}/expand`, { method: 'POST' });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    const res = await resp.json();
    showToast('Bubble berhasil diekspansi menjadi artikel! 🚀', 'success');
    await renderBubbles();
    if (res.note && res.note.id) {
      switchTab('notes');
      await openNote(res.note.id);
    }
  } catch (e) {
    showToast('Gagal ekspansi bubble: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
};

// ─── Tab key for note textarea (insert 2 spaces) ──────────
document.getElementById('note-textarea')?.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const ta = e.target;
    const start = ta.selectionStart;
    const end   = ta.selectionEnd;
    ta.value = ta.value.substring(0, start) + '  ' + ta.value.substring(end);
    ta.selectionStart = ta.selectionEnd = start + 2;
  }
});

// ─── Init ─────────────────────────────────────────────────
async function init() {
  await renderNotesList();
}

init();
