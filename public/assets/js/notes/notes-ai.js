// ─── ATOM Notes: AI Refine, Multi-Note Chat & Micro AI ──
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

// ─── Safe AI Refine State & Logic ─────────────────────────
let safeRefineOriginalText = '';
let safeRefineResultText   = '';
let currentRefineStyle     = 'structured';
let currentRefineView      = 'split';

function countWords(str) {
  if (!str) return 0;
  return str.trim().split(/\s+/).filter(Boolean).length;
}

function openSafeRefineModal() {
  const textarea = document.getElementById('note-textarea');
  const content  = textarea?.value || '';
  if (!content.trim()) {
    showToast('Tulis isi catatan terlebih dahulu sebelum merapikan', 'warning');
    return;
  }

  safeRefineOriginalText = content;
  safeRefineResultText   = '';
  currentRefineStyle     = 'structured';
  currentRefineView      = 'split';

  const modal      = document.getElementById('safe-refine-modal');
  const origBox    = document.getElementById('refine-original-text');
  const origStat   = document.getElementById('refine-stat-original');
  const resultStat = document.getElementById('refine-stat-result');
  const diffBadge  = document.getElementById('refine-diff-badge');
  const rawEl      = document.getElementById('refine-result-raw');
  const previewEl  = document.getElementById('refine-result-preview');

  if (origBox) origBox.textContent = content;
  if (origStat) origStat.textContent = `${countWords(content)} kata`;
  if (resultStat) resultStat.textContent = '0 kata';
  if (diffBadge) {
    diffBadge.textContent = '0%';
    diffBadge.className = 'refine-diff-badge';
  }
  if (rawEl) rawEl.value = '';
  if (previewEl) previewEl.innerHTML = '';

  // Reset preset chips
  document.querySelectorAll('.safe-refine-presets .preset-chip').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.style === 'structured');
  });

  // Reset view buttons
  updateSafeRefineViewUI('split');

  if (modal) modal.classList.remove('hidden');

  // Trigger initial AI generation
  runSafeRefineAI();
}

function closeSafeRefineModal() {
  const modal = document.getElementById('safe-refine-modal');
  if (modal) modal.classList.add('hidden');
}

