/**
 * A.T.O.M. — Magic Notes & Magic Bubbles Logic
 * Full CRUD, real-time auto-save, resilient error handling, and AI augmentation
 */

// ─── State ────────────────────────────────────────────────
let currentNoteId   = null;
let currentNoteMode = 'edit'; // 'view' | 'edit' | 'chat'
let noteChatHistory = [];
let currentTab      = 'notes';
let autoSaveTimer   = null;
let isSaving        = false;

// ─── Safe Helpers ─────────────────────────────────────────
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;

function normalizeBubbleColor(color) {
  const map = {
    amber: '#f59e0b',
    purple: '#9333ea',
    blue: '#3b82f6',
    teal: '#14b8a6',
    rose: '#f43f5e',
    green: '#10b981',
    gold: '#ebb338'
  };
  if (!color) return '#3b82f6';
  const c = String(color).toLowerCase().trim();
  if (map[c]) return map[c];
  if (c.startsWith('#') && (c.length === 7 || c.length === 4)) return c;
  return '#3b82f6';
}

function formatSafeDate(dateStr) {
  if (!dateStr) return new Date().toISOString().slice(0, 10);
  try {
    const s = String(dateStr);
    return s.length >= 10 ? s.slice(0, 10) : s;
  } catch {
    return new Date().toISOString().slice(0, 10);
  }
}

function setSaveStatus(text, color = 'var(--text-muted)') {
  const el = document.getElementById('note-save-status');
  if (!el) return;
  el.textContent = text;
  el.style.color = color;
}

// ─── Note API Handlers ─────────────────────────────────────
async function createNote(title = 'Catatan Baru', content = '', tags = []) {
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
  try {
    const resp = await fetch(`/api/notes/${id}`);
    if (!resp.ok) return null;
    return await resp.json();
  } catch (err) {
    console.error('[GET NOTE ERROR]', err);
    return null;
  }
}

async function getAllNotes() {
  try {
    const resp = await fetch('/api/notes');
    if (!resp.ok) return [];
    return await resp.json();
  } catch (err) {
    console.error('[GET ALL NOTES ERROR]', err);
    return [];
  }
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
  try {
    const resp = await fetch(`/api/notes/${id}`, { method: 'DELETE' });
    return resp.ok;
  } catch (err) {
    console.error('[DELETE NOTE ERROR]', err);
    return false;
  }
}

async function searchNotes(query) {
  try {
    const q = encodeURIComponent(query.trim());
    const resp = await fetch(`/api/notes?query=${q}`);
    if (!resp.ok) return [];
    return await resp.json();
  } catch (err) {
    console.error('[SEARCH NOTES ERROR]', err);
    return [];
  }
}

async function getAllTags() {
  try {
    const resp = await fetch('/api/notes/tags');
    if (!resp.ok) return [];
    return await resp.json();
  } catch {
    return [];
  }
}

// ─── Bubble API Handlers ───────────────────────────────────
async function loadBubbles() {
  try {
    const resp = await fetch('/api/bubbles');
    if (!resp.ok) return [];
    return await resp.json();
  } catch (err) {
    console.error('[LOAD BUBBLES ERROR]', err);
    return [];
  }
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
  try {
    const resp = await fetch(`/api/bubbles/${id}`, { method: 'DELETE' });
    return resp.ok;
  } catch (err) {
    console.error('[DELETE BUBBLE ERROR]', err);
    return false;
  }
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
    ? `<p style="text-align:center;color:var(--text-muted);font-size:0.8rem;padding:var(--space-4);">Belum ada Magic Note. Klik "New Note" di atas!</p>`
    : notes.map(note => `
        <div class="note-item ${note.id === currentNoteId ? 'active' : ''}" data-id="${note.id}" onclick="openNote(${note.id})">
          <span class="note-item-title">${escapeHtml(note.title || 'Untitled Note')}</span>
          <button class="note-item-delete" onclick="confirmDeleteNote(event, ${note.id})" title="Hapus note" aria-label="Delete">🗑</button>
        </div>
      `).join('');

  if (statsEl) {
    statsEl.textContent = `${allNotes.length} notes · ${allTags.length} tags`;
  }
}

