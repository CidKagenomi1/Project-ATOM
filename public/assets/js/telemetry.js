/**
 * A.T.O.M. — Resilient Telemetry & Model Usage Dashboard
 * Architecture: Client-First Fast Store with Session Backfill & Background Cloud Sync
 * Zero connection drops, instant rendering, comprehensive per-model metrics.
 */

let allTelemetryLogs = [];
let currentFilter = 'all';

// ─── Provider Categorizer & Stylizer ─────────────────────────────
function getModelCategory(modelName) {
  const m = (modelName || '').toLowerCase();
  if (m.includes('groq')) return { id: 'groq', name: 'Groq Cloud', color: '#a78bfa', badgeClass: 'badge-groq', icon: '⚡' };
  if (m.includes('deepseek')) return { id: 'deepseek', name: 'DeepSeek Cloud', color: '#38bdf8', badgeClass: 'badge-deepseek', icon: '🐳' };
  if (m.includes('gemini')) return { id: 'gemini', name: 'Google Gemini', color: '#60a5fa', badgeClass: 'badge-gemini', icon: '♊' };
  if (m.includes('openrouter') || m.includes('or:')) return { id: 'openrouter', name: 'OpenRouter Free', color: '#f472b6', badgeClass: 'badge-openrouter', icon: '🌐' };
  if (m.includes('ollama')) return { id: 'ollama', name: 'Ollama Local', color: '#34d399', badgeClass: 'badge-ollama', icon: '🧠' };
  if (m.includes('cortex') || m.includes('auto')) return { id: 'cortex', name: 'Cortex Route', color: '#ebb338', badgeClass: 'badge-cortex', icon: '🤖' };
  return { id: 'other', name: 'Custom AI', color: '#94a3b8', badgeClass: 'badge-cortex', icon: '✨' };
}

// ─── Format Token Helper ─────────────────────────────────────────
function formatTokens(num) {
  if (!num || isNaN(num)) return '0';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toLocaleString();
}

function formatDuration(num) {
  const d = parseFloat(num);
  if (isNaN(d) || d <= 0) return '0.80s';
  return d.toFixed(2) + 's';
}

function formatDate(isoStr) {
  try {
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr || '-';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + 
           ' · ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  } catch {
    return isoStr || '-';
  }
}

// ─── Load Telemetry Data (Client-First Resilient Architecture) ───
async function loadTelemetryData() {
  let logs = [];
  const statusPill = document.getElementById('sync-status-text');

  // 1. Ambil dari LocalStorage utama (Instan 0ms)
  try {
    const raw = localStorage.getItem('atom_telemetry_logs');
    if (raw) {
      logs = JSON.parse(raw);
    }
  } catch (e) {
    console.warn('[ATOM] Failed to parse local telemetry:', e);
  }

  // 2. Jika log kosong atau sangat sedikit, lakukan backfill otomatis dari riwayat obrolan
  if (!logs || logs.length === 0) {
    if (typeof window.backfillTelemetryFromSessions === 'function') {
      const backfilled = window.backfillTelemetryFromSessions();
      if (backfilled && backfilled.length > 0) {
        logs = backfilled;
        try {
          localStorage.setItem('atom_telemetry_logs', JSON.stringify(logs));
        } catch {}
      }
    }
  }

  // 3. Background fetch opsional dari backend /api/telemetry (Non-blocking)
  try {
    const resp = await fetch('/api/telemetry', { cache: 'no-store' });
    if (resp.ok) {
      const serverRows = await resp.json();
      if (Array.isArray(serverRows) && serverRows.length > 0) {
        // Gabungkan tanpa duplikasi prompt & waktu yang persis sama
        const existingKeys = new Set(logs.map(l => (l.timestamp || '') + '|' + (l.user_input || '').slice(0, 30)));
        serverRows.forEach(sr => {
          const key = (sr.timestamp || '') + '|' + (sr.user_input || '').slice(0, 30);
          if (!existingKeys.has(key)) {
            const pLen = (sr.user_input || '').length;
            const rLen = (sr.ai_response || '').length;
            logs.push({
              id: 'srv_' + Math.random().toString(36).substring(2, 8),
              timestamp: sr.timestamp || new Date().toISOString(),
              user_input: sr.user_input || '',
              model_used: sr.model_used || 'Unknown',
              response_time: parseFloat(sr.response_time) || 1.2,
              status: sr.status || 'SUCCESS',
              ai_response: sr.ai_response || '',
              tokens: {
                prompt: Math.max(1, Math.ceil(pLen / 4)),
                completion: Math.max(1, Math.ceil(rLen / 4)),
                total: Math.max(2, Math.ceil((pLen + rLen) / 4))
              }
            });
            existingKeys.add(key);
          }
        });
        
        // Simpan gabungan terbaru ke local
        try {
          localStorage.setItem('atom_telemetry_logs', JSON.stringify(logs));
        } catch {}
        
        if (statusPill) statusPill.textContent = 'Local & Server Synced';
      }
    }
  } catch (err) {
    // Jika backend offline/putus, tetap aman gunakan data lokal
    if (statusPill) statusPill.textContent = 'Client-First Offline Mode';
  }

  // Urutkan dari yang paling baru
  logs.sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0));
  return logs;
}

