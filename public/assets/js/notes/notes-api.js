// ─── ATOM Notes: API & State ─────────────────────────────
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
let allNotesCache   = [];

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