// ─── Open Note ────────────────────────────────────────────
async function openNote(id, targetMode = null) {
  const note = await getNote(id);
  if (!note) return;

  currentNoteId = id;
  noteChatHistory = [];

  // Populate editor fields
  const titleInput = document.getElementById('note-title-input');
  const textarea   = document.getElementById('note-textarea');
  const tagsInput  = document.getElementById('tags-input');

  if (titleInput) titleInput.value = note.title || '';
  if (textarea)   textarea.value = note.content || '';
  if (tagsInput)  tagsInput.value = Array.isArray(note.tags) ? note.tags.join(', ') : '';

  renderTagsDisplay(note.tags || []);
  renderMarkdownView(note.content || '');
  renderNoteChatMessages();

  // Show editor, hide placeholder
  const placeholderEl = document.getElementById('note-placeholder');
  const editorEl      = document.getElementById('note-editor');
  if (placeholderEl) placeholderEl.style.display = 'none';
  if (editorEl) {
    editorEl.style.display = 'flex';
    editorEl.classList.remove('hidden');
  }

  // Determine mode: if note is empty, open in edit mode for immediate typing!
  const hasContent = Boolean(note.content && note.content.trim().length > 0);
  const mode = targetMode || (hasContent ? 'view' : 'edit');
  setNoteMode(mode);

  setSaveStatus('Tersimpan ✓', 'var(--text-muted)');

  // Highlight active note in sidebar
  document.querySelectorAll('.note-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === String(id));
  });

  // On mobile, scroll editor into view smoothly
  if (window.innerWidth <= 768) {
    document.getElementById('note-content-area')?.scrollIntoView({ behavior: 'smooth' });
  }
}
window.openNote = openNote;

function renderMarkdownView(content) {
  const viewEl = document.getElementById('note-view-content');
  if (!viewEl) return;
  if (!content || !content.trim()) {
    viewEl.innerHTML = `
      <div style="padding:var(--space-6);text-align:center;color:var(--text-muted);border:1px dashed rgba(255,255,255,0.1);border-radius:var(--radius-lg);cursor:pointer;" onclick="setNoteMode('edit')" title="Klik untuk mulai menulis">
        <p style="font-size:1.1rem;margin-bottom:6px;">✍️ Catatan ini masih kosong</p>
        <p style="font-size:0.8rem;color:var(--gold-light);">Klik di sini atau tombol "✏️ Edit" di atas untuk mulai mengetik.</p>
      </div>`;
    return;
  }
  const renderer = window.renderMarkdown || marked.parse;
  viewEl.innerHTML = renderer(content);
}

function renderTagsDisplay(tags) {
  const tagsDisplay = document.getElementById('tags-display');
  if (!tagsDisplay) return;
  if (!Array.isArray(tags) || tags.length === 0) {
    tagsDisplay.innerHTML = '';
    return;
  }
  tagsDisplay.innerHTML = tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join(' ');
}

// ─── Note Mode ────────────────────────────────────────────
window.setNoteMode = function(mode) {
  // If switching from edit to view, sync view content immediately
  if (currentNoteMode === 'edit' && mode === 'view') {
    const currentText = document.getElementById('note-textarea')?.value || '';
    renderMarkdownView(currentText);
    triggerAutoSave(true);
  }

  currentNoteMode = mode;
  const modes = ['view', 'edit', 'chat'];
  modes.forEach(m => {
    const panel = document.getElementById(`note-${m}-content`);
    if (panel) {
      panel.style.display = m === mode ? (m === 'chat' ? 'flex' : 'block') : 'none';
    }
    const btn = document.getElementById(`mode-${m}-btn`);
    if (btn) btn.classList.toggle('active', m === mode);
  });

  // Auto-focus textarea when entering edit mode
  if (mode === 'edit') {
    const ta = document.getElementById('note-textarea');
    if (ta && document.activeElement !== ta && document.activeElement !== document.getElementById('note-title-input')) {
      ta.focus();
    }
  }
};

// ─── Real-Time Auto-Save & Manual Save ────────────────────
async function persistNote(id, isExplicitSave = false) {
  if (!id) return;
  if (isSaving) return;
  isSaving = true;

  const titleInput = document.getElementById('note-title-input');
  const textarea   = document.getElementById('note-textarea');
  const tagsInput  = document.getElementById('tags-input');

  const title   = titleInput?.value.trim() || 'Untitled Note';
  const content = textarea?.value || '';
  const tagsRaw = tagsInput?.value || '';
  const tags    = tagsRaw.split(',').map(t => t.trim()).filter(Boolean);

  setSaveStatus('Menyimpan...', 'var(--gold-light)');

  try {
    await updateNote(id, { title, content, tags });
    renderTagsDisplay(tags);
    setSaveStatus('Tersimpan otomatis ✓', 'var(--success)');

    // Update title in sidebar active item without full reload
    const activeItem = document.querySelector(`.note-item[data-id="${id}"] .note-item-title`);
    if (activeItem) {
      activeItem.textContent = title;
    }

    if (isExplicitSave) {
      renderMarkdownView(content);
      showToast('Magic Note tersimpan! ✅', 'success');
      setNoteMode('view');
    }
  } catch (err) {
    setSaveStatus('Gagal simpan!', 'var(--error)');
    if (isExplicitSave) {
      showToast('Gagal menyimpan note: ' + err.message, 'error');
    }
  } finally {
    isSaving = false;
  }
}

