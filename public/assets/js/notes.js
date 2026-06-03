/**
 * A.T.O.M. — Notes Logic
 * CRUD operations in localStorage, AI features via /api/notes_ai
 */

// ─── Storage Key ──────────────────────────────────────────
const NOTES_KEY   = 'atom_smart_notes';
const BUBBLES_KEY = 'atom_bubbles';

// ─── State ────────────────────────────────────────────────
let currentNoteId  = null;
let currentNoteMode = 'view'; // 'view' | 'edit' | 'chat'
let noteChatHistory = [];
let currentTab     = 'notes';

// ─── Note Storage ─────────────────────────────────────────
function loadNotes() {
  try {
    return JSON.parse(localStorage.getItem(NOTES_KEY) || '{"notes":[],"lastId":0}');
  } catch { return { notes: [], lastId: 0 }; }
}

function saveNotes(db) {
  localStorage.setItem(NOTES_KEY, JSON.stringify(db));
}

function createNote(title = 'Untitled Note', content = '', tags = []) {
  const db = loadNotes();
  const id = db.lastId + 1;
  const now = new Date().toISOString();
  const note = { id, title, content, tags, type: 'note', createdAt: now, updatedAt: now };
  db.notes.push(note);
  db.lastId = id;
  saveNotes(db);
  return note;
}

function getNote(id) {
  const db = loadNotes();
  return db.notes.find(n => n.id === id) || null;
}

