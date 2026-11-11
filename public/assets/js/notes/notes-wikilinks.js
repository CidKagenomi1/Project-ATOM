// ─── ATOM Notes: Knowledge Interconnection & Wikilinks ──
// ─── Knowledge Interconnection & Wikilinks Logic ──────────

function parseWikilinks(html, allNotes = []) {
  if (!html) return '';
  return html.replace(/\[\[(.*?)\]\]/g, (match, raw) => {
    const trimmed = raw.trim();
    if (!trimmed) return match;

    const parts = trimmed.split('|');
    const targetTitle = parts[0].trim();
    const displayLabel = (parts[1] || parts[0]).trim();

    const exists = allNotes.some(n => n.title && n.title.toLowerCase().trim() === targetTitle.toLowerCase());
    if (exists) {
      return `<a href="javascript:void(0)" class="atom-wikilink" onclick="openNoteByTitle('${escapeHtml(targetTitle)}')"><span class="wikilink-icon">🔗</span> ${escapeHtml(displayLabel)}</a>`;
    } else {
      return `<a href="javascript:void(0)" class="atom-wikilink new" title="Catatan belum dibuat. Klik untuk membuat baru." onclick="createAndOpenWikilink('${escapeHtml(targetTitle)}')"><span class="wikilink-icon">➕</span> ${escapeHtml(displayLabel)}</a>`;
    }
  });
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

window.openNoteByTitle = async function(title) {
  if (!title) return;
  const notes = await getAllNotes();
  allNotesCache = notes;
  const found = notes.find(n => n.title && n.title.toLowerCase().trim() === title.toLowerCase().trim());
  if (found) {
    await openNote(found.id);
    showToast(`Membuka catatan "${found.title}" 🔗`, 'info');
  } else {
    await createAndOpenWikilink(title);
  }
};

window.createAndOpenWikilink = async function(title) {
  if (!title) return;
  try {
    const newNote = await createNote(title, `# ${title}\n\nCatatan ini ditautkan secara cerdas via Wikilink.\n`, ['wikilink']);
    await renderNotesList();
    await openNote(newNote.id, 'edit');
    showToast(`Catatan baru "${title}" berhasil dibuat & ditautkan! ✨`, 'success');
  } catch (err) {
    showToast(`Gagal membuat catatan: ${err.message}`, 'error');
  }
};

window.toggleKnowledgePanel = function() {
  const body = document.getElementById('knowledge-panel-body');
  const toggleBtn = document.getElementById('btn-knowledge-toggle');
  if (!body) return;
  const isClosed = body.style.display === 'none';
  body.style.display = isClosed ? 'block' : 'none';
  if (toggleBtn) {
    toggleBtn.textContent = isClosed ? '▼' : '▲';
  }
};

async function updateKnowledgeConnections(noteId) {
  if (!noteId) return;
  try {
    const notes = await getAllNotes();
    allNotesCache = notes;
    const currentNote = notes.find(n => n.id === noteId);
    if (!currentNote) return;

    const currentTitle = (currentNote.title || '').toLowerCase().trim();
    const currentContent = currentNote.content || '';

    // 1. Outbound References from current note
    const outboundMatches = [...currentContent.matchAll(/\[\[(.*?)\]\]/g)];
    const outboundTitles = [...new Set(outboundMatches.map(m => m[1].split('|')[0].trim()))].filter(Boolean);

    const outboundListEl = document.getElementById('outbound-list');
    const outboundCountEl = document.getElementById('outbound-count');
    if (outboundCountEl) outboundCountEl.textContent = outboundTitles.length;

    if (outboundListEl) {
      if (outboundTitles.length === 0) {
        outboundListEl.innerHTML = `<p class="knowledge-empty">Belum ada rujukan. Ketik <code>[[Nama Catatan]]</code> di teks untuk menghubungkan.</p>`;
      } else {
        outboundListEl.innerHTML = outboundTitles.map(targetTitle => {
          const targetNote = notes.find(n => n.title && n.title.toLowerCase().trim() === targetTitle.toLowerCase());
          const exists = Boolean(targetNote);
          const snippet = exists && targetNote.content
            ? escapeHtml(targetNote.content.slice(0, 70).replace(/\n/g, ' '))
            : 'Belum dibuat • Klik untuk membuat catatan baru';
          return `
            <div class="knowledge-item" onclick="openNoteByTitle('${escapeHtml(targetTitle)}')">
              <span class="knowledge-item-title">
                <span>${exists ? '🔗' : '➕'}</span> ${escapeHtml(targetTitle)}
              </span>
              <span class="knowledge-item-snippet">${snippet}</span>
            </div>
          `;
        }).join('');
      }
    }

    // 2. Linked Mentions (Backlinks) from other notes
    const backlinks = [];
    if (currentTitle) {
      notes.forEach(otherNote => {
        if (otherNote.id === noteId) return;
        const otherContent = otherNote.content || '';
        const pattern = new RegExp(`\\[\\[${escapeRegex(currentTitle)}(\\|[^\\]]+)?\\]\\]`, 'i');
        const match = otherContent.match(pattern);
        if (match) {
          const idx = match.index || 0;
          const start = Math.max(0, idx - 30);
          const end = Math.min(otherContent.length, idx + match[0].length + 40);
          const snippet = (start > 0 ? '...' : '') + otherContent.substring(start, end).replace(/\n/g, ' ') + (end < otherContent.length ? '...' : '');
          backlinks.push({
            id: otherNote.id,
            title: otherNote.title || 'Untitled Note',
            snippet
          });
        }
      });
    }

    const backlinksListEl = document.getElementById('backlinks-list');
    const backlinksCountEl = document.getElementById('backlinks-count');
    if (backlinksCountEl) backlinksCountEl.textContent = backlinks.length;

    if (backlinksListEl) {
      if (backlinks.length === 0) {
        backlinksListEl.innerHTML = `<p class="knowledge-empty">Tidak ada catatan lain yang menautkan catatan ini.</p>`;
      } else {
        backlinksListEl.innerHTML = backlinks.map(b => `
          <div class="knowledge-item" onclick="openNote(${b.id})">
            <span class="knowledge-item-title">
              <span>📥</span> ${escapeHtml(b.title)}
            </span>
            <span class="knowledge-item-snippet">${escapeHtml(b.snippet)}</span>
          </div>
        `).join('');
      }
    }

    // Update total badge & connections button
    const total = outboundTitles.length + backlinks.length;
    const badgeEl = document.getElementById('knowledge-badge');
    if (badgeEl) badgeEl.textContent = `${total} Links`;

    const connCountEl = document.getElementById('connections-count');
    if (connCountEl) connCountEl.textContent = `${total} Relasi`;
  } catch (err) {
    console.error('[KNOWLEDGE ERROR]', err);
  }
}

// ─── Wikilink Autocomplete Dropdown Logic ─────────────────
let activeAutocompleteIndex = 0;
let filteredWikilinkNotes = [];
let currentWikilinkQuery = '';

function checkWikilinkAutocomplete(e) {
  const ta = document.getElementById('note-textarea');
  const dropdown = document.getElementById('wikilink-autocomplete');
  if (!ta || !dropdown) return;

  const cursorPos = ta.selectionStart;
  const textBefore = ta.value.substring(0, cursorPos);
  const match = textBefore.match(/\[\[([^\]\n]*)$/);

  if (!match) {
    dropdown.classList.add('hidden');
    return;
  }

  currentWikilinkQuery = match[1].toLowerCase().trim();
  filteredWikilinkNotes = allNotesCache.filter(n => {
    if (n.id === currentNoteId) return false;
    if (!currentWikilinkQuery) return true;
    return (n.title || '').toLowerCase().includes(currentWikilinkQuery);
  }).slice(0, 6);

  activeAutocompleteIndex = 0;
  renderWikilinkDropdown(currentWikilinkQuery);

  const rect = ta.getBoundingClientRect();
  dropdown.style.left = `${Math.min(rect.left + 24, window.innerWidth - 320)}px`;
  dropdown.style.top = `${Math.min(rect.top + 70, window.innerHeight - 250)}px`;
  dropdown.classList.remove('hidden');
}

function renderWikilinkDropdown(query = '') {
  const listEl = document.getElementById('wikilink-autocomplete-list');
  if (!listEl) return;

  let html = filteredWikilinkNotes.map((note, idx) => `
    <div class="wikilink-option ${idx === activeAutocompleteIndex ? 'active' : ''}" data-idx="${idx}" onclick="selectWikilinkNote('${escapeHtml(note.title)}')">
      <span>🔗 ${escapeHtml(note.title || 'Untitled')}</span>
      <span class="wikilink-option-tag">${note.tags && note.tags[0] ? '#' + escapeHtml(note.tags[0]) : ''}</span>
    </div>
  `).join('');

  if (query && !filteredWikilinkNotes.some(n => (n.title || '').toLowerCase() === query)) {
    const isNewActive = activeAutocompleteIndex === filteredWikilinkNotes.length;
    html += `
      <div class="wikilink-option ${isNewActive ? 'active' : ''}" onclick="selectWikilinkNote('${escapeHtml(query)}')">
        <span>➕ Buat baru: "${escapeHtml(query)}"</span>
      </div>
    `;
  }

  if (!html) {
    html = `<div style="padding:8px 12px;font-size:0.75rem;color:var(--text-muted);">Ketik nama catatan untuk mencari...</div>`;
  }

  listEl.innerHTML = html;
}

window.selectWikilinkNote = function(title) {
  const ta = document.getElementById('note-textarea');
  const dropdown = document.getElementById('wikilink-autocomplete');
  if (!ta) return;

  const cursorPos = ta.selectionStart;
  const textBefore = ta.value.substring(0, cursorPos);
  const textAfter = ta.value.substring(cursorPos);
  const match = textBefore.match(/\[\[([^\]\n]*)$/);

  if (match) {
    const replaceStart = match.index;
    const insertion = `[[${title}]] `;
    ta.value = ta.value.substring(0, replaceStart) + insertion + textAfter;
    ta.selectionStart = ta.selectionEnd = replaceStart + insertion.length;
    ta.focus();
    triggerAutoSave();
  }

  if (dropdown) dropdown.classList.add('hidden');
};

// Autocomplete keyboard & dismissal events
document.getElementById('note-textarea')?.addEventListener('input', checkWikilinkAutocomplete);
document.getElementById('note-textarea')?.addEventListener('keyup', (e) => {
  if (['[', 'Backspace', 'Delete'].includes(e.key)) {
    checkWikilinkAutocomplete(e);
  }
});

document.getElementById('knowledge-panel-header')?.addEventListener('click', () => {
  toggleKnowledgePanel();
});

document.getElementById('btn-toggle-connections')?.addEventListener('click', () => {
  const body = document.getElementById('knowledge-panel-body');
  if (body && body.style.display === 'none') {
    toggleKnowledgePanel();
  }
  document.getElementById('knowledge-panel')?.scrollIntoView({ behavior: 'smooth' });
});

document.addEventListener('click', (e) => {
  const dropdown = document.getElementById('wikilink-autocomplete');
  if (dropdown && !dropdown.classList.contains('hidden')) {
    if (!dropdown.contains(e.target) && e.target.id !== 'note-textarea') {
      dropdown.classList.add('hidden');
    }
  }
});

