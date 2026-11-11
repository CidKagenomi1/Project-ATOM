// ─── ATOM Notes: Concept & Test Bubbles ──────────────────
// ─── Bubble API Handlers with Resilient Local Fallback ─────
const LOCAL_BUBBLES_KEY = 'atom_local_bubbles';

function getLocalBubbles() {
  try {
    const raw = localStorage.getItem(LOCAL_BUBBLES_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveLocalBubbles(list) {
  try {
    localStorage.setItem(LOCAL_BUBBLES_KEY, JSON.stringify(list));
  } catch (e) {
    console.warn('LocalStorage save error:', e);
  }
}

async function loadBubbles() {
  try {
    const resp = await fetch('/api/bubbles');
    if (resp.ok) {
      const data = await resp.json();
      if (Array.isArray(data)) {
        saveLocalBubbles(data);
        return data;
      }
    }
  } catch (err) {
    console.warn('[LOAD BUBBLES] API unreachable, using local storage cache:', err);
  }
  return getLocalBubbles();
}

async function addBubble(text) {
  const randomColors = ['#9333EA', '#3B82F6', '#14B8A6', '#F59E0B', '#F43F5E', '#10B981'];
  const newBubble = {
    id: Date.now(),
    text: text,
    color: randomColors[Math.floor(Math.random() * randomColors.length)],
    created_at: new Date().toISOString(),
    expanded: false
  };

  try {
    const resp = await fetch('/api/bubbles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (resp.ok) {
      const serverBubble = await resp.json();
      const local = getLocalBubbles();
      // Remove any existing with same id if any, and insert
      const filtered = local.filter(b => String(b.id) !== String(serverBubble.id));
      filtered.unshift(serverBubble);
      saveLocalBubbles(filtered);
      return serverBubble;
    }
  } catch (err) {
    console.warn('[ADD BUBBLE] Server unavailable, fallback to local storage:', err);
  }

  // Fallback to local storage
  const local = getLocalBubbles();
  local.unshift(newBubble);
  saveLocalBubbles(local);
  return newBubble;
}

async function deleteBubble(id) {
  // 1. Immediately remove from local storage cache
  const local = getLocalBubbles().filter(b => String(b.id) !== String(id));
  saveLocalBubbles(local);

  // 2. Call backend DELETE
  try {
    const resp = await fetch(`/api/bubbles/${encodeURIComponent(id)}`, { method: 'DELETE' });
    if (!resp.ok) {
      console.warn('[DELETE BUBBLE] Server responded with HTTP status:', resp.status);
    }
  } catch (err) {
    console.warn('[DELETE BUBBLE] Server unreachable, deleted locally:', err);
  }
  return true;
}



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
      <div class="bubble-card" data-id="${b.id}" style="
        background: linear-gradient(135deg, ${hex}28, rgba(22, 27, 34, 0.75));
        border: 1px solid ${hex}55;
        box-shadow: 0 4px 16px ${hex}18;
      ">
        <p class="bubble-text">${escapeHtml(b.text || '')}</p>
        <div class="bubble-footer">
          <span class="bubble-date">${date} ${b.expanded ? '✨ Expanded' : ''}</span>
          <div class="bubble-actions" style="display:flex;gap:6px;">
            ${!b.expanded 
              ? `<button class="btn btn-primary btn-sm" onclick="expandBubble('${b.id}', event)" title="Kembangkan menjadi artikel penuh">🚀 Expand</button>` 
              : '<span style="font-size:0.72rem;color:var(--success);padding:4px 6px;font-weight:700;">✅ Expanded</span>'}
            <button class="btn btn-danger btn-sm" onclick="removeBubble('${b.id}', event)" title="Hapus bubble">🗑</button>
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

window.removeBubble = async function(id, event) {
  if (event && event.stopPropagation) event.stopPropagation();
  if (!confirm('Hapus Magic Bubble ini?')) return;

  // Optimistic UI removal: smooth shrink and fade immediately
  const card = document.querySelector(`.bubble-card[data-id="${id}"]`);
  if (card) {
    card.style.transition = 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)';
    card.style.opacity = '0';
    card.style.transform = 'scale(0.8)';
    setTimeout(() => {
      if (card && card.parentNode) card.remove();
    }, 250);
  }

  const ok = await deleteBubble(id);
  if (ok) {
    await renderBubbles();
    showToast('Bubble dihapus 🗑', 'info');
  } else {
    showToast('Gagal menghapus bubble', 'error');
  }
};

window.expandBubble = async function(id, event) {
  if (event && event.stopPropagation) event.stopPropagation();
  showAIOverlay('CrewAI sedang meriset & menulis artikel...');
  try {
    const resp = await fetch(`/api/bubbles/${encodeURIComponent(id)}/expand`, { method: 'POST' });
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

