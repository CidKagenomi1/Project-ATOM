// ─── ATOM Notes: Editor, Modes & Auto-Save ──────────────
let currentActiveTag = '';

// Helper: Strip Markdown syntax for clean card snippet preview
function getSnippetPreview(content) {
  if (!content || !content.trim()) return '';
  return content
    .replace(/^#+\s+/gm, '') // headings
    .replace(/!\[.*?\]\(.*?\)/g, '') // images
    .replace(/\[\[(.*?)\]\]/g, '$1') // wikilinks
    .replace(/\[(.*?)\]\(.*?\)/g, '$1') // links
    .replace(/[*_`~>#]/g, '') // inline formatting
    .replace(/\n+/g, ' ')
    .trim();
}

// ─── Render Notes Gallery (Knowledge Hub Grid) ────────────
async function renderNotesGallery(query = '', filterTag = null) {
  const gridEl     = document.getElementById('notes-grid');
  const statsEl    = document.getElementById('gallery-stats-pill');
  const tagPillsEl = document.getElementById('gallery-tag-pills');
  if (!gridEl) return;

  if (filterTag !== null) {
    currentActiveTag = filterTag;
  }

  const allNotes = await getAllNotes();
  const allTags  = await getAllTags();
  allNotesCache  = allNotes;

  // Filter by search query
  let notes = query && query.trim() ? await searchNotes(query) : [...allNotes];

  // Filter by tag if selected
  if (currentActiveTag) {
    notes = notes.filter(n => Array.isArray(n.tags) && n.tags.includes(currentActiveTag));
  }

  // Update Stats Pill
  if (statsEl) {
    statsEl.textContent = `${allNotes.length} Catatan · ${allTags.length} Tag`;
  }

  // Render Tag Filter Chips
  if (tagPillsEl) {
    tagPillsEl.innerHTML = `
      <button class="tag-filter-chip ${!currentActiveTag ? 'active' : ''}" onclick="setTagFilter('')">
        Semua
      </button>
      ${allTags.map(tag => `
        <button class="tag-filter-chip ${currentActiveTag === tag ? 'active' : ''}" onclick="setTagFilter('${escapeHtml(tag)}')">
          #${escapeHtml(tag)}
        </button>
      `).join('')}
    `;
  }

  // Empty state check
  if (notes.length === 0) {
    gridEl.innerHTML = `
      <div class="gallery-empty-state">
        <div class="gallery-empty-icon">
          <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:1.8rem;height:1.8rem;opacity:0.6;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </div>
        <h3 style="margin:0;font-size:1.1rem;font-weight:600;color:var(--text-primary);letter-spacing:-0.01em;">
          ${query || currentActiveTag ? 'Tidak ada catatan yang cocok' : 'Belum ada catatan'}
        </h3>
        <p style="margin:0;font-size:0.84rem;color:var(--text-muted);max-width:340px;">
          ${query || currentActiveTag ? 'Coba gunakan kata kunci pencarian lain atau klik "Semua" pada filter tag.' : 'Mulai tuangkan ide, riset, atau notulensi pertama Anda sekarang.'}
        </p>
        <button class="btn btn-primary btn-sm" onclick="createNewNoteFlow()" style="margin-top:6px;">
          + Buat Catatan Baru
        </button>
      </div>
    `;
    return;
  }

  // New Note quick card
  const newCardHtml = (!query && !currentActiveTag) ? `
    <div class="note-card-new" onclick="createNewNoteFlow()" title="Klik untuk membuat catatan baru">
      <div class="note-card-new-icon">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:1.2rem;height:1.2rem;"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
      </div>
      <div>
        <div class="note-card-new-title">Catatan Baru</div>
        <div class="note-card-new-sub">Mulai menyusun ide baru</div>
      </div>
    </div>
  ` : '';

  const cardsHtml = notes.map(note => {
    const rawSnippet = getSnippetPreview(note.content);
    const snippet = rawSnippet ? escapeHtml(rawSnippet.slice(0, 140)) + (rawSnippet.length > 140 ? '...' : '') : '<span class="empty">Catatan ini masih kosong...</span>';
    const tags = Array.isArray(note.tags) ? note.tags : [];
    const wordCount = (note.content || '').split(/\s+/).filter(Boolean).length;
    
    let timeLabel = `${wordCount} kata`;
    if (note.updated_at) {
      try {
        const d = new Date(note.updated_at);
        timeLabel = d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
      } catch(e) {}
    }

    return `
      <div class="note-card" data-id="${note.id}" onclick="openNote(${note.id})">
        <div class="note-card-header">
          <div class="note-card-title-group">
            <span class="note-card-icon">
              <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:0.85rem;height:0.85rem;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            </span>
            <h3 class="note-card-title" title="${escapeHtml(note.title || 'Untitled Note')}">${escapeHtml(note.title || 'Untitled Note')}</h3>
          </div>
          <button class="note-card-delete-btn" onclick="confirmDeleteNote(event, ${note.id})" title="Hapus catatan" aria-label="Delete">
            <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:0.75rem;height:0.75rem;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
          </button>
        </div>
        <div class="note-card-body">
          <p class="note-card-snippet">${snippet}</p>
        </div>
        <div class="note-card-footer">
          <div class="note-card-tags">
            ${tags.slice(0, 3).map(t => `<span class="note-card-tag-pill">#${escapeHtml(t)}</span>`).join('')}
            ${tags.length > 3 ? `<span class="note-card-tag-pill">+${tags.length - 3}</span>` : ''}
          </div>
          <span class="note-card-meta">${timeLabel}</span>
        </div>
      </div>
    `;
  }).join('');

  gridEl.innerHTML = newCardHtml + cardsHtml;
}

window.setTagFilter = function(tag) {
  currentActiveTag = tag;
  const searchInput = document.getElementById('notes-search');
  renderNotesGallery(searchInput?.value || '', tag);
};

// Backwards-compatible alias for existing callers
window.renderNotesList = async function(query = '') {
  await renderNotesGallery(query, currentActiveTag);
};

// ─── Open Document View ────────────────────────────────────
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

  // Switch views: hide Gallery, show Document View
  const galleryView = document.getElementById('notes-gallery-view');
  const docView     = document.getElementById('notes-document-view');
  if (galleryView) {
    galleryView.style.display = 'none';
    galleryView.classList.add('hidden');
  }
  if (docView) {
    docView.style.display = 'flex';
    docView.classList.remove('hidden');
  }

  // Determine mode: if note is empty, open in edit mode for immediate typing!
  const hasContent = Boolean(note.content && note.content.trim().length > 0);
  const mode = targetMode || (hasContent ? 'view' : 'edit');
  setNoteMode(mode);

  setSaveStatus('Tersimpan ✓', 'var(--text-muted)');

  // Refresh knowledge connections & backlinks
  updateKnowledgeConnections(id);

  // Refresh multi-note chat context sources
  renderChatSourcesUI();
}
window.openNote = openNote;

// ─── Close Document View (Back to Gallery Hub) ─────────────
window.closeDocumentView = async function() {
  triggerAutoSave(true);
  const galleryView = document.getElementById('notes-gallery-view');
  const docView     = document.getElementById('notes-document-view');

  if (docView) {
    docView.style.display = 'none';
    docView.classList.add('hidden');
  }
  if (galleryView) {
    galleryView.style.display = 'flex';
    galleryView.classList.remove('hidden');
  }

  currentNoteId = null;
  const searchInput = document.getElementById('notes-search');
  await renderNotesGallery(searchInput?.value || '', currentActiveTag);
};

window.mobileCloseNote = window.closeDocumentView;

function renderMarkdownView(content) {
  const viewEl = document.getElementById('note-view-content');
  if (!viewEl) return;
  if (!content || !content.trim()) {
    viewEl.innerHTML = `
      <div style="padding:var(--space-8);text-align:center;color:var(--text-muted);border:1px dashed rgba(255,255,255,0.08);border-radius:var(--radius-lg);cursor:pointer;background:rgba(255,255,255,0.015);transition:all 0.2s;" onmouseenter="this.style.borderColor='rgba(255,255,255,0.2)'" onmouseleave="this.style.borderColor='rgba(255,255,255,0.08)'" onclick="setNoteMode('edit')" title="Klik untuk mulai menulis">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width:2rem;height:2rem;margin-bottom:8px;color:var(--text-muted);opacity:0.6;"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path></svg>
        <p style="font-size:0.95rem;font-weight:600;margin-bottom:4px;color:var(--text-primary);letter-spacing:-0.01em;">Catatan ini masih kosong</p>
        <p style="font-size:0.78rem;color:var(--text-muted);">Klik di sini atau beralih ke mode <strong>Edit</strong> untuk mulai menulis dalam Markdown.</p>
      </div>`;
    if (typeof rebuildScrollAnchors === 'function') rebuildScrollAnchors();
    return;
  }
  const renderer = window.renderMarkdown || marked.parse;
  let html = renderer(content);
  html = parseWikilinks(html, allNotesCache);
  viewEl.innerHTML = html;
  if (typeof rebuildScrollAnchors === 'function') rebuildScrollAnchors();
}

function renderTagsDisplay(tags) {
  const tagsDisplay = document.getElementById('tags-display');
  if (!tagsDisplay) return;
  if (!Array.isArray(tags) || tags.length === 0) {
    tagsDisplay.innerHTML = '<span class="tag-chip empty-tag-hint" onclick="setNoteMode(\'edit\')" title="Tambah tag">+ tag</span>';
    return;
  }
  tagsDisplay.innerHTML = tags.map(t => `<span class="tag" title="Tag: ${escapeHtml(t)}">#${escapeHtml(t)}</span>`).join(' ');
}

// ─── Note Mode Switching (Baca | Edit | Split | Co-Pilot) ───
window.setNoteMode = function(mode) {
  const noteBody    = document.getElementById('note-body');
  const viewContent = document.getElementById('note-view-content');
  const editContent = document.getElementById('note-edit-content');
  const chatContent = document.getElementById('note-chat-content');
  const tagsInput   = document.getElementById('tags-input');
  const ta          = document.getElementById('note-textarea');

  // If entering view or split, make sure markdown is rendered fresh
  if (mode === 'view' || mode === 'split') {
    renderMarkdownView(ta?.value || '');
  }

  currentNoteMode = mode;

  // Single unified segmented control: Baca | Edit | Split | Co-Pilot
  ['view', 'edit', 'split', 'chat'].forEach(m => {
    const btn = document.getElementById(`mode-${m}-btn`);
    if (btn) btn.classList.toggle('active', m === mode);
  });

  const tagsBar   = document.getElementById('tags-bar');
  const isMobile  = window.innerWidth <= 768;

  // Keep tags bar clean: show text input only in edit or split mode
  if (tagsInput) {
    tagsInput.style.display = (mode === 'edit' || mode === 'split') ? 'inline-block' : 'none';
  }

  // Tags bar on mobile hidden in chat mode for maximum vertical space; on desktop keeps flex
  if (tagsBar) {
    tagsBar.style.display = (mode === 'chat' && isMobile) ? 'none' : 'flex';
  }

  // Adjust canvas layout & display
  if (mode === 'chat') {
    if (viewContent) {
      viewContent.style.display = isMobile ? 'none' : 'block';
      renderMarkdownView(ta?.value || '');
    }
    if (editContent) editContent.style.display = 'none';
    if (chatContent) chatContent.style.display = 'flex';
    if (noteBody) {
      noteBody.classList.remove('mode-view', 'mode-edit', 'mode-split');
      noteBody.classList.add('mode-chat');
    }
    setTimeout(() => {
      const chatInput = document.getElementById('note-chat-input');
      chatInput?.focus();
    }, 40);
  } else if (mode === 'split') {
    if (chatContent) chatContent.style.display = 'none';
    if (editContent) editContent.style.display = 'flex';
    if (viewContent) viewContent.style.display = 'block';
    if (noteBody) {
      noteBody.classList.remove('mode-view', 'mode-edit');
      noteBody.classList.add('mode-split');
    }
    // Rebuild anchors and align initial scroll position accurately
    setTimeout(() => {
      rebuildScrollAnchors();
      if (ta && viewContent) {
        viewContent.scrollTop = getPreviewScrollFromEditor(ta.scrollTop);
      }
    }, 40);
  } else if (mode === 'edit') {
    if (chatContent) chatContent.style.display = 'none';
    if (viewContent) viewContent.style.display = 'none';
    if (editContent) editContent.style.display = 'block';
    if (noteBody) {
      noteBody.classList.remove('mode-view', 'mode-split');
      noteBody.classList.add('mode-edit');
    }
    // Auto-focus textarea when entering edit mode
    if (ta && document.activeElement !== ta && document.activeElement !== document.getElementById('note-title-input')) {
      ta.focus();
    }
  } else { // 'view'
    if (chatContent) chatContent.style.display = 'none';
    if (editContent) editContent.style.display = 'none';
    if (viewContent) viewContent.style.display = 'block';
    if (noteBody) {
      noteBody.classList.remove('mode-edit', 'mode-split');
      noteBody.classList.add('mode-view');
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

    // Refresh knowledge graph & backlinks
    updateKnowledgeConnections(id);

    if (isExplicitSave) {
      renderMarkdownView(content);
      showToast('Crew Note tersimpan! ✅', 'success');
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

// Input listeners for Auto-Save & Split Mode Live Preview
let splitRenderDebounce = null;
document.getElementById('note-title-input')?.addEventListener('input', () => triggerAutoSave());
document.getElementById('note-textarea')?.addEventListener('input', () => {
  triggerAutoSave();
  if (currentNoteMode === 'split') {
    clearTimeout(splitRenderDebounce);
    splitRenderDebounce = setTimeout(() => {
      const ta = document.getElementById('note-textarea');
      const view = document.getElementById('note-view-content');
      if (ta) {
        renderMarkdownView(ta.value);
        if (view) {
          view.scrollTop = getPreviewScrollFromEditor(ta.scrollTop);
        }
      }
    }, 80);
  }
});
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

// ─── Delete Note ─────────────────────────────────────────
window.confirmDeleteNote = async function(e, id) {
  if (e && e.stopPropagation) e.stopPropagation();
  if (!confirm('Hapus Crew Note ini?')) return;

  const success = await deleteNote(id);
  if (success) {
    if (currentNoteId === id) {
      await closeDocumentView();
    } else {
      await renderNotesGallery(document.getElementById('notes-search')?.value || '', currentActiveTag);
    }
    showToast('Crew Note dihapus 🗑', 'info');
  } else {
    showToast('Gagal menghapus note', 'error');
  }
};

document.getElementById('btn-delete-note')?.addEventListener('click', () => {
  if (!currentNoteId) return;
  confirmDeleteNote({ stopPropagation: () => {} }, currentNoteId);
});

// ─── New Note Flow ─────────────────────────────────────────
window.createNewNoteFlow = async function() {
  const btn = document.getElementById('btn-new-note');
  if (btn) btn.disabled = true;

  try {
    const note = await createNote('Catatan Baru', '', []);
    await renderNotesGallery();
    await openNote(note.id, 'edit');
    const titleInput = document.getElementById('note-title-input');
    if (titleInput) {
      titleInput.focus();
      titleInput.select();
    }
    showToast('Crew Note baru siap diedit! ✨', 'success');
  } catch (err) {
    showToast('Gagal membuat note: ' + err.message, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
};

document.getElementById('btn-new-note')?.addEventListener('click', createNewNoteFlow);

// ─── Search Notes & Clear Button ──────────────────────────
const notesSearchInput = document.getElementById('notes-search');
const btnClearSearch   = document.getElementById('btn-clear-search');

notesSearchInput?.addEventListener('input', async (e) => {
  const query = e.target.value;
  if (btnClearSearch) {
    btnClearSearch.classList.toggle('hidden', !query.trim());
  }
  await renderNotesGallery(query, currentActiveTag);
});

btnClearSearch?.addEventListener('click', async () => {
  if (notesSearchInput) {
    notesSearchInput.value = '';
    notesSearchInput.focus();
  }
  btnClearSearch.classList.add('hidden');
  await renderNotesGallery('', currentActiveTag);
});

// ─── Quick Switcher (Ctrl+K Command Palette) ──────────────
let quickSwitcherActiveIndex = 0;
let quickSwitcherFilteredNotes = [];

window.openQuickSwitcher = async function() {
  const modal = document.getElementById('quick-switcher-modal');
  const input = document.getElementById('quick-switcher-input');
  if (!modal || !input) return;

  const notes = await getAllNotes();
  allNotesCache = notes;
  quickSwitcherFilteredNotes = notes;
  quickSwitcherActiveIndex = 0;

  modal.classList.remove('hidden');
  input.value = '';
  renderQuickSwitcherResults('');
  setTimeout(() => input.focus(), 30);
};

window.closeQuickSwitcher = function() {
  const modal = document.getElementById('quick-switcher-modal');
  if (modal) modal.classList.add('hidden');
};

document.getElementById('btn-close-quick-switcher')?.addEventListener('click', closeQuickSwitcher);

function renderQuickSwitcherResults(query = '') {
  const container = document.getElementById('quick-switcher-results');
  if (!container) return;

  const q = query.trim().toLowerCase();
  const filtered = q
    ? allNotesCache.filter(n => (n.title || '').toLowerCase().includes(q) || (n.content || '').toLowerCase().includes(q))
    : allNotesCache;

  quickSwitcherFilteredNotes = filtered;

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="padding:20px;text-align:center;color:var(--text-muted);font-size:0.82rem;">
        Tidak ada catatan yang cocok dengan "<strong>${escapeHtml(query)}</strong>"<br>
        <span style="font-size:0.75rem;margin-top:6px;display:inline-block;color:var(--text-secondary);">Tekan <strong>Enter</strong> untuk membuat catatan baru dengan judul ini.</span>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map((note, idx) => `
    <div class="quick-switcher-item ${idx === quickSwitcherActiveIndex ? 'selected' : ''}" onclick="selectQuickSwitcherNote(${note.id})">
      <div class="quick-switcher-item-left">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:0.85rem;height:0.85rem;color:var(--text-muted);"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        <span class="quick-switcher-item-title">${escapeHtml(note.title || 'Untitled Note')}</span>
      </div>
      <span class="quick-switcher-item-tags">${Array.isArray(note.tags) && note.tags.length ? '#' + escapeHtml(note.tags[0]) : ''}</span>
    </div>
  `).join('');
}

window.selectQuickSwitcherNote = async function(id) {
  closeQuickSwitcher();
  await openNote(id);
};

const quickSwitcherInput = document.getElementById('quick-switcher-input');
quickSwitcherInput?.addEventListener('input', (e) => {
  quickSwitcherActiveIndex = 0;
  renderQuickSwitcherResults(e.target.value);
});

quickSwitcherInput?.addEventListener('keydown', async (e) => {
  const container = document.getElementById('quick-switcher-results');
  const items = container?.querySelectorAll('.quick-switcher-item') || [];

  if (e.key === 'ArrowDown') {
    e.preventDefault();
    if (quickSwitcherFilteredNotes.length > 0) {
      quickSwitcherActiveIndex = (quickSwitcherActiveIndex + 1) % quickSwitcherFilteredNotes.length;
      items.forEach((el, idx) => el.classList.toggle('selected', idx === quickSwitcherActiveIndex));
      items[quickSwitcherActiveIndex]?.scrollIntoView({ block: 'nearest' });
    }
    return;
  }

  if (e.key === 'ArrowUp') {
    e.preventDefault();
    if (quickSwitcherFilteredNotes.length > 0) {
      quickSwitcherActiveIndex = (quickSwitcherActiveIndex - 1 + quickSwitcherFilteredNotes.length) % quickSwitcherFilteredNotes.length;
      items.forEach((el, idx) => el.classList.toggle('selected', idx === quickSwitcherActiveIndex));
      items[quickSwitcherActiveIndex]?.scrollIntoView({ block: 'nearest' });
    }
    return;
  }

  if (e.key === 'Enter') {
    e.preventDefault();
    if (quickSwitcherFilteredNotes.length > 0 && quickSwitcherFilteredNotes[quickSwitcherActiveIndex]) {
      const target = quickSwitcherFilteredNotes[quickSwitcherActiveIndex];
      await selectQuickSwitcherNote(target.id);
    } else if (quickSwitcherInput.value.trim()) {
      // Create new note with this title!
      const newTitle = quickSwitcherInput.value.trim();
      closeQuickSwitcher();
      const newNote = await createNote(newTitle, '', []);
      await renderNotesGallery();
      await openNote(newNote.id, 'edit');
      showToast(`Catatan "${newTitle}" berhasil dibuat! ✨`, 'success');
    }
    return;
  }

  if (e.key === 'Escape') {
    e.preventDefault();
    closeQuickSwitcher();
    return;
  }
});

// Global Shortcuts (Ctrl+K & Escape)
window.addEventListener('keydown', (e) => {
  // Ctrl+K or Cmd+K: Open Quick Switcher
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    const modal = document.getElementById('quick-switcher-modal');
    if (modal && !modal.classList.contains('hidden')) {
      closeQuickSwitcher();
    } else {
      openQuickSwitcher();
    }
    return;
  }

  // Escape: Close modals or return to Gallery if inside Document View
  if (e.key === 'Escape') {
    const qsModal = document.getElementById('quick-switcher-modal');
    if (qsModal && !qsModal.classList.contains('hidden')) {
      closeQuickSwitcher();
      return;
    }
    const docView = document.getElementById('notes-document-view');
    const isDocActive = docView && docView.style.display !== 'none' && !docView.classList.contains('hidden');
    const activeEl = document.activeElement;
    const isTyping = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA');

    if (isDocActive && !isTyping) {
      closeDocumentView();
    }
  }
});



// ─── Tab key & Wikilink Keyboard Navigation ─────────────
document.getElementById('note-textarea')?.addEventListener('keydown', (e) => {
  const dropdown = document.getElementById('wikilink-autocomplete');
  const isDropdownActive = dropdown && !dropdown.classList.contains('hidden');

  if (isDropdownActive) {
    const totalOptions = filteredWikilinkNotes.length + (currentWikilinkQuery ? 1 : 0);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (totalOptions > 0) {
        activeAutocompleteIndex = (activeAutocompleteIndex + 1) % totalOptions;
        renderWikilinkDropdown(currentWikilinkQuery);
      }
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (totalOptions > 0) {
        activeAutocompleteIndex = (activeAutocompleteIndex - 1 + totalOptions) % totalOptions;
        renderWikilinkDropdown(currentWikilinkQuery);
      }
      return;
    }
    if (e.key === 'Enter' || e.key === 'Tab') {
      if (totalOptions > 0) {
        e.preventDefault();
        if (activeAutocompleteIndex < filteredWikilinkNotes.length) {
          const selected = filteredWikilinkNotes[activeAutocompleteIndex];
          if (selected) {
            selectWikilinkNote(selected.title);
            return;
          }
        } else if (currentWikilinkQuery) {
          selectWikilinkNote(currentWikilinkQuery);
          return;
        }
      }
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      dropdown.classList.add('hidden');
      return;
    }
  }

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

// ─── Anchor-Based Two-Way Synchronous Scrolling for Split Mode ───
let isSyncingEditorScroll = false;
let isSyncingPreviewScroll = false;
let syncScrollTimer = null;
let scrollAnchors = [];

function rebuildScrollAnchors() {
  const textarea = document.getElementById('note-textarea');
  const preview = document.getElementById('note-view-content');
  if (!textarea || !preview || currentNoteMode !== 'split') {
    scrollAnchors = [];
    return;
  }

  const text = textarea.value;
  if (!text.trim()) {
    scrollAnchors = [];
    return;
  }

  const lines = text.split('\n');
  const totalLines = lines.length;
  const linePixelHeight = textarea.scrollHeight / Math.max(totalLines, 1);

  // Target semua heading dan elemen blok di preview
  const blockElements = preview.querySelectorAll('h1, h2, h3, h4, h5, h6, p, ul, ol, blockquote, pre, table');
  const anchors = [];

  // Selalu ada anchor awal (0, 0)
  anchors.push({ editorTop: 0, previewTop: 0 });

  blockElements.forEach(el => {
    const rawSnippet = el.textContent.trim().replace(/\s+/g, ' ');
    if (rawSnippet.length < 5) return;
    const snippet = rawSnippet.slice(0, 32);

    const charIndex = text.indexOf(snippet);
    if (charIndex !== -1) {
      const lineNum = text.slice(0, charIndex).split('\n').length - 1;
      const editorTop = lineNum * linePixelHeight;
      const previewTop = el.offsetTop - preview.offsetTop;
      anchors.push({ editorTop, previewTop });
    }
  });

  anchors.sort((a, b) => a.editorTop - b.editorTop);

  const cleanAnchors = [];
  let lastEditorTop = -1;
  let lastPreviewTop = -1;
  for (const a of anchors) {
    if (a.editorTop > lastEditorTop && a.previewTop >= lastPreviewTop) {
      cleanAnchors.push(a);
      lastEditorTop = a.editorTop;
      lastPreviewTop = a.previewTop;
    }
  }

  const maxEditor = Math.max(textarea.scrollHeight - textarea.clientHeight, 0);
  const maxPreview = Math.max(preview.scrollHeight - preview.clientHeight, 0);
  if (cleanAnchors.length > 0) {
    const last = cleanAnchors[cleanAnchors.length - 1];
    if (last.editorTop < maxEditor || last.previewTop < maxPreview) {
      cleanAnchors.push({ editorTop: maxEditor, previewTop: maxPreview });
    }
  } else {
    cleanAnchors.push({ editorTop: maxEditor, previewTop: maxPreview });
  }

  scrollAnchors = cleanAnchors;
}

function getPreviewScrollFromEditor(editorScrollTop) {
  const textarea = document.getElementById('note-textarea');
  const preview = document.getElementById('note-view-content');
  if (!scrollAnchors || scrollAnchors.length < 2) {
    const maxTa = (textarea?.scrollHeight || 1) - (textarea?.clientHeight || 0);
    const maxView = (preview?.scrollHeight || 1) - (preview?.clientHeight || 0);
    return maxTa > 0 ? (editorScrollTop / maxTa) * maxView : 0;
  }

  if (editorScrollTop <= scrollAnchors[0].editorTop) {
    return scrollAnchors[0].previewTop;
  }

  const last = scrollAnchors[scrollAnchors.length - 1];
  if (editorScrollTop >= last.editorTop) {
    return last.previewTop;
  }

  for (let i = 0; i < scrollAnchors.length - 1; i++) {
    const a1 = scrollAnchors[i];
    const a2 = scrollAnchors[i + 1];
    if (editorScrollTop >= a1.editorTop && editorScrollTop <= a2.editorTop) {
      const spanEditor = a2.editorTop - a1.editorTop;
      if (spanEditor <= 0) return a1.previewTop;
      const t = (editorScrollTop - a1.editorTop) / spanEditor;
      return a1.previewTop + t * (a2.previewTop - a1.previewTop);
    }
  }

  return last.previewTop;
}

function getEditorScrollFromPreview(previewScrollTop) {
  const textarea = document.getElementById('note-textarea');
  const preview = document.getElementById('note-view-content');
  if (!scrollAnchors || scrollAnchors.length < 2) {
    const maxTa = (textarea?.scrollHeight || 1) - (textarea?.clientHeight || 0);
    const maxView = (preview?.scrollHeight || 1) - (preview?.clientHeight || 0);
    return maxView > 0 ? (previewScrollTop / maxView) * maxTa : 0;
  }

  if (previewScrollTop <= scrollAnchors[0].previewTop) {
    return scrollAnchors[0].editorTop;
  }

  const last = scrollAnchors[scrollAnchors.length - 1];
  if (previewScrollTop >= last.previewTop) {
    return last.editorTop;
  }

  for (let i = 0; i < scrollAnchors.length - 1; i++) {
    const a1 = scrollAnchors[i];
    const a2 = scrollAnchors[i + 1];
    if (previewScrollTop >= a1.previewTop && previewScrollTop <= a2.previewTop) {
      const spanPreview = a2.previewTop - a1.previewTop;
      if (spanPreview <= 0) return a1.editorTop;
      const t = (previewScrollTop - a1.previewTop) / spanPreview;
      return a1.editorTop + t * (a2.editorTop - a1.editorTop);
    }
  }

  return last.editorTop;
}

function setupSplitSyncScroll() {
  const textarea = document.getElementById('note-textarea');
  const preview = document.getElementById('note-view-content');
  if (!textarea || !preview) return;

  // Textarea (Editor) -> Markdown Preview
  textarea.addEventListener('scroll', () => {
    if (currentNoteMode !== 'split') return;
    if (isSyncingPreviewScroll) return;

    isSyncingEditorScroll = true;
    preview.scrollTop = getPreviewScrollFromEditor(textarea.scrollTop);

    clearTimeout(syncScrollTimer);
    syncScrollTimer = setTimeout(() => {
      isSyncingEditorScroll = false;
    }, 45);
  }, { passive: true });

  // Markdown Preview -> Textarea (Editor)
  preview.addEventListener('scroll', () => {
    if (currentNoteMode !== 'split') return;
    if (isSyncingEditorScroll) return;

    isSyncingPreviewScroll = true;
    textarea.scrollTop = getEditorScrollFromPreview(preview.scrollTop);

    clearTimeout(syncScrollTimer);
    syncScrollTimer = setTimeout(() => {
      isSyncingPreviewScroll = false;
    }, 45);
  }, { passive: true });

  window.addEventListener('resize', () => {
    if (currentNoteMode === 'split') {
      rebuildScrollAnchors();
    } else if (currentNoteMode === 'chat') {
      const viewContent = document.getElementById('note-view-content');
      if (viewContent) {
        viewContent.style.display = (window.innerWidth <= 768) ? 'none' : 'block';
      }
    }
  });
}

// Initialize synchronized scrolling
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setupSplitSyncScroll();
  });
} else {
  setupSplitSyncScroll();
}