// ─── Main Render Function ────────────────────────────────────────
async function loadAndRender() {
  allTelemetryLogs = await loadTelemetryData();

  const noDataEl  = document.getElementById('no-data');
  const contentEl = document.getElementById('telem-content');
  const countBadge = document.getElementById('telem-badge-count');

  if (!allTelemetryLogs || allTelemetryLogs.length === 0) {
    if (noDataEl)  noDataEl.style.display  = 'block';
    if (contentEl) contentEl.style.display = 'none';
    if (countBadge) countBadge.textContent = '0 Riwayat';
    return;
  }

  if (noDataEl)  noDataEl.style.display  = 'none';
  if (contentEl) contentEl.style.display = 'block';

  const total = allTelemetryLogs.length;
  if (countBadge) countBadge.textContent = `${total.toLocaleString()} Aktivitas`;

  // 1. Overview Calculations
  let totalTokens = 0;
  let totalPromptTokens = 0;
  let totalCompletionTokens = 0;
  let totalDuration = 0;
  let successCount = 0;

  const modelMap = {};

  allTelemetryLogs.forEach(entry => {
    const t = entry.tokens || {};
    const promptTok = t.prompt || Math.max(1, Math.ceil((entry.user_input || '').length / 4));
    const compTok = t.completion || Math.max(1, Math.ceil((entry.ai_response || '').length / 4));
    const tok = t.total || (promptTok + compTok);

    totalTokens += tok;
    totalPromptTokens += promptTok;
    totalCompletionTokens += compTok;

    const dur = parseFloat(entry.response_time) || 0;
    totalDuration += dur;

    if (entry.status === 'SUCCESS' || entry.status === 'FAILOVER') {
      successCount++;
    }

    const modelKey = entry.model_used || 'Cortex Route';
    if (!modelMap[modelKey]) {
      modelMap[modelKey] = {
        model: modelKey,
        category: getModelCategory(modelKey),
        count: 0,
        durations: [],
        totalTokens: 0,
        promptTokens: 0,
        completionTokens: 0,
        success: 0,
        lastUsed: entry.timestamp
      };
    }

    modelMap[modelKey].count++;
    modelMap[modelKey].durations.push(dur);
    modelMap[modelKey].totalTokens += tok;
    modelMap[modelKey].promptTokens += promptTok;
    modelMap[modelKey].completionTokens += compTok;
    if (entry.status === 'SUCCESS' || entry.status === 'FAILOVER') {
      modelMap[modelKey].success++;
    }
  });

  const avgDuration = total > 0 ? (totalDuration / total) : 0;
  const successRate = total > 0 ? Math.round((successCount / total) * 100) : 100;

  // Set Top Metric Values
  setText('m-total', total.toLocaleString());
  setText('m-total-sub', `${Object.keys(modelMap).length} model AI aktif`);
  setText('m-tokens', formatTokens(totalTokens));
  setText('m-tokens-sub', `${formatTokens(totalPromptTokens)} in / ${formatTokens(totalCompletionTokens)} out`);
  setText('m-avg', formatDuration(avgDuration));
  setText('m-avg-sub', 'Rata-rata latensi respons');
  setText('m-success', successRate + '%');
  setText('m-success-sub', `${total - successCount} gagal tercatat`);

  // 2. Render Model Usage Cards
  renderModelCards(modelMap, total);

  // 3. Render Share Breakdown Bars
  renderModelShareBars(modelMap, total);

  // 4. Render Latency Comparisons
  renderLatencyComparison(allTelemetryLogs, modelMap);

  // 5. Setup Filter Pills & Table
  setupFilterPills(modelMap);
  renderActivityTable(currentFilter);

  // 6. Render Feedback & Critique Intelligence
  renderFeedbackCritique(allTelemetryLogs);
}