async function runSafeRefineAI() {
  const loadingEl  = document.getElementById('refine-loading');
  const previewEl  = document.getElementById('refine-result-preview');
  const rawEl      = document.getElementById('refine-result-raw');
  const regenBtn   = document.getElementById('btn-refine-regen');
  const applyBtn   = document.getElementById('btn-refine-apply');
  const resultStat = document.getElementById('refine-stat-result');
  const diffBadge  = document.getElementById('refine-diff-badge');

  if (loadingEl) loadingEl.style.display = 'flex';
  if (regenBtn) regenBtn.disabled = true;
  if (applyBtn) applyBtn.disabled = true;

  try {
    const result = await callNotesAI('refine', {
      content: safeRefineOriginalText,
      style: currentRefineStyle
    });

    if (result && !String(result).startsWith('[ERROR]')) {
      safeRefineResultText = result;
      if (previewEl) {
        previewEl.innerHTML = typeof marked !== 'undefined' ? marked.parse(result) : escapeHtml(result);
      }
      if (rawEl) rawEl.value = result;

      // Calculate stats
      const origCount = countWords(safeRefineOriginalText);
      const resCount  = countWords(result);
      if (resultStat) resultStat.textContent = `${resCount} kata`;

      if (diffBadge) {
        if (origCount > 0) {
          const diffPct = Math.round(((resCount - origCount) / origCount) * 100);
          diffBadge.textContent = `${diffPct >= 0 ? '+' : ''}${diffPct}%`;
          diffBadge.className = `refine-diff-badge ${diffPct < 0 ? 'neg' : ''}`;
        } else {
          diffBadge.textContent = '+100%';
          diffBadge.className = 'refine-diff-badge';
        }
      }

      if (applyBtn) applyBtn.disabled = false;
    } else {
      throw new Error(result || 'Tidak ada respons dari AI.');
    }
  } catch (err) {
    console.error('[SAFE REFINE ERROR]', err);
    showToast(`Gagal merapihkan teks: ${err.message}`, 'error');
    if (previewEl) {
      previewEl.innerHTML = `<div style="color:#ef4444;padding:var(--space-4);background:rgba(239,68,68,0.1);border-radius:var(--radius-md);border:1px solid rgba(239,68,68,0.3);">⚠️ Terjadi kesalahan: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (loadingEl) loadingEl.style.display = 'none';
    if (regenBtn) regenBtn.disabled = false;
  }
}

function updateSafeRefineViewUI(mode) {
  currentRefineView = mode;
  const colOrig   = document.getElementById('refine-col-original');
  const colResult = document.getElementById('refine-col-result');
  const previewEl = document.getElementById('refine-result-preview');
  const rawEl     = document.getElementById('refine-result-raw');

  document.querySelectorAll('.safe-refine-view-toggles .view-chip').forEach(btn => {
    btn.classList.toggle('active', btn.id === `btn-view-${mode}`);
  });

  if (mode === 'split') {
    if (colOrig) colOrig.style.display = 'flex';
    if (colResult) colResult.style.display = 'flex';
    if (previewEl) previewEl.style.display = 'block';
    if (rawEl) rawEl.style.display = 'none';
  } else if (mode === 'preview') {
    if (colOrig) colOrig.style.display = 'none';
    if (colResult) colResult.style.display = 'flex';
    if (previewEl) previewEl.style.display = 'block';
    if (rawEl) rawEl.style.display = 'none';
  } else if (mode === 'raw') {
    if (colOrig) colOrig.style.display = 'none';
    if (colResult) colResult.style.display = 'flex';
    if (previewEl) previewEl.style.display = 'none';
    if (rawEl) rawEl.style.display = 'block';
  }
}

function applySafeRefineChanges() {
  const rawEl = document.getElementById('refine-result-raw');
  // allow edits in raw view if user tweaked it
  const finalContent = (currentRefineView === 'raw' && rawEl?.value) ? rawEl.value : safeRefineResultText;

  if (!finalContent?.trim()) {
    showToast('Belum ada teks hasil AI untuk diterapkan', 'warning');
    return;
  }

  const textarea = document.getElementById('note-textarea');
  if (textarea) {
    textarea.value = finalContent;
  }

  // Update view mode display if note rendered
  const viewContent = document.getElementById('note-view-content');
  if (viewContent && typeof marked !== 'undefined') {
    viewContent.innerHTML = marked.parse(finalContent);
  }

  triggerAutoSave(true);
  closeSafeRefineModal();
  showToast('Perubahan AI berhasil diterapkan ke catatan! ✨', 'success');
}

// Bind Safe Refine Events
document.getElementById('btn-refine')?.addEventListener('click', openSafeRefineModal);
document.getElementById('btn-close-refine-modal')?.addEventListener('click', closeSafeRefineModal);
document.getElementById('btn-refine-cancel')?.addEventListener('click', closeSafeRefineModal);
document.getElementById('btn-refine-apply')?.addEventListener('click', applySafeRefineChanges);
document.getElementById('btn-refine-regen')?.addEventListener('click', runSafeRefineAI);

document.querySelectorAll('.safe-refine-presets .preset-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.safe-refine-presets .preset-chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentRefineStyle = btn.dataset.style || 'structured';
    runSafeRefineAI();
  });
});

document.getElementById('btn-view-split')?.addEventListener('click', () => updateSafeRefineViewUI('split'));
document.getElementById('btn-view-preview')?.addEventListener('click', () => updateSafeRefineViewUI('preview'));
document.getElementById('btn-view-raw')?.addEventListener('click', () => updateSafeRefineViewUI('raw'));

// Listen for Escape key to close modal safely
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const modal = document.getElementById('safe-refine-modal');
    if (modal && !modal.classList.contains('hidden')) {
      closeSafeRefineModal();
    }
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

// ─── Multi-Note Context Note Chat (NotebookLM Style) ─────
let selectedChatSourceIds = new Set();
let tempSourcesSelection  = new Set();

function formatCitations(text) {
  if (!text) return '';
  return text.replace(/\[Sumber:\s*(.*?)\]/gi, (match, docTitle) => {
    return `<span class="source-citation" title="Dokumen Rujukan">📌 ${escapeHtml(docTitle.trim())}</span>`;
  });
}

let isCopilotGenerating = false;

function renderNoteChatMessages() {
  const msgArea = document.getElementById('note-chat-messages');
  if (!msgArea) return;

  if (noteChatHistory.length === 0 && !isCopilotGenerating) {
    msgArea.innerHTML = `
      <div class="copilot-empty-state">
        <div class="copilot-empty-icon">
          <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:1.6rem;height:1.6rem;"><circle cx="12" cy="12" r="3"></circle><ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(30 12 12)"></ellipse><ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(90 12 12)"></ellipse><ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(150 12 12)"></ellipse></svg>
        </div>
        <h2 class="copilot-empty-title">Knowledge Co-Pilot Studio</h2>
        <p class="copilot-empty-desc">Tanyakan wawasan tersembunyi, analisis benang merah, atau minta sintesis menyeluruh dari dokumen catatan Anda.</p>
        
        <div class="copilot-starters-grid">
          <div class="starter-card" onclick="sendStarterPrompt('Buat ringkasan eksekutif komprehensif yang mensintesis seluruh catatan terpilih menjadi satu kesimpulan utuh.')">
            <span class="starter-card-icon">📑</span>
            <div>
              <div class="starter-card-title">Sintesis Eksekutif</div>
              <div class="starter-card-desc">Rangkum inti pemikiran dokumen menjadi kesimpulan padat</div>
            </div>
          </div>
          <div class="starter-card" onclick="sendStarterPrompt('Bandingkan poin-poin utama, kesamaan, dan perbedaan antara catatan-catatan yang dipilih ini.')">
            <span class="starter-card-icon">⚖️</span>
            <div>
              <div class="starter-card-title">Bandingkan Konsep</div>
              <div class="starter-card-desc">Cari benang merah, kesamaan, dan kontradiksi ide</div>
            </div>
          </div>
          <div class="starter-card" onclick="sendStarterPrompt('Ekstrak semua action items, to-do list, dan rencana tindakan konkret dari catatan ini.')">
            <span class="starter-card-icon">✅</span>
            <div>
              <div class="starter-card-title">Ekstrak Action Items</div>
              <div class="starter-card-desc">Ubah catatan menjadi checklist langkah tindak lanjut</div>
            </div>
          </div>
          <div class="starter-card" onclick="sendStarterPrompt('Apa benang merah, korelasi ide, dan wawasan terpenting yang menghubungkan catatan-catatan ini?')">
            <span class="starter-card-icon">💡</span>
            <div>
              <div class="starter-card-title">Analisis Benang Merah</div>
              <div class="starter-card-desc">Temukan korelasi dan peluang ide baru yang tersembunyi</div>
            </div>
          </div>
        </div>
      </div>
    `;
    return;
  }

  const renderer = window.renderMarkdown || marked.parse;
  let html = noteChatHistory.map((m, idx) => {
    if (m.role === 'user') {
      return `
        <div class="chat-message-item chat-user">
          <div class="chat-message-content">${escapeHtml(m.content)}</div>
        </div>
      `;
    } else {
      let rendered = renderer(m.content);
      rendered = formatCitations(rendered);
      return `
        <div class="chat-message-item chat-ai">
          <div class="chat-ai-header">
            <div class="chat-ai-identity">
              <span class="chat-ai-avatar">✨</span>
              <span class="chat-ai-name">Cortex Knowledge AI</span>
              <span class="chat-ai-badge">Sintesis Dokumen</span>
            </div>
          </div>
          <div class="chat-message-content">${rendered}</div>
          <div class="chat-ai-actions">
            <button class="chat-action-btn" onclick="copyCopilotResponse(${idx})" title="Salin jawaban ini">
              <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:0.75rem;height:0.75rem;"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"></rect><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path></svg>
              <span>Salin</span>
            </button>
            <button class="chat-action-btn" onclick="insertCopilotResponseToNote(${idx})" title="Sisipkan jawaban ini ke dalam catatan aktif">
              <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:0.75rem;height:0.75rem;"><path d="M12 5v14M19 12l-7 7-7-7"></path></svg>
              <span>Sisipkan ke Catatan</span>
            </button>
          </div>
        </div>
      `;
    }
  }).join('');

  if (isCopilotGenerating) {
    html += `
      <div class="chat-message-item chat-ai" style="padding:14px 18px;width:fit-content;">
        <div class="chat-thinking-bubble">
          <span class="thinking-dot"></span>
          <span class="thinking-dot"></span>
          <span class="thinking-dot"></span>
          <span class="thinking-text">Cortex AI sedang menganalisis dokumen...</span>
        </div>
      </div>
    `;
  }

  msgArea.innerHTML = html;
  msgArea.scrollTop = msgArea.scrollHeight;
}

window.sendStarterPrompt = function(promptText) {
  const input = document.getElementById('note-chat-input');
  if (input) {
    input.value = promptText;
    sendNoteChatMessage();
  }
};

window.copyCopilotResponse = function(idx) {
  const item = noteChatHistory[idx];
  if (item && item.content) {
    navigator.clipboard.writeText(item.content);
    showToast('Jawaban AI disalin ke clipboard! 📋', 'success');
  }
};

window.insertCopilotResponseToNote = async function(idx) {
  const item = noteChatHistory[idx];
  if (!item || !item.content || !currentNoteId) {
    showToast('Tidak ada catatan aktif untuk disisipkan', 'warning');
    return;
  }
  const textarea = document.getElementById('note-textarea');
  if (textarea) {
    const currentVal = textarea.value || '';
    const addition = `\n\n---\n### 💡 Ringkasan Co-Pilot\n${item.content}\n`;
    textarea.value = currentVal.trim() + addition;
    triggerAutoSave(true);
    showToast('Jawaban Co-Pilot berhasil disisipkan ke catatan! 📥', 'success');
  }
};

function renderChatSourcesUI() {
  if (selectedChatSourceIds.size === 0 && currentNoteId) {
    selectedChatSourceIds.add(currentNoteId);
  }

  const summaryEl = document.getElementById('chat-sources-summary');
  const pillsContainer = document.getElementById('chat-sources-pills');
  if (!summaryEl) return;

  const selectedNotes = allNotesCache.filter(n => selectedChatSourceIds.has(n.id));
  let totalWords = 0;
  selectedNotes.forEach(n => {
    const text = (n.id === currentNoteId)
      ? (document.getElementById('note-textarea')?.value || n.content || '')
      : (n.content || '');
    totalWords += countWords(text);
  });

  const count = selectedNotes.length;
  if (count === 0) {
    summaryEl.textContent = `0 Catatan (Pilih Konteks)`;
  } else if (count === 1) {
    const noteTitle = selectedNotes[0]?.title || 'Catatan Aktif';
    const shortTitle = noteTitle.length > 22 ? noteTitle.substring(0, 20) + '...' : noteTitle;
    summaryEl.textContent = `${shortTitle} (~${totalWords} kata)`;
  } else {
    summaryEl.textContent = `${count} Catatan Terpilih (~${totalWords} kata)`;
  }

  if (pillsContainer) {
    if (selectedNotes.length === 0) {
      pillsContainer.innerHTML = `<span style="font-size:0.72rem;color:#ef4444;">⚠️ Belum ada catatan yang dipilih sebagai sumber.</span>`;
      return;
    }

    pillsContainer.innerHTML = selectedNotes.map(n => `
      <span class="source-pill" title="${escapeHtml(n.title)}">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:0.75rem;height:0.75rem;color:var(--gold-primary);flex-shrink:0;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        <span>${escapeHtml(n.title || 'Untitled')}</span>
        ${selectedNotes.length > 1 ? `<span class="source-pill-remove" onclick="removeChatSource(${n.id})" title="Hapus dari konteks">✕</span>` : ''}
      </span>
    `).join('');
  }
}

window.removeChatSource = function(id) {
  if (selectedChatSourceIds.size <= 1) {
    showToast('Minimal harus ada 1 catatan sebagai sumber konteks', 'warning');
    return;
  }
  selectedChatSourceIds.delete(id);
  renderChatSourcesUI();
};

function openSourcesModal() {
  tempSourcesSelection = new Set(selectedChatSourceIds);
  if (tempSourcesSelection.size === 0 && currentNoteId) {
    tempSourcesSelection.add(currentNoteId);
  }
  renderSourcesModalList();
  const modal = document.getElementById('sources-modal');
  if (modal) modal.classList.remove('hidden');
}

function closeSourcesModal() {
  const modal = document.getElementById('sources-modal');
  if (modal) modal.classList.add('hidden');
}

function renderSourcesModalList(searchQuery = '') {
  const listEl = document.getElementById('sources-modal-list');
  const countEl = document.getElementById('sources-modal-count');
  const wordsEl = document.getElementById('sources-modal-words');
  if (!listEl) return;

  const query = searchQuery.toLowerCase().trim();
  const filtered = allNotesCache.filter(n => {
    if (!query) return true;
    const title = (n.title || '').toLowerCase();
    const tags = Array.isArray(n.tags) ? n.tags.join(' ').toLowerCase() : '';
    return title.includes(query) || tags.includes(query);
  });

  let totalWords = 0;
  allNotesCache.forEach(n => {
    if (tempSourcesSelection.has(n.id)) {
      totalWords += countWords(n.content || '');
    }
  });

  if (countEl) countEl.textContent = `${tempSourcesSelection.size} catatan terpilih`;
  if (wordsEl) wordsEl.textContent = `~${totalWords} kata total konteks`;

  if (filtered.length === 0) {
    listEl.innerHTML = `<p style="text-align:center;color:var(--text-muted);font-size:0.8rem;padding:var(--space-4);">Tidak ada catatan yang cocok dengan pencarian.</p>`;
    return;
  }

  listEl.innerHTML = filtered.map(n => {
    const isSelected = tempSourcesSelection.has(n.id);
    const words = countWords(n.content || '');
    return `
      <div class="source-item-row ${isSelected ? 'selected' : ''}" onclick="toggleSourceSelection(${n.id})">
        <div class="source-item-left">
          <input type="checkbox" class="source-item-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleSourceSelection(${n.id});">
          <div class="source-item-info">
            <span class="source-item-title">${escapeHtml(n.title || 'Untitled')} ${n.id === currentNoteId ? '<span style="font-size:0.65rem;color:var(--gold-light);font-weight:700;">(AKTIF)</span>' : ''}</span>
            <span class="source-item-preview">${escapeHtml((n.content || '').slice(0, 90).replace(/\n/g, ' ') || 'Catatan kosong...')}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-stat">${words} kata</span>
          ${n.tags && n.tags[0] ? `<span class="source-item-tag">#${escapeHtml(n.tags[0])}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

window.toggleSourceSelection = function(id) {
  if (tempSourcesSelection.has(id)) {
    if (tempSourcesSelection.size <= 1) {
      showToast('Pilih minimal 1 catatan sebagai konteks', 'warning');
      return;
    }
    tempSourcesSelection.delete(id);
  } else {
    tempSourcesSelection.add(id);
  }
  const searchInput = document.getElementById('sources-search-input');
  renderSourcesModalList(searchInput?.value || '');
};

async function sendNoteChatMessage() {
  const input = document.getElementById('note-chat-input');
  const question = input?.value.trim();
  if (!question || isCopilotGenerating) return;

  if (selectedChatSourceIds.size === 0 && currentNoteId) {
    selectedChatSourceIds.add(currentNoteId);
  }

  // Build combined context across all selected notes
  let combinedContext = '';
  const selectedNotes = allNotesCache.filter(n => selectedChatSourceIds.has(n.id));

  for (const n of selectedNotes) {
    const content = (n.id === currentNoteId)
      ? (document.getElementById('note-textarea')?.value || n.content || '')
      : (n.content || '');
    combinedContext += `=== DOKUMEN: [${n.title || 'Untitled'}] ===\n${content}\n\n`;
  }

  if (!combinedContext.trim()) {
    showToast('Catatan sumber kosong, tidak ada bahan untuk ditanyakan', 'warning');
    return;
  }

  input.value = '';
  input.style.height = 'auto'; // reset textarea height
  noteChatHistory.push({ role: 'user', content: question });
  
  isCopilotGenerating = true;
  renderNoteChatMessages();

  try {
    const result = await callNotesAI('chat', { content: combinedContext, question });
    noteChatHistory.push({ role: 'assistant', content: result || 'Tidak ada respons dari AI.' });
  } catch (e) {
    noteChatHistory.push({ role: 'assistant', content: `[ERROR] Gagal mendapatkan jawaban dari Cortex AI: ${e.message}` });
  } finally {
    isCopilotGenerating = false;
    renderNoteChatMessages();
    setTimeout(() => {
      input.focus();
    }, 50);
  }
}

// Auto-expand textarea & Keydown listener
const copilotTextareaEl = document.getElementById('note-chat-input');
copilotTextareaEl?.addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 140) + 'px';
});

copilotTextareaEl?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendNoteChatMessage();
  }
});