function triggerAutoSave(immediate = false) {
  if (!currentNoteId) return;
  clearTimeout(autoSaveTimer);
  if (immediate) {
    persistNote(currentNoteId, false);
  } else {
    setSaveStatus('Perubahan belum tersimpan...', 'var(--text-muted)');
    autoSaveTimer = setTimeout(() => {
      persistNote(currentNoteId, false);
    }, 750);
  }
}

// Input listeners for Auto-Save
document.getElementById('note-title-input')?.addEventListener('input', () => triggerAutoSave());
document.getElementById('note-textarea')?.addEventListener('input', () => triggerAutoSave());
document.getElementById('tags-input')?.addEventListener('input', () => triggerAutoSave());

// Manual Save button
document.getElementById('btn-save-note')?.addEventListener('click', async () => {
  if (!currentNoteId) {
    showToast('Pilih atau buat note terlebih dahulu', 'warning');
    return;
  }
  clearTimeout(autoSaveTimer);
  await persistNote(currentNoteId, true);
});

// Click on markdown view switches to edit mode
document.getElementById('note-view-content')?.addEventListener('click', (e) => {
  // Don't switch if user clicked an external link
  if (e.target.tagName === 'A') return;
  setNoteMode('edit');
});

// ─── Delete Note ─────────────────────────────────────────
window.confirmDeleteNote = async function(e, id) {
  if (e && e.stopPropagation) e.stopPropagation();
  if (!confirm('Hapus Magic Note ini?')) return;

  const success = await deleteNote(id);
  if (success) {
    if (currentNoteId === id) {
      currentNoteId = null;
      document.getElementById('note-placeholder').style.display = 'flex';
      const editorEl = document.getElementById('note-editor');
      if (editorEl) editorEl.style.display = 'none';
    }
    await renderNotesList(document.getElementById('notes-search')?.value || '');
    showToast('Magic Note dihapus 🗑', 'info');
  } else {
    showToast('Gagal menghapus note', 'error');
  }
};

document.getElementById('btn-delete-note')?.addEventListener('click', () => {
  if (!currentNoteId) return;
  confirmDeleteNote({ stopPropagation: () => {} }, currentNoteId);
});

