// ─── ATOM Notes: Editor, Modes & Auto-Save ──────────────
// ─── Render Notes Sidebar ─────────────────────────────────
async function renderNotesList(query = '') {
  const notesList = document.getElementById('notes-list');
  const statsEl   = document.getElementById('notes-stats');
  if (!notesList) return;

  const notes = await searchNotes(query);
  const allTags = await getAllTags();
  const allNotes = await getAllNotes();
  allNotesCache = allNotes;

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

  // Refresh knowledge connections & backlinks
  updateKnowledgeConnections(id);

  // Refresh multi-note chat context sources
  renderChatSourcesUI();
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
  let html = renderer(content);
  html = parseWikilinks(html, allNotesCache);
  viewEl.innerHTML = html;
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

    // Refresh knowledge graph & backlinks
    updateKnowledgeConnections(id);

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