// Sources Modal Events
document.getElementById('btn-open-sources-modal')?.addEventListener('click', openSourcesModal);
document.getElementById('btn-close-sources-modal')?.addEventListener('click', closeSourcesModal);
document.getElementById('btn-cancel-sources')?.addEventListener('click', closeSourcesModal);

document.getElementById('btn-sources-select-all')?.addEventListener('click', () => {
  allNotesCache.forEach(n => tempSourcesSelection.add(n.id));
  renderSourcesModalList(document.getElementById('sources-search-input')?.value || '');
});

document.getElementById('btn-sources-active-only')?.addEventListener('click', () => {
  tempSourcesSelection.clear();
  if (currentNoteId) tempSourcesSelection.add(currentNoteId);
  renderSourcesModalList(document.getElementById('sources-search-input')?.value || '');
});

document.getElementById('sources-search-input')?.addEventListener('input', (e) => {
  renderSourcesModalList(e.target.value);
});

document.getElementById('btn-apply-sources')?.addEventListener('click', () => {
  if (tempSourcesSelection.size === 0) {
    showToast('Pilih minimal 1 catatan sumber', 'warning');
    return;
  }
  selectedChatSourceIds = new Set(tempSourcesSelection);
  renderChatSourcesUI();
  closeSourcesModal();
  showToast(`Basis konteks diperbarui: ${selectedChatSourceIds.size} catatan terpilih! 📚`, 'success');
});

