// ─── ATOM Notes: Master Orchestrator ─────────────────────
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



// ─── Initialization ───────────────────────────────────────
async function init() {
  // Check if there is an imported note from Topics
  const importedNoteRaw = localStorage.getItem('atom_draft_imported_note');
  if (importedNoteRaw) {
    try {
      const draft = JSON.parse(importedNoteRaw);
      localStorage.removeItem('atom_draft_imported_note');
      const note = await createNote(draft.title || 'Catatan Berita', draft.content || '', draft.tags || ['intel', 'news']);
      await renderNotesList();
      await openNote(note.id, 'edit');
      showToast('Berita berhasil diimpor ke Crew Note! ✨', 'success');
      return;
    } catch (e) {
      console.warn('Failed to parse imported note:', e);
    }
  }

  // In Document & Gallery Mode, users land on the Knowledge Hub (Gallery View)
  // unless there is an imported draft note from Topics.
  await renderNotesList();
}

init();