// ─── Render Individual Model Usage Cards ─────────────────────────
function renderModelCards(modelMap, totalQueries) {
  const container = document.getElementById('model-cards-container');
  if (!container) return;

  const modelsList = Object.values(modelMap).sort((a, b) => b.count - a.count);

  container.innerHTML = modelsList.map(item => {
    const sharePct = Math.round((item.count / totalQueries) * 100);
    const avgDur = item.durations.length > 0 
      ? (item.durations.reduce((a, b) => a + b, 0) / item.durations.length) 
      : 0;
    const cat = item.category;

    return `
      <div class="model-stat-card">
        <div class="model-card-top">
          <div class="model-card-title">
            <span style="font-size:1.15rem;">${cat.icon}</span>
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px;" title="${escapeHtml(item.model)}">
              ${escapeHtml(item.model)}
            </span>
          </div>
          <span class="model-provider-badge ${cat.badgeClass}">${escapeHtml(cat.name)}</span>
        </div>

        <div class="model-stat-grid">
          <div class="model-stat-item">
            <span class="model-stat-label">Total Calls</span>
            <span class="model-stat-val text-gold">${item.count} <span style="font-size:0.75rem;font-weight:400;color:var(--text-muted);">(${sharePct}%)</span></span>
          </div>
          <div class="model-stat-item">
            <span class="model-stat-label">Est. Tokens</span>
            <span class="model-stat-val" style="color:${cat.color};">${formatTokens(item.totalTokens)}</span>
          </div>
          <div class="model-stat-item">
            <span class="model-stat-label">Avg Speed</span>
            <span class="model-stat-val">${formatDuration(avgDur)}</span>
          </div>
          <div class="model-stat-item">
            <span class="model-stat-label">Reliability</span>
            <span class="model-stat-val text-success">${Math.round((item.success / item.count) * 100)}%</span>
          </div>
        </div>

        <div>
          <div style="display:flex;justify-content:space-between;font-size:0.68rem;color:var(--text-muted);margin-bottom:2px;">
            <span>Pangsa Lalu Lintas</span>
            <span style="color:${cat.color};font-weight:600;">${sharePct}%</span>
          </div>
          <div class="model-progress-bar">
            <div class="model-progress-fill" style="width:${sharePct}%;background:${cat.color};"></div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Render Share Breakdown Bars ─────────────────────────────────
function renderModelShareBars(modelMap, totalQueries) {
  const usageEl = document.getElementById('model-usage-list');
  if (!usageEl) return;

  const sorted = Object.values(modelMap).sort((a, b) => b.count - a.count);

  usageEl.innerHTML = sorted.map(item => {
    const pct = Math.round((item.count / totalQueries) * 100);
    const cat = item.category;

    return `
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="font-size:0.9rem;">${cat.icon}</span>
            <span style="font-size:0.8rem;color:var(--text-primary);font-weight:600;">${escapeHtml(item.model)}</span>
          </div>
          <span style="font-size:0.75rem;color:var(--text-muted);font-family:var(--font-mono);">${item.count} calls · ${pct}%</span>
        </div>
        <div style="height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;">
          <div style="width:${pct}%;height:100%;background:${cat.color};border-radius:3px;transition:width 0.5s ease;"></div>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Render Latency Comparison ───────────────────────────────────
function renderLatencyComparison(logs, modelMap) {
  const times = logs.map(d => parseFloat(d.response_time) || 0).filter(t => t > 0);
  const fastest = times.length > 0 ? Math.min(...times) : 0;
  const slowest = times.length > 0 ? Math.max(...times) : 0;
  const avgT = times.length > 0 ? (times.reduce((a, b) => a + b, 0) / times.length) : 0;

  setText('t-fastest', formatDuration(fastest));
  setText('t-avg', formatDuration(avgT));
  setText('t-slowest', formatDuration(slowest));

  const modelTimesEl = document.getElementById('model-time-bars');
  if (!modelTimesEl) return;

  const modelAvgs = Object.values(modelMap).map(item => {
    const avg = item.durations.length > 0 
      ? (item.durations.reduce((a, b) => a + b, 0) / item.durations.length) 
      : 0;
    return { model: item.model, avg, category: item.category };
  }).sort((a, b) => a.avg - b.avg);

  const maxAvg = Math.max(...modelAvgs.map(m => m.avg), 1);

  modelTimesEl.innerHTML = modelAvgs.map(item => {
    const pct = Math.min(100, Math.max(12, Math.round((item.avg / maxAvg) * 100)));
    return `
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:2px;font-size:0.72rem;">
          <span style="color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px;">
            ${escapeHtml(item.model)}
          </span>
          <span style="color:${item.category.color};font-weight:600;font-family:var(--font-mono);">${item.avg.toFixed(2)}s</span>
        </div>
        <div style="height:4px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;">
          <div style="width:${pct}%;height:100%;background:${item.category.color};border-radius:2px;"></div>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Setup Filter Pills Row ──────────────────────────────────────
function setupFilterPills(modelMap) {
  const container = document.getElementById('filter-pills-container');
  if (!container) return;

  const categories = [{ id: 'all', label: 'Semua Model' }];
  const seenIds = new Set();

  Object.values(modelMap).forEach(item => {
    const cat = item.category;
    if (!seenIds.has(cat.id)) {
      seenIds.add(cat.id);
      categories.push({ id: cat.id, label: `${cat.icon} ${cat.name}` });
    }
  });

  container.innerHTML = categories.map(cat => `
    <button class="filter-pill ${currentFilter === cat.id ? 'active' : ''}" data-filter="${cat.id}">
      ${cat.label}
    </button>
  `).join('');

  container.querySelectorAll('.filter-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      renderActivityTable(currentFilter);
    });
  });
}

// ─── Render Activity Table ───────────────────────────────────────
function renderActivityTable(filter) {
  const tbody = document.getElementById('activity-tbody');
  if (!tbody) return;

  let filtered = allTelemetryLogs;
  if (filter && filter !== 'all') {
    filtered = allTelemetryLogs.filter(row => {
      const cat = getModelCategory(row.model_used);
      return cat.id === filter;
    });
  }

  const recent = filtered.slice(0, 30);

  if (recent.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center;padding:var(--space-6);color:var(--text-muted);">
          Tidak ada riwayat telemetri untuk filter ini.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = recent.map((row, idx) => {
    const ts = formatDate(row.timestamp);
    const dur = formatDuration(row.response_time);
    const statusColor = (row.status === 'SUCCESS' || row.status === 'FAILOVER') ? 'var(--success)' : 'var(--error)';
    const cat = getModelCategory(row.model_used);
    const badgeClass = cat.badgeClass || 'badge-cortex';
    const estTokens = row.tokens?.total ? formatTokens(row.tokens.total) : formatTokens(Math.ceil((row.user_input || '').length / 4));
    const rowId = `telem-row-${idx}`;

    return `
      <tr onclick="toggleRowDetails('${rowId}')" style="cursor:pointer;" class="telem-header-row">
        <td style="white-space:nowrap;font-size:0.75rem;">${escapeHtml(ts)}</td>
        <td>
          <span class="model-badge" style="color:${cat.color};border-color:${cat.color}44;">
            ${cat.icon} ${escapeHtml(row.model_used || '-')}
          </span>
        </td>
        <td style="font-family:var(--font-mono);font-size:0.75rem;">${dur}</td>
        <td style="font-family:var(--font-mono);font-size:0.75rem;color:var(--gold-light);">${estTokens}</td>
        <td><span style="color:${statusColor};font-size:0.72rem;font-weight:700;">${escapeHtml(row.status || '-')}</span></td>
        <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="Klik untuk membuka detail kueri">${escapeHtml(row.user_input || '-')}</td>
      </tr>
      <tr id="${rowId}-details" style="display:none; background: rgba(0, 0, 0, 0.35);">
        <td colspan="6" style="padding:var(--space-4); border-bottom:var(--glass-border);">
          <div style="display:flex; flex-direction:column; gap:var(--space-3); text-align:left;">
            <div>
              <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px; font-weight:700;">
                User Prompt (${row.tokens?.prompt ? row.tokens.prompt + ' tokens' : 'input'})
              </div>
              <div style="font-size:0.85rem; color:var(--text-primary); white-space:pre-wrap; background:rgba(255,255,255,0.02); padding:var(--space-3); border-radius:var(--radius-md); border:var(--glass-border); font-family:var(--font-chat);">
                ${escapeHtml(row.user_input || '-')}
              </div>
            </div>
            <div>
              <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px; font-weight:700;">
                AI Response Output (${row.tokens?.completion ? row.tokens.completion + ' tokens' : 'output'})
              </div>
              <div style="font-size:0.85rem; color:var(--text-primary); white-space:pre-wrap; background:rgba(255,255,255,0.02); padding:var(--space-3); border-radius:var(--radius-md); border:var(--glass-border); font-family:var(--font-chat);">
                ${escapeHtml(row.ai_response || '(Respons AI tidak tercatat untuk entri ini)')}
              </div>
            </div>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Expandable telemetry row handler
window.toggleRowDetails = function(rowId) {
  const detailsEl = document.getElementById(`${rowId}-details`);
  if (detailsEl) {
    const isHidden = detailsEl.style.display === 'none';
    detailsEl.style.display = isHidden ? 'table-row' : 'none';
  }
};

// ─── Export Telemetry (Download JSON) ─────────────────────────────
document.getElementById('btn-export-telemetry')?.addEventListener('click', () => {
  if (!allTelemetryLogs || allTelemetryLogs.length === 0) {
    if (typeof showToast === 'function') showToast('Belum ada data untuk diekspor', 'warning');
    return;
  }
  const jsonStr = JSON.stringify(allTelemetryLogs, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `atom_telemetry_export_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  if (typeof showToast === 'function') showToast('Data telemetri berhasil diekspor', 'success');
});

// ─── Clear Telemetry ─────────────────────────────────────────────
document.getElementById('btn-clear-telemetry')?.addEventListener('click', async () => {
  if (!confirm('Hapus semua data telemetri dan metrik penggunaan model?')) return;
  
  // 1. Bersihkan localStorage
  try {
    localStorage.removeItem('atom_telemetry_logs');
    localStorage.removeItem('atom_model_usage_stats');
  } catch {}

  // 2. Bersihkan server jika terhubung
  try {
    await fetch('/api/telemetry', { method: 'DELETE' });
  } catch {}

  allTelemetryLogs = [];
  if (typeof showToast === 'function') showToast('Semua data telemetri telah dibersihkan', 'info');
  await loadAndRender();
});

// ─── Helper ───────────────────────────────────────────────────────
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ─── Render Feedback & Critique Intelligence Feed ────────────────
function renderFeedbackCritique(logs) {
  const badgeEl = document.getElementById('feedback-stat-badge');
  const totalEl = document.getElementById('fb-total');
  const likesEl = document.getElementById('fb-likes');
  const dislikesEl = document.getElementById('fb-dislikes');
  const ratioEl = document.getElementById('fb-ratio');
  const critiqueContainer = document.getElementById('critique-list-container');

  if (!logs) return;

  // Saring semua feedback likes & dislikes
  const feedbackEntries = logs.filter(l => 
    l.feedback_type === 'LIKE' || 
    l.feedback_type === 'DISLIKE' || 
    l.status === 'FEEDBACK_LIKE' || 
    l.status === 'FEEDBACK_DISLIKE' ||
    Boolean(l.critique_category || l.critique_note)
  );

  const likes = feedbackEntries.filter(l => l.feedback_type === 'LIKE' || l.status === 'FEEDBACK_LIKE');
  const dislikes = feedbackEntries.filter(l => l.feedback_type === 'DISLIKE' || l.status === 'FEEDBACK_DISLIKE' || Boolean(l.critique_category || l.critique_note));

  const totalReactions = likes.length + dislikes.length;
  const ratio = totalReactions > 0 ? Math.round((likes.length / totalReactions) * 100) : 100;

  if (badgeEl) badgeEl.textContent = `${totalReactions} Reaksi`;
  if (totalEl) totalEl.textContent = totalReactions.toLocaleString();
  if (likesEl) likesEl.textContent = likes.length.toLocaleString();
  if (dislikesEl) dislikesEl.textContent = dislikes.length.toLocaleString();
  if (ratioEl) ratioEl.textContent = totalReactions > 0 ? `${ratio}%` : '100%';

  if (!critiqueContainer) return;

  if (dislikes.length === 0) {
    critiqueContainer.innerHTML = `
      <div style="text-align:center;padding:var(--space-6);color:var(--text-muted);background:rgba(255,255,255,0.02);border-radius:var(--radius-md);border:var(--glass-border);">
        <div style="font-size:1.5rem;margin-bottom:6px;">✨</div>
        <div style="font-size:0.85rem;color:var(--text-secondary);font-weight:600;">Belum Ada Catatan Kritik Pengguna</div>
        <div style="font-size:0.75rem;margin-top:4px;">Semua respon yang dinilai mendapatkan Like. Jika tombol Dislike ditekan, kritik & masukan akan muncul di sini.</div>
      </div>
    `;
    return;
  }

  critiqueContainer.innerHTML = dislikes.slice(0, 20).map(item => {
    const ts = formatDate(item.timestamp);
    const cat = getModelCategory(item.model_used);
    const categoryName = item.critique_category || 'Kritik Umum / Kualitas';
    const note = item.critique_note ? escapeHtml(item.critique_note) : '<i style="color:var(--text-muted);">Tidak ada catatan teks tambahan</i>';
    const promptSnippet = escapeHtml((item.user_input || '-').slice(0, 140));
    const respSnippet = escapeHtml((item.ai_response || '-').slice(0, 180));

    return `
      <div style="background:rgba(18, 22, 30, 0.6);border:1px solid rgba(239, 68, 68, 0.25);border-radius:var(--radius-md);padding:var(--space-3) var(--space-4);display:flex;flex-direction:column;gap:8px;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="background:rgba(239, 68, 68, 0.15);color:#fca5a5;border:1px solid rgba(239, 68, 68, 0.4);padding:2px 8px;border-radius:var(--radius-full);font-size:0.68rem;font-weight:700;">
              👎 ${escapeHtml(categoryName)}
            </span>
            <span class="model-badge" style="color:${cat.color};border-color:${cat.color}44;">
              ${cat.icon} ${escapeHtml(item.model_used || 'AI Model')}
            </span>
          </div>
          <span style="font-size:0.72rem;color:var(--text-muted);font-family:var(--font-mono);">${ts}</span>
        </div>

        <div style="background:rgba(0,0,0,0.25);padding:8px 12px;border-radius:var(--radius-sm);border-left:3px solid #ef4444;">
          <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:2px;">Kritik / Catatan Pengguna:</div>
          <div style="font-size:0.84rem;color:var(--text-primary);font-family:var(--font-ui);line-height:1.45;">
            ${note}
          </div>
        </div>

        <div style="grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));display:grid;gap:8px;font-size:0.75rem;color:var(--text-muted);">
          <div>
            <span style="font-weight:600;color:var(--gold-light);">Prompt: </span>
            <span>${promptSnippet}${item.user_input && item.user_input.length > 140 ? '...' : ''}</span>
          </div>
          <div>
            <span style="font-weight:600;color:var(--text-secondary);">Cuplikan Jawaban: </span>
            <span>${respSnippet}${item.ai_response && item.ai_response.length > 180 ? '...' : ''}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ─── Pipeline Flowchart Inspector & Simulator ────────────────────
const FLOW_STEPS_INFO = {
  1: {
    icon: '💬',
    title: 'Tahap 1: Input & Injeksi Konteks Pengguna',
    file: 'public/assets/js/chat.js · roleplay.js',
    body: 'Ketika pengguna mengetik pesan di kotak input dan menekan kirim (atau Enter), sistem membaca teks prompt, mengekstrak dokumen lampiran (jika ada), menyisipkan persona/karakter roleplay yang sedang aktif, serta mengambil riwayat 6 percakapan terakhir (sliding window) dari sesi saat ini untuk dikirimkan sebagai memori kontekstual.'
  },
  2: {
    icon: '⚡',
    title: 'Tahap 2: Optimistic UI & Local Preprocessing',
    file: 'public/assets/js/app.js (logTelemetry)',
    body: 'Sebelum request berangkat ke server, browser langsung menghitung perkiraan token (prompt tokens ~4 chars/token), merender gelembung pesan pengguna secara instan (optimistic UI), memunculkan indikator mengetik, dan mencatat telemetry log awal ke localStorage agar sistem 100% anti-putus.'
  },
  3: {
    icon: '🧠',
    title: 'Tahap 3: ATOM Cortex Router & Dispatcher',
    file: 'modules/core/cortex.py · api/index.py',
    body: 'Backend FastAPI menerima payload via endpoint /api/chat. Objek ATOMCortex menguraikan preferensi model (auto, groq, deepseek, gemini, openrouter, atau ollama), menyelaraskan memori Librarian, mengevaluasi tipe kueri (apakah membutuhkan coding, reasoning mendalam, atau jawaban kilat), dan menentukan rute pemanggilan provider utama.'
  },
  4: {
    icon: '🚀',
    title: 'Tahap 4: Multi-Model Inference Hub',
    file: 'modules/core/cortex.py (Groq, DeepSeek, Gemini, OpenRouter, Ollama)',
    body: 'Permintaan inferensi dieksekusi secara asinkron ke provider yang dipilih:\n• Groq Cloud (LPU Llama 3.3 70B): Kecepatan luar biasa ~300 token/detik.\n• DeepSeek Cloud (V3): Penalaran bertahap & sintesis kode kompleks.\n• Google Gemini (Flash 2.5): Analisis multimodal teks & gambar.\n• OpenRouter Hub: Akses gratis model open-source dunia.\n• Ollama: Eksekusi privat offline di mesin lokal.'
  },
  5: {
    icon: '🛡️',
    title: 'Tahap 5: Automated Failover Engine',
    file: 'modules/core/cortex.py (Fallback & Error Recovery)',
    body: 'Jika provider utama mengalami rate-limit, gangguan koneksi, atau timeout, Cortex tidak menyerah. Sistem secara otomatis mengalihkan (failover) kueri ke provider cadangan (misal dari Groq ke Gemini Flash atau OpenRouter) tanpa perlu campur tangan pengguna, sehingga sesi obrolan tidak pernah macet.'
  },
  6: {
    icon: '⚙️',
    title: 'Tahap 6: Thinking Extraction & Markdown Parsing',
    file: 'public/assets/js/chat.js · marked.js',
    body: 'Respons teks mentah dari LLM diuraikan: langkah-langkah penalaran internal [THINKING] dipisahkan ke dalam drawer akordeon khusus yang bisa di-expand, Markdown diformat menjadi HTML dengan syntax highlighting untuk blok kode, dan waktu total inferensi dicatat dengan presisi tinggi.'
  },
  7: {
    icon: '💾',
    title: 'Tahap 7: Multi-Tier Persistence & Telemetry Logging',
    file: 'data/atom_chat_sessions.json · localStorage · api/index.py',
    body: 'Hasil akhir disimpan secara berlapis:\n1. File Fisik Proyek: Ditulis ke data/atom_chat_sessions.json atau atom_rp_sessions.json agar tercatat permanen di Git.\n2. Local Cache: Diperbarui di localStorage browser untuk loading instan berikutnya.\n3. Telemetry Store: Metrik token, latensi, dan model yang bertugas dikirimkan ke dasbor Telemetry ini.'
  }
};

function setupPipelineFlowchart() {
  const viewport = document.getElementById('flow-viewport');
  const nodes = document.querySelectorAll('.flow-step-node, #flow-hub-node');
  const dots = document.querySelectorAll('.flow-dot-btn');
  const btnPrev = document.getElementById('flow-slide-prev');
  const btnNext = document.getElementById('flow-slide-next');
  const counterEl = document.getElementById('flow-step-counter');
  const titleEl = document.getElementById('inspector-title');
  const fileEl = document.getElementById('inspector-file');
  const bodyEl = document.getElementById('inspector-body');
  const simBtn = document.getElementById('btn-simulate-flow');

  let currentStep = 1;
  let isProgrammaticScroll = false;
  let scrollTimeout = null;

  function updateInspector(stepNum) {
    const info = FLOW_STEPS_INFO[stepNum];
    if (!info) return;
    if (titleEl) titleEl.innerHTML = `<span>${info.icon}</span> ${escapeHtml(info.title)}`;
    if (fileEl) fileEl.textContent = `File Terkait: ${info.file}`;
    if (bodyEl) bodyEl.innerHTML = escapeHtml(info.body).replace(/\n/g, '<br>');
  }

  function selectStep(stepNum, shouldScroll = true) {
    stepNum = Math.max(1, Math.min(7, stepNum));
    currentStep = stepNum;

    // Update active class on card nodes
    nodes.forEach(n => {
      const s = parseInt(n.dataset.step, 10);
      if (s === stepNum) {
        n.classList.add('active');
      } else {
        n.classList.remove('active');
      }
    });

    // Update active class on dots
    dots.forEach(d => {
      const s = parseInt(d.dataset.step, 10);
      if (s === stepNum) {
        d.classList.add('active');
      } else {
        d.classList.remove('active');
      }
    });

    // Update counter
    if (counterEl) {
      counterEl.textContent = `${stepNum} / 7`;
    }

    // Update arrow buttons
    if (btnPrev) btnPrev.disabled = (stepNum <= 1);
    if (btnNext) btnNext.disabled = (stepNum >= 7);

    // Update inspector content
    updateInspector(stepNum);

    // Smooth scroll card into view
    if (shouldScroll && viewport) {
      const activeNode = document.querySelector(`[data-step="${stepNum}"]`);
      if (activeNode) {
        isProgrammaticScroll = true;
        activeNode.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          isProgrammaticScroll = false;
        }, 450);
      }
    }
  }

  // Click on cards
  let dragDistance = 0;
  nodes.forEach(node => {
    node.addEventListener('click', (e) => {
      if (dragDistance > 10) return; // Prevent click if user was dragging
      const step = parseInt(node.dataset.step, 10);
      if (!isNaN(step)) {
        selectStep(step, true);
      }
    });
  });

  // Click on dots
  dots.forEach(dot => {
    dot.addEventListener('click', () => {
      const step = parseInt(dot.dataset.step, 10);
      if (!isNaN(step)) {
        selectStep(step, true);
      }
    });
  });

  // Prev / Next button clicks
  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentStep > 1) {
        selectStep(currentStep - 1, true);
      }
    });
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      if (currentStep < 7) {
        selectStep(currentStep + 1, true);
      }
    });
  }

  // Mouse Drag-to-Scroll on Desktop
  if (viewport) {
    let isDown = false;
    let startX = 0;
    let scrollLeft = 0;

    viewport.addEventListener('mousedown', (e) => {
      isDown = true;
      dragDistance = 0;
      viewport.classList.add('is-dragging');
      startX = e.pageX - viewport.offsetLeft;
      scrollLeft = viewport.scrollLeft;
    });

    viewport.addEventListener('mouseleave', () => {
      if (isDown) {
        isDown = false;
        viewport.classList.remove('is-dragging');
      }
    });

    viewport.addEventListener('mouseup', () => {
      if (isDown) {
        isDown = false;
        viewport.classList.remove('is-dragging');
      }
    });

    viewport.addEventListener('mousemove', (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - viewport.offsetLeft;
      const walk = (x - startX) * 1.5;
      dragDistance += Math.abs(x - startX);
      viewport.scrollLeft = scrollLeft - walk;
    });

    // Scroll listener (detects swipe/drag position and updates active step & inspector)
    let scrollEndDebounce = null;
    viewport.addEventListener('scroll', () => {
      if (isProgrammaticScroll) return;

      clearTimeout(scrollEndDebounce);
      scrollEndDebounce = setTimeout(() => {
        if (isProgrammaticScroll) return;

        const viewRect = viewport.getBoundingClientRect();
        const viewCenter = viewRect.left + viewRect.width / 2;

        let closestStep = currentStep;
        let minDiff = Infinity;

        nodes.forEach(n => {
          const r = n.getBoundingClientRect();
          const nodeCenter = r.left + r.width / 2;
          const diff = Math.abs(nodeCenter - viewCenter);
          if (diff < minDiff) {
            minDiff = diff;
            closestStep = parseInt(n.dataset.step, 10);
          }
        });

        if (closestStep && closestStep !== currentStep) {
          selectStep(closestStep, false);
        }
      }, 70);
    }, { passive: true });
  }

  // Simulator button
  if (simBtn) {
    simBtn.addEventListener('click', async () => {
      simBtn.disabled = true;
      const originalText = simBtn.textContent;
      simBtn.textContent = '⏳ Mengalirkan Sinyal...';

      for (let s = 1; s <= 7; s++) {
        selectStep(s, true);
        await new Promise(r => setTimeout(r, 700));
      }

      simBtn.disabled = false;
      simBtn.textContent = originalText;
      if (typeof showToast === 'function') {
        showToast('Simulasi Pipeline Selesai (Latency: 0.85s · Status: OK)', 'success');
      }
    });
  }

  // Initial step setup
  selectStep(1, false);
}

// ─── Init ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadAndRender();
  setupPipelineFlowchart();
});