document.getElementById('btn-note-chat-send')?.addEventListener('click', sendNoteChatMessage);

document.getElementById('btn-clear-note-chat')?.addEventListener('click', () => {
  noteChatHistory = [];
  renderNoteChatMessages();
  showToast('Riwayat Co-Pilot dibersihkan', 'info');
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



// ─── Selection-Based Micro AI Actions ──────────────────────
let microSnippet       = '';
let microSource        = 'textarea'; // 'textarea' | 'view'
let microTextRange     = { start: 0, end: 0 };
let currentMicroResult = '';
let lastMouseUpPos     = { x: 0, y: 0 };

// Track mouse position on mouseup
document.addEventListener('mouseup', (e) => {
  lastMouseUpPos = { x: e.clientX, y: e.clientY };
});

function clampToolbarToViewport() {
  const toolbar = document.getElementById('micro-ai-toolbar');
  if (!toolbar || toolbar.classList.contains('hidden')) return;

  requestAnimationFrame(() => {
    const margin = 16;
    const topbarHeight = 65;
    const rect = toolbar.getBoundingClientRect();

    // Vertical clamping: if bottom goes below viewport, move top upwards
    if (rect.bottom > window.innerHeight - margin) {
      const overflowY = rect.bottom - (window.innerHeight - margin);
      const currentTop = parseFloat(toolbar.style.top) || rect.top;
      let newTop = currentTop - overflowY;
      if (newTop < topbarHeight) {
        newTop = topbarHeight;
      }
      toolbar.style.top = `${newTop}px`;
    }

    // Horizontal clamping: if right goes beyond viewport, move left
    const updatedRect = toolbar.getBoundingClientRect();
    if (updatedRect.right > window.innerWidth - margin) {
      const overflowX = updatedRect.right - (window.innerWidth - margin);
      const currentLeft = parseFloat(toolbar.style.left) || updatedRect.left;
      let newLeft = Math.max(margin, currentLeft - overflowX);
      toolbar.style.left = `${newLeft}px`;
    }
  });
}

let lastTriggerPos     = { x: 0, y: 0 };

function hideMicroTrigger() {
  const trigger = document.getElementById('micro-ai-trigger');
  if (trigger) trigger.classList.add('hidden');
}

function showMicroTrigger(x, y, snippet, source, range = null) {
  microSnippet = snippet;
  microSource  = source;
  if (range) microTextRange = range;
  lastTriggerPos = { x, y };

  const trigger = document.getElementById('micro-ai-trigger');
  if (!trigger) return;

  // Position trigger floating calmly right above the selection point
  let posX = x;
  let posY = y - 36;

  // Keep within viewport boundaries
  if (posX + 130 > window.innerWidth - 16) {
    posX = window.innerWidth - 146;
  }
  if (posX < 16) posX = 16;
  if (posY < 65) posY = y + 24;

  trigger.style.left = `${posX}px`;
  trigger.style.top  = `${posY}px`;
  trigger.classList.remove('hidden');
}

function hideMicroToolbar() {
  hideMicroTrigger();
  const toolbar = document.getElementById('micro-ai-toolbar');
  const popover = document.getElementById('micro-ai-popover');
  if (toolbar) {
    toolbar.classList.add('hidden');
    toolbar.classList.remove('has-result');
  }
  if (popover) {
    popover.classList.add('hidden');
    const popContent = document.getElementById('micro-popover-content');
    if (popContent) popContent.innerHTML = '';
  }
  document.querySelectorAll('.micro-btn').forEach(btn => btn.classList.remove('active', 'loading'));
  microSnippet = '';
  currentMicroResult = '';
}

function showMicroToolbar(x, y, snippet, source, range = null) {
  hideMicroTrigger();
  microSnippet = snippet;
  microSource  = source;
  if (range) microTextRange = range;

  const toolbar = document.getElementById('micro-ai-toolbar');
  const popover = document.getElementById('micro-ai-popover');
  if (!toolbar) return;

  toolbar.classList.remove('has-result');
  if (popover) {
    popover.classList.add('hidden');
    const popContent = document.getElementById('micro-popover-content');
    if (popContent) popContent.innerHTML = '';
  }
  document.querySelectorAll('.micro-btn').forEach(btn => btn.classList.remove('active', 'loading'));

  // Calculate coordinates clamped to viewport (Vertical Menu Layout)
  const menuWidth  = 190;
  const menuHeight = 220;
  let posX = x + 12;
  let posY = y - 10;

  // Flip horizontally if overflow to right
  if (posX + menuWidth > window.innerWidth - 16) {
    posX = x - menuWidth - 12;
  }
  if (posX < 16) posX = 16;

  // Flip vertically if overflow to bottom
  if (posY + menuHeight > window.innerHeight - 16) {
    posY = window.innerHeight - menuHeight - 20;
  }
  if (posY < 65) posY = 65;

  toolbar.style.left = `${posX}px`;
  toolbar.style.top  = `${posY}px`;
  toolbar.classList.remove('hidden');

  clampToolbarToViewport();
}

// Click trigger pill to reveal the full contextual actions menu
document.getElementById('btn-micro-trigger')?.addEventListener('click', (e) => {
  e.stopPropagation();
  hideMicroTrigger();
  showMicroToolbar(lastTriggerPos.x, lastTriggerPos.y, microSnippet, microSource, microTextRange);
});

function checkTextareaSelection() {
  const ta = document.getElementById('note-textarea');
  if (!ta) return;
  const start = ta.selectionStart;
  const end   = ta.selectionEnd;
  if (end > start) {
    const selected = ta.value.substring(start, end).trim();
    if (selected.length >= 3) {
      const rect = ta.getBoundingClientRect();
      const x = lastMouseUpPos.x > 0 ? lastMouseUpPos.x : (rect.left + 40);
      const y = lastMouseUpPos.y > 0 ? lastMouseUpPos.y : (rect.top + 50);
      showMicroTrigger(x, y, selected, 'textarea', { start, end });
      return;
    }
  }
  // User unselected or clicked to move cursor -> dismiss toolbar
  hideMicroToolbar();
}

function checkViewSelection() {
  const viewEl = document.getElementById('note-view-content');
  if (!viewEl) return;
  const sel = window.getSelection();
  if (sel && !sel.isCollapsed) {
    const selected = sel.toString().trim();
    if (selected.length >= 3 && viewEl.contains(sel.anchorNode)) {
      try {
        const range = sel.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        showMicroTrigger(rect.right, rect.top, selected, 'view');
        return;
      } catch (err) {
        console.warn('Range rect error:', err);
      }
    }
  }
  // User unselected in view -> dismiss toolbar
  hideMicroToolbar();
}

// Attach selection listeners
const noteTextarea = document.getElementById('note-textarea');
if (noteTextarea) {
  noteTextarea.addEventListener('mouseup', () => {
    setTimeout(checkTextareaSelection, 20);
  });
  noteTextarea.addEventListener('keyup', (e) => {
    if (['Shift', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
      setTimeout(checkTextareaSelection, 20);
    } else {
      if (noteTextarea.selectionStart === noteTextarea.selectionEnd) {
        hideMicroToolbar();
      }
    }
  });
}

const noteViewContent = document.getElementById('note-view-content');
if (noteViewContent) {
  noteViewContent.addEventListener('mouseup', () => {
    setTimeout(checkViewSelection, 20);
  });
}

// Click outside dismissal: any click outside toolbar and trigger dismisses them immediately
document.addEventListener('mousedown', (e) => {
  const toolbar = document.getElementById('micro-ai-toolbar');
  const trigger = document.getElementById('micro-ai-trigger');
  
  const inToolbar = toolbar && !toolbar.classList.contains('hidden') && toolbar.contains(e.target);
  const inTrigger = trigger && !trigger.classList.contains('hidden') && trigger.contains(e.target);
  
  if (!inToolbar && !inTrigger) {
    hideMicroToolbar();
  }
});

// Selection change listener: dismiss if selection collapses anywhere
document.addEventListener('selectionchange', () => {
  const toolbar = document.getElementById('micro-ai-toolbar');
  const trigger = document.getElementById('micro-ai-trigger');
  const isToolbarOpen = toolbar && !toolbar.classList.contains('hidden');
  const isTriggerOpen = trigger && !trigger.classList.contains('hidden');
  if (!isToolbarOpen && !isTriggerOpen) return;

  const ta = document.getElementById('note-textarea');
  if (document.activeElement === ta && ta) {
    if (ta.selectionStart === ta.selectionEnd) {
      hideMicroToolbar();
    }
  } else {
    const sel = window.getSelection();
    if (sel && sel.isCollapsed && (!toolbar || !toolbar.contains(document.activeElement)) && (!trigger || !trigger.contains(document.activeElement))) {
      hideMicroToolbar();
    }
  }
});

// Micro AI Buttons click
document.querySelectorAll('.micro-btn').forEach(btn => {
  btn.addEventListener('click', async (e) => {
    e.stopPropagation();
    const microType = btn.dataset.micro;
    if (!microSnippet) {
      showToast('Pilih potongan teks terlebih dahulu', 'warning');
      return;
    }

    document.querySelectorAll('.micro-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active', 'loading');

    const toolbar     = document.getElementById('micro-ai-toolbar');
    const popover     = document.getElementById('micro-ai-popover');
    const popTitle    = document.getElementById('micro-popover-title');
    const popContent  = document.getElementById('micro-popover-content');
    const replaceBtn  = document.getElementById('btn-micro-replace');

    const titles = {
      refine: '🪄 Hasil Poles Teks (Refined)',
      summarize: '📝 Ringkasan Poin Kunci',
      explain: '🔍 Penjelasan Istilah / Konsep',
      translate: '🌐 Terjemahan Dwibahasa',
      todo: '⚡ Checklist Tindakan (To-Do)'
    };

    if (popTitle) popTitle.textContent = titles[microType] || '✨ Hasil Cortex AI';
    if (popContent) popContent.innerHTML = '<div style="color:var(--gold-light);display:flex;align-items:center;gap:8px;"><div class="nucleus-spinner" style="width:18px;height:18px;border-width:2px;"></div> Memproses dengan Neural Cortex...</div>';
    
    if (toolbar) toolbar.classList.add('has-result');
    if (popover) popover.classList.remove('hidden');

    // Clamp immediately so popover expansion stays within viewport
    clampToolbarToViewport();

    // Explain might not necessarily replace, but keep available
    if (replaceBtn) {
      replaceBtn.style.display = (microType === 'explain') ? 'none' : 'inline-flex';
    }

    try {
      const result = await callNotesAI('micro', {
        content: microSnippet,
        micro_type: microType
      });

      if (result && !String(result).startsWith('[ERROR]')) {
        currentMicroResult = result;
        if (popContent) {
          popContent.textContent = result;
        }
      } else {
        throw new Error(result || 'Gagal memproses');
      }
    } catch (err) {
      console.error('[MICRO AI ERROR]', err);
      if (popContent) {
        popContent.innerHTML = `<span style="color:#ef4444;">⚠️ ${escapeHtml(err.message)}</span>`;
      }
    } finally {
      btn.classList.remove('loading');
      // Re-clamp after content is rendered
      clampToolbarToViewport();
    }
  });
});

// Window resize listener to keep toolbar clamped
window.addEventListener('resize', clampToolbarToViewport);

// Popover action buttons
document.getElementById('btn-close-micro-toolbar')?.addEventListener('click', (e) => {
  e.stopPropagation();
  hideMicroToolbar();
});

document.getElementById('btn-close-micro-popover')?.addEventListener('click', (e) => {
  e.stopPropagation();
  const toolbar = document.getElementById('micro-ai-toolbar');
  const popover = document.getElementById('micro-ai-popover');
  if (popover) popover.classList.add('hidden');
  if (toolbar) toolbar.classList.remove('has-result');
  document.querySelectorAll('.micro-btn').forEach(b => b.classList.remove('active', 'loading'));
  currentMicroResult = '';
  clampToolbarToViewport();
});

document.getElementById('btn-micro-copy')?.addEventListener('click', async (e) => {
  e.stopPropagation();
  if (!currentMicroResult) return;
  try {
    await navigator.clipboard.writeText(currentMicroResult);
    showToast('Teks hasil AI berhasil disalin! 📋', 'success');
  } catch {
    showToast('Gagal menyalin teks', 'error');
  }
});

document.getElementById('btn-micro-replace')?.addEventListener('click', (e) => {
  e.stopPropagation();
  if (!currentMicroResult) return;

  const ta = document.getElementById('note-textarea');
  if (microSource === 'textarea' && ta) {
    const val = ta.value;
    const start = microTextRange.start;
    const end   = microTextRange.end;
    ta.value = val.substring(0, start) + currentMicroResult + val.substring(end);
    ta.setSelectionRange(start, start + currentMicroResult.length);
    triggerAutoSave(true);
    hideMicroToolbar();
    showToast('Teks berhasil diganti! ✨', 'success');
  } else if (microSource === 'view' && ta) {
    // Replace snippet in textarea value
    if (ta.value.includes(microSnippet)) {
      ta.value = ta.value.replace(microSnippet, currentMicroResult);
      const viewEl = document.getElementById('note-view-content');
      if (viewEl && typeof marked !== 'undefined') {
        viewEl.innerHTML = marked.parse(ta.value);
      }
      triggerAutoSave(true);
      hideMicroToolbar();
      showToast('Teks berhasil diperbarui! ✨', 'success');
    } else {
      setNoteMode('edit');
      showToast('Beralih ke mode edit untuk menyunting', 'info');
    }
  }
});

document.getElementById('btn-micro-insert')?.addEventListener('click', (e) => {
  e.stopPropagation();
  if (!currentMicroResult) return;

  const ta = document.getElementById('note-textarea');
  if (microSource === 'textarea' && ta) {
    const val = ta.value;
    const end = microTextRange.end;
    const insertion = `\n\n${currentMicroResult}`;
    ta.value = val.substring(0, end) + insertion + val.substring(end);
    ta.setSelectionRange(end + insertion.length, end + insertion.length);
    triggerAutoSave(true);
    hideMicroToolbar();
    showToast('Teks berhasil disisipkan di bawah! ➕', 'success');
  } else if (microSource === 'view' && ta) {
    if (ta.value.includes(microSnippet)) {
      ta.value = ta.value.replace(microSnippet, `${microSnippet}\n\n${currentMicroResult}`);
      const viewEl = document.getElementById('note-view-content');
      if (viewEl && typeof marked !== 'undefined') {
        viewEl.innerHTML = marked.parse(ta.value);
      }
      triggerAutoSave(true);
      hideMicroToolbar();
      showToast('Teks berhasil disisipkan! ➕', 'success');
    } else {
      setNoteMode('edit');
      showToast('Beralih ke mode edit untuk menyunting', 'info');
    }
  }
});

// ─── AI Studio Dropdown Menu Toggle ────────────────────────
const aiStudioToggle = document.getElementById('btn-ai-studio-toggle');
const aiStudioMenu   = document.getElementById('ai-studio-menu');

if (aiStudioToggle && aiStudioMenu) {
  aiStudioToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    aiStudioMenu.classList.toggle('hidden');
  });

  // Clicking an item in the menu automatically closes it
  aiStudioMenu.querySelectorAll('.ai-menu-item').forEach(item => {
    item.addEventListener('click', () => {
      aiStudioMenu.classList.add('hidden');
    });
  });

  // Click outside closes menu
  document.addEventListener('click', (e) => {
    if (!aiStudioMenu.classList.contains('hidden') && !aiStudioMenu.contains(e.target) && !aiStudioToggle.contains(e.target)) {
      aiStudioMenu.classList.add('hidden');
    }
  });
}