// ─── New Note ─────────────────────────────────────────────
document.getElementById('btn-new-note')?.addEventListener('click', async () => {
  const btn = document.getElementById('btn-new-note');
  if (btn) btn.disabled = true;

  try {
    const note = await createNote('Catatan Baru', '', []);
    await renderNotesList();
    await openNote(note.id, 'edit');
    const titleInput = document.getElementById('note-title-input');
    if (titleInput) {
      titleInput.focus();
      titleInput.select();
    }
    showToast('Magic Note baru siap diedit! ✨', 'success');
  } catch (err) {
    showToast('Gagal membuat note: ' + err.message, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
});

// ─── Search Notes ─────────────────────────────────────────
document.getElementById('notes-search')?.addEventListener('input', async (e) => {
  await renderNotesList(e.target.value);
});

// ─── AI Tools ─────────────────────────────────────────────
document.getElementById('btn-autotag')?.addEventListener('click', async () => {
  let content = document.getElementById('note-textarea')?.value;
  if (!content || !content.trim()) {
    const note = await getNote(currentNoteId);
    content = note?.content || '';
  }
  if (!content.trim()) {
    showToast('Isi konten catatan terlebih dahulu', 'warning');
    return;
  }

  showAIOverlay('🤖 Magic Tagging sedang menganalisis...');
  try {
    const result = await callNotesAI('autotag', { content });
    if (Array.isArray(result)) {
      const tagsInput = document.getElementById('tags-input');
      if (tagsInput) tagsInput.value = result.join(', ');
      renderTagsDisplay(result);
      triggerAutoSave(true);
      showToast(`Tags terpasang: ${result.join(', ')}`, 'success');
    }
  } catch (e) {
    showToast('Gagal auto-tag: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
});

document.getElementById('btn-refine')?.addEventListener('click', async () => {
  const textarea = document.getElementById('note-textarea');
  const content  = textarea?.value;
  if (!content?.trim()) {
    showToast('Teks catatan masih kosong', 'warning');
    return;
  }

  showAIOverlay('✨ AI sedang merapihkan teks & format Markdown...');
  try {
    const result = await callNotesAI('refine', { content });
    if (textarea && result) {
      textarea.value = result;
      triggerAutoSave(true);
      showToast('Teks berhasil dirapihkan! ✨', 'success');
    }
  } catch (e) {
    showToast('Gagal merapihkan teks: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
});

document.getElementById('btn-gen-title')?.addEventListener('click', async () => {
  const content = document.getElementById('note-textarea')?.value || '';
  if (!content.trim()) {
    showToast('Tulis isi catatan terlebih dahulu', 'warning');
    return;
  }

  showAIOverlay('🏷️ Menghasilkan judul cerdas...');
  try {
    const result = await callNotesAI('title', { content });
    if (result) {
      const titleInput = document.getElementById('note-title-input');
      if (titleInput) titleInput.value = result;
      triggerAutoSave(true);
      showToast(`Judul diperbarui: "${result}"`, 'success');
    }
  } catch (e) {
    showToast('Gagal generate judul: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
});

document.getElementById('btn-metadata')?.addEventListener('click', async () => {
  const content = document.getElementById('note-textarea')?.value || '';
  if (!content.trim()) {
    showToast('Tulis isi catatan terlebih dahulu', 'warning');
    return;
  }

  showAIOverlay('📊 Mengekstrak metadata terstruktur...');
  try {
    const result = await callNotesAI('metadata', { content });
    if (result) {
      const titleInput = document.getElementById('note-title-input');
      if (titleInput && result.title) titleInput.value = result.title;
      
      const tagsInput = document.getElementById('tags-input');
      if (tagsInput && Array.isArray(result.tags)) {
        tagsInput.value = result.tags.join(', ');
        renderTagsDisplay(result.tags);
      }
      triggerAutoSave(true);
      showToast(`Metadata diekstrak! Summary: "${result.summary || ''}"`, 'success');
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
    msgArea.innerHTML = `<p style="text-align:center;color:var(--text-muted);font-size:0.8rem;padding:var(--space-4);">Tanya apa saja tentang isi catatan ini (NotebookLM style)...</p>`;
    return;
  }
  const renderer = window.renderMarkdown || marked.parse;
  msgArea.innerHTML = noteChatHistory.map(m => `
    <div class="chat-message-item ${m.role === 'user' ? 'chat-user' : 'chat-ai'}">
      <strong class="chat-message-sender">${m.role === 'user' ? '🧑 You' : '⚛️ ATOM'}</strong>
      <div class="chat-message-content">${m.role === 'user' ? escapeHtml(m.content) : renderer(m.content)}</div>
    </div>
  `).join('');
  msgArea.scrollTop = msgArea.scrollHeight;
}

async function sendNoteChatMessage() {
  const input    = document.getElementById('note-chat-input');
  const question = input?.value.trim();
  if (!question || !currentNoteId) return;

  const note = await getNote(currentNoteId);
  const currentContent = document.getElementById('note-textarea')?.value || note?.content || '';
  if (!currentContent.trim()) {
    showToast('Catatan kosong, tidak ada bahan untuk ditanyakan', 'warning');
    return;
  }

  input.value = '';
  noteChatHistory.push({ role: 'user', content: question });
  renderNoteChatMessages();

  try {
    const result = await callNotesAI('chat', { content: currentContent, question });
    noteChatHistory.push({ role: 'assistant', content: result || 'Tidak ada respons dari AI.' });
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
    throw new Error(err.detail || err.error || `HTTP ${resp.status}`);
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

// ─── Tabs Switching ───────────────────────────────────────
window.switchTab = function(tab) {
  currentTab = tab;
  const tabNotesEl   = document.getElementById('tab-notes');
  const tabBubblesEl = document.getElementById('tab-bubbles');
  const tabNotesBtn  = document.getElementById('tab-notes-btn');
  const tabBubblesBtn = document.getElementById('tab-bubbles-btn');

  if (tabNotesEl)   tabNotesEl.style.display   = tab === 'notes' ? 'flex' : 'none';
  if (tabBubblesEl) tabBubblesEl.style.display = tab === 'bubbles' ? 'block' : 'none';
  if (tabNotesBtn)  tabNotesBtn.classList.toggle('active', tab === 'notes');
  if (tabBubblesBtn) tabBubblesBtn.classList.toggle('active', tab === 'bubbles');

  if (tab === 'bubbles') {
    renderBubbles();
    if (!window.bubblesFogInstance && window.BubblesFog) {
      window.bubblesFogInstance = new window.BubblesFog('bubbles-fog-canvas');
    } else if (window.bubblesFogInstance) {
      window.bubblesFogInstance.resize();
    }
  }
};

// ─── Magic Bubbles Logic ──────────────────────────────────
async function renderBubbles() {
  const grid = document.getElementById('bubble-grid');
  if (!grid) return;

  const bubbles = await loadBubbles();

  if (!bubbles || bubbles.length === 0) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;color:var(--text-muted);font-size:0.85rem;padding:var(--space-8);background:rgba(22,27,34,0.4);border-radius:var(--radius-xl);border:1px dashed rgba(255,255,255,0.08);">
        <p style="font-size:1.5rem;margin-bottom:8px;">🫧</p>
        <p>Belum ada ide di Magic Bubbles.</p>
        <p style="font-size:0.75rem;color:var(--gold-light);margin-top:4px;">Ketik ide kilat di kolom input di atas dan tekan <strong>+ Add Bubble</strong>!</p>
      </div>`;
    setTimeout(() => {
      if (window.bubblesFogInstance) window.bubblesFogInstance.resize();
    }, 50);
    return;
  }

  grid.innerHTML = bubbles.map(b => {
    const hex = normalizeBubbleColor(b.color);
    const date = formatSafeDate(b.created_at);
    return `
      <div class="bubble-card" style="
        background: linear-gradient(135deg, ${hex}28, rgba(22, 27, 34, 0.75));
        border: 1px solid ${hex}55;
        box-shadow: 0 4px 16px ${hex}18;
      ">
        <p class="bubble-text">${escapeHtml(b.text || '')}</p>
        <div class="bubble-footer">
          <span class="bubble-date">${date} ${b.expanded ? '✨ Expanded' : ''}</span>
          <div class="bubble-actions" style="display:flex;gap:6px;">
            ${!b.expanded 
              ? `<button class="btn btn-primary btn-sm" onclick="expandBubble(${b.id})" title="Kembangkan menjadi artikel penuh">🚀 Expand</button>` 
              : '<span style="font-size:0.72rem;color:var(--success);padding:4px 6px;font-weight:700;">✅ Expanded</span>'}
            <button class="btn btn-danger btn-sm" onclick="removeBubble(${b.id})" title="Hapus bubble">🗑</button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  setTimeout(() => {
    if (window.bubblesFogInstance) window.bubblesFogInstance.resize();
  }, 50);
}

// Add Bubble Button
document.getElementById('btn-add-bubble')?.addEventListener('click', async () => {
  const input = document.getElementById('bubble-input');
  const btn   = document.getElementById('btn-add-bubble');
  const text  = input?.value.trim();

  if (!text) {
    showToast('Ketik ide singkat terlebih dahulu!', 'warning');
    input?.focus();
    return;
  }

  if (btn) btn.disabled = true;

  try {
    await addBubble(text);
    input.value = '';
    await renderBubbles();
    showToast('Magic Bubble ditambahkan! 🫧', 'success');
  } catch (err) {
    showToast('Gagal menambahkan bubble: ' + err.message, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
});

document.getElementById('bubble-input')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    document.getElementById('btn-add-bubble')?.click();
  }
});

window.removeBubble = async function(id) {
  if (!confirm('Hapus Magic Bubble ini?')) return;
  const ok = await deleteBubble(id);
  if (ok) {
    await renderBubbles();
    showToast('Bubble dihapus', 'info');
  } else {
    showToast('Gagal menghapus bubble', 'error');
  }
};

window.expandBubble = async function(id) {
  showAIOverlay('CrewAI sedang meriset & menulis artikel...');
  try {
    const resp = await fetch(`/api/bubbles/${id}/expand`, { method: 'POST' });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    const res = await resp.json();
    showToast('Bubble berhasil diekspansi menjadi Magic Note! 🚀', 'success');
    await renderBubbles();
    if (res.note && res.note.id) {
      switchTab('notes');
      await renderNotesList();
      await openNote(res.note.id);
    }
  } catch (e) {
    showToast('Gagal ekspansi bubble: ' + e.message, 'error');
  } finally {
    hideAIOverlay();
  }
};

// ─── Tab key inside textarea ──────────────────────────────
document.getElementById('note-textarea')?.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const ta = e.target;
    const start = ta.selectionStart;
    const end   = ta.selectionEnd;
    ta.value = ta.value.substring(0, start) + '  ' + ta.value.substring(end);
    ta.selectionStart = ta.selectionEnd = start + 2;
    triggerAutoSave();
  }
});

// ─── Initialization ───────────────────────────────────────
async function init() {
  await renderNotesList();
  
  // If there are existing notes, auto-select the latest one so screen is never blank
  const notes = await getAllNotes();
  if (notes.length > 0 && !currentNoteId) {
    await openNote(notes[0].id);
  }
}

init();