function getAllNotes() {
  const db = loadNotes();
  return [...db.notes].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

function updateNote(id, updates) {
  const db = loadNotes();
  const idx = db.notes.findIndex(n => n.id === id);
  if (idx === -1) return null;
  db.notes[idx] = { ...db.notes[idx], ...updates, updatedAt: new Date().toISOString() };
  saveNotes(db);
  return db.notes[idx];
}

function deleteNote(id) {
  const db = loadNotes();
  db.notes = db.notes.filter(n => n.id !== id);
  saveNotes(db);
}

function searchNotes(query) {
  const notes = getAllNotes();
  if (!query.trim()) return notes;
  const q = query.toLowerCase();
  return notes.filter(n =>
    n.title.toLowerCase().includes(q) ||
    n.content.toLowerCase().includes(q) ||
    n.tags.some(t => t.toLowerCase().includes(q))
  );
}

function getAllTags() {
  const notes = getAllNotes();
  const tags = new Set();
  notes.forEach(n => n.tags?.forEach(t => tags.add(t)));
  return [...tags].sort();
}

// ─── Bubble Storage ───────────────────────────────────────
const BUBBLE_COLORS = ['#9333EA', '#3B82F6', '#14B8A6', '#F59E0B', '#F43F5E', '#10B981'];

function loadBubbles() {
  try {
    return JSON.parse(localStorage.getItem(BUBBLES_KEY) || '{"bubbles":[],"lastId":0}');
  } catch { return { bubbles: [], lastId: 0 }; }
}

function saveBubbles(db) {
  localStorage.setItem(BUBBLES_KEY, JSON.stringify(db));
}

function addBubble(text) {
  const db = loadBubbles();
  const id = db.lastId + 1;
  const bubble = {
    id,
    text,
    color: BUBBLE_COLORS[Math.floor(Math.random() * BUBBLE_COLORS.length)],
    createdAt: new Date().toISOString(),
    expanded: false
  };
  db.bubbles.unshift(bubble);
  db.lastId = id;
  saveBubbles(db);
  return bubble;
}

function deleteBubble(id) {
  const db = loadBubbles();
  db.bubbles = db.bubbles.filter(b => b.id !== id);
  saveBubbles(db);
}


// ─── Render Notes Sidebar ─────────────────────────────────
function renderNotesList(query = '') {
  const notesList = document.getElementById('notes-list');
  const statsEl   = document.getElementById('notes-stats');
  if (!notesList) return;

  const notes = searchNotes(query);
  const allTags = getAllTags();

  notesList.innerHTML = notes.length === 0
    ? `<p style="text-align:center;color:var(--text-muted);font-size:0.8rem;padding:var(--space-4);">Tidak ada catatan. Buat baru!</p>`
    : notes.map(note => `
        <div class="note-item ${note.id === currentNoteId ? 'active' : ''}" onclick="openNote(${note.id})">
          <span class="note-item-title">${escapeHtml(note.title)}</span>
          <button class="note-item-delete" onclick="confirmDeleteNote(event, ${note.id})" aria-label="Delete">🗑</button>
        </div>
      `).join('');

  if (statsEl) {
    statsEl.textContent = `${getAllNotes().length} notes · ${allTags.length} tags`;
  }
}

// ─── Open Note ────────────────────────────────────────────
function openNote(id) {
  const note = getNote(id);
  if (!note) return;

  currentNoteId = id;
  noteChatHistory = [];
  setNoteMode('view');
  renderNotesList(document.getElementById('notes-search')?.value || '');

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
document.getElementById('btn-save-note')?.addEventListener('click', () => {
  if (!currentNoteId) return;

  const title   = document.getElementById('note-title-input')?.value.trim() || 'Untitled';
  const content = document.getElementById('note-textarea')?.value || '';
  const tagsRaw = document.getElementById('tags-input')?.value || '';
  const tags    = tagsRaw.split(',').map(t => t.trim()).filter(Boolean);

  updateNote(currentNoteId, { title, content, tags });
  renderTagsDisplay(tags);
  renderMarkdownView(content);
  renderNotesList(document.getElementById('notes-search')?.value || '');
  showToast('Note tersimpan! ✅', 'success');
  setNoteMode('view');
});

// ─── Delete Note ─────────────────────────────────────────
window.confirmDeleteNote = function(e, id) {
  e.stopPropagation();
  if (!confirm('Hapus catatan ini?')) return;
  deleteNote(id);
  if (currentNoteId === id) {
    currentNoteId = null;
    document.getElementById('note-placeholder').style.display = 'flex';
    const editorEl = document.getElementById('note-editor');
    editorEl.style.display = 'none';
  }
  renderNotesList(document.getElementById('notes-search')?.value || '');
  showToast('Note dihapus', 'info');
};

document.getElementById('btn-delete-note')?.addEventListener('click', () => {
  if (!currentNoteId) return;
  confirmDeleteNote({ stopPropagation: () => {} }, currentNoteId);
});

// ─── New Note ─────────────────────────────────────────────
document.getElementById('btn-new-note')?.addEventListener('click', () => {
  const note = createNote();
  openNote(note.id);
  setNoteMode('edit');
  renderNotesList();
  document.getElementById('note-title-input')?.focus();
});

// ─── Search Notes ─────────────────────────────────────────
document.getElementById('notes-search')?.addEventListener('input', (e) => {
  renderNotesList(e.target.value);
});

// ─── AI: Auto-Tag ─────────────────────────────────────────
document.getElementById('btn-autotag')?.addEventListener('click', async () => {
  const content = document.getElementById('note-textarea')?.value || getNote(currentNoteId)?.content || '';
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

// ─── Note Chat ────────────────────────────────────────────
function renderNoteChatMessages() {
  const msgArea = document.getElementById('note-chat-messages');
  if (!msgArea) return;
  if (noteChatHistory.length === 0) {
    msgArea.innerHTML = `<p style="text-align:center;color:var(--text-muted);font-size:0.8rem;padding:var(--space-4);">Tanya tentang isi catatan ini...</p>`;
    return;
  }
  msgArea.innerHTML = noteChatHistory.map(m => `
    <div class="${m.role === 'user' ? 'chat-user' : 'chat-ai'}" style="
      background: var(--bg-elevated);
      border-left: 3px solid ${m.role === 'user' ? 'var(--text-muted)' : 'var(--gold-primary)'};
      border-radius: 4px;
      padding: 10px 14px;
      font-size: 0.85rem;
      color: var(--text-primary);
    ">
      <strong style="font-size:0.72rem;color:${m.role === 'user' ? 'var(--text-muted)' : 'var(--gold-primary)'};">${m.role === 'user' ? '🧑 You' : '⚛️ ATOM'}</strong>
      <div style="margin-top:4px;">${m.role === 'user' ? escapeHtml(m.content) : renderMarkdown(m.content)}</div>
    </div>
  `).join('');
  msgArea.scrollTop = msgArea.scrollHeight;
}

async function sendNoteChatMessage() {
  const input    = document.getElementById('note-chat-input');
  const question = input?.value.trim();
  if (!question || !currentNoteId) return;

  const note = getNote(currentNoteId);
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

  if (tab === 'bubbles') renderBubbles();
};

// ─── Bubbles ──────────────────────────────────────────────
function renderBubbles() {
  const grid = document.getElementById('bubble-grid');
  if (!grid) return;

  const data = loadBubbles();
  const bubbles = data.bubbles;

  if (!bubbles.length) {
    grid.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:var(--text-muted);font-size:0.85rem;">Belum ada bubble. Tambah ide pertamamu!</p>`;
    return;
  }

  grid.innerHTML = bubbles.map(b => `
    <div class="bubble-card" style="
      background: linear-gradient(135deg, ${b.color}33, ${b.color}15);
      border-color: ${b.color}60;
    ">
      <p class="bubble-text">${escapeHtml(b.text)}</p>
      <div class="bubble-footer">
        <span class="bubble-date">${b.createdAt.slice(0, 10)} ${b.expanded ? '✨ Expanded' : ''}</span>
        <div class="bubble-actions">
          <button class="btn btn-danger btn-sm" onclick="removeBubble(${b.id})">🗑</button>
        </div>
      </div>
    </div>
  `).join('');
}

document.getElementById('btn-add-bubble')?.addEventListener('click', () => {
  const input = document.getElementById('bubble-input');
  const text = input?.value.trim();
  if (!text) return;
  addBubble(text);
  input.value = '';
  renderBubbles();
  showToast('Bubble ditambahkan! 🫧', 'success');
});

document.getElementById('bubble-input')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('btn-add-bubble')?.click();
});

window.removeBubble = function(id) {
  deleteBubble(id);
  renderBubbles();
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
function init() {
  renderNotesList();
}

init();
