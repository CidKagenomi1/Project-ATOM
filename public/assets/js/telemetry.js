/**
 * A.T.O.M. — Telemetry Dashboard
 * Reads from backend API /api/telemetry and renders stats
 */

async function loadTelemetry() {
  try {
    const resp = await fetch('/api/telemetry');
    if (!resp.ok) return [];
    return resp.json();
  } catch (e) {
    console.error('[ATOM] Failed to load telemetry:', e);
    return [];
  }
}

async function loadAndRender() {
  const data = await loadTelemetry();
  const noDataEl  = document.getElementById('no-data');
  const contentEl = document.getElementById('telem-content');

  if (!data || data.length === 0) {
    if (noDataEl)  noDataEl.style.display  = 'block';
    if (contentEl) contentEl.style.display = 'none';
    return;
  }

  if (noDataEl)  noDataEl.style.display  = 'none';
  if (contentEl) contentEl.style.display = 'block';

  // ─── Metrics ───────────────────────────────────────────
  const total       = data.length;
  const avgTime     = data.reduce((s, d) => s + (parseFloat(d.response_time) || 0), 0) / total;
  const successRate = Math.round((data.filter(d => d.status === 'SUCCESS' || d.status === 'FAILOVER').length / total) * 100);

  // Top model
  const modelCount = {};
  data.forEach(d => { modelCount[d.model_used] = (modelCount[d.model_used] || 0) + 1; });
  const topModel = Object.entries(modelCount).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';

  setText('m-total',   total.toLocaleString());
  setText('m-avg',     avgTime.toFixed(2) + 's');
  setText('m-success', successRate + '%');
  setText('m-top',     topModel.split('-')[0] || topModel);

  // ─── Response Time ─────────────────────────────────────
  const times   = data.map(d => parseFloat(d.response_time) || 0);
  const fastest = Math.min(...times);
  const slowest = Math.max(...times);
  const avgT    = times.reduce((a, b) => a + b, 0) / times.length;

  setText('t-fastest', fastest.toFixed(2) + 's');
  setText('t-avg',     avgT.toFixed(2) + 's');
  setText('t-slowest', slowest.toFixed(2) + 's');

  // ─── Model Usage List ──────────────────────────────────
  const usageEl = document.getElementById('model-usage-list');
  if (usageEl) {
    const sortedModels = Object.entries(modelCount).sort((a, b) => b[1] - a[1]);
    usageEl.innerHTML = sortedModels.map(([model, count]) => {
      const pct = Math.round((count / total) * 100);
      const color = model.toLowerCase().includes('groq')   ? '#a78bfa'
                  : model.toLowerCase().includes('gemini') ? '#60a5fa'
                  : model.toLowerCase().includes('llama')  ? '#fbbf24'
                  : '#8B949E';
      return `
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span style="font-size:0.8rem;color:var(--text-primary);font-weight:600;">${escapeHtml(model)}</span>
            <span style="font-size:0.75rem;color:var(--text-muted);">${count} (${pct}%)</span>
          </div>
          <div style="height:6px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;">
            <div style="width:${pct}%;height:100%;background:${color};border-radius:3px;transition:width 0.5s ease;"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  // ─── Model Time Bars ───────────────────────────────────
  const modelTimesEl = document.getElementById('model-time-bars');
  if (modelTimesEl) {
    const modelGroups = {};
    data.forEach(d => {
      if (!modelGroups[d.model_used]) modelGroups[d.model_used] = [];
      modelGroups[d.model_used].push(parseFloat(d.response_time) || 0);
    });
    const modelAvgs = Object.entries(modelGroups)
      .map(([m, ts]) => [m, ts.reduce((a, b) => a + b, 0) / ts.length])
      .sort((a, b) => a[1] - b[1]);
    const maxAvg = Math.max(...modelAvgs.map(([, v]) => v));

    modelTimesEl.innerHTML = modelAvgs.map(([model, avg]) => {
      const pct = Math.round((avg / maxAvg) * 100);
      const color = model.toLowerCase().includes('groq')   ? '#a78bfa'
                  : model.toLowerCase().includes('gemini') ? '#60a5fa'
                  : model.toLowerCase().includes('llama')  ? '#fbbf24'
                  : '#8B949E';
      return `
        <div>
          <div style="display:flex;justify-content:space-between;margin-bottom:2px;font-size:0.72rem;">
            <span style="color:var(--text-secondary);">${escapeHtml(model.split('-').slice(0, 2).join('-'))}</span>
            <span style="color:${color};font-weight:600;">${avg.toFixed(2)}s</span>
          </div>
          <div style="height:4px;background:var(--bg-elevated);border-radius:2px;overflow:hidden;">
            <div style="width:${pct}%;height:100%;background:${color};border-radius:2px;"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  // ─── Activity Log ──────────────────────────────────────
  const tbody = document.getElementById('activity-tbody');
  if (tbody) {
    const recent = [...data].reverse().slice(0, 20);
    tbody.innerHTML = recent.map((row, idx) => {
      const ts  = row.timestamp ? row.timestamp : '-';
      const dur = parseFloat(row.response_time).toFixed(2) + 's';
      const statusColor = row.status === 'SUCCESS' ? 'var(--success)' : row.status === 'FAILOVER' ? 'var(--warning)' : 'var(--error)';
      const modelClass  = (row.model_used || '').toLowerCase().includes('groq') ? 'groq' : (row.model_used || '').toLowerCase().includes('gemini') ? 'gemini' : '';
      const rowId = `telem-row-${idx}`;
      return `
        <tr onclick="toggleRowDetails('${rowId}')" style="cursor:pointer;" class="telem-header-row">
          <td style="white-space:nowrap;">${escapeHtml(ts)}</td>
          <td><span class="model-badge ${modelClass}">${escapeHtml(row.model_used || '-')}</span></td>
          <td style="font-family:var(--font-mono);">${dur}</td>
          <td><span style="color:${statusColor};font-size:0.75rem;font-weight:600;">${escapeHtml(row.status || '-')}</span></td>
          <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="Click to view conversation details">${escapeHtml(row.user_input || '-')}</td>
        </tr>
        <tr id="${rowId}-details" style="display:none; background: rgba(0, 0, 0, 0.2);">
          <td colspan="5" style="padding:var(--space-4); border-bottom:var(--glass-border);">
            <div style="display:flex; flex-direction:column; gap:var(--space-3); text-align:left;">
              <div>
                <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px; font-weight:700;">Full Prompt</div>
                <div style="font-size:0.85rem; color:var(--text-primary); white-space:pre-wrap; background:rgba(255,255,255,0.01); padding:var(--space-3); border-radius:var(--radius-md); border:var(--glass-border); font-family:var(--font-chat);">${escapeHtml(row.user_input || '-')}</div>
              </div>
              <div>
                <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px; font-weight:700;">AI Response</div>
                <div style="font-size:0.85rem; color:var(--text-primary); white-space:pre-wrap; background:rgba(255,255,255,0.01); padding:var(--space-3); border-radius:var(--radius-md); border:var(--glass-border); font-family:var(--font-chat);">${escapeHtml(row.ai_response || '(No AI response was captured for this entry)')}</div>
              </div>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  }
}

// Expandable telemetry row handler
window.toggleRowDetails = function(rowId) {
  const detailsEl = document.getElementById(`${rowId}-details`);
  if (detailsEl) {
    const isHidden = detailsEl.style.display === 'none';
    detailsEl.style.display = isHidden ? 'table-row' : 'none';
  }
};

// ─── Clear Telemetry ───────────────────────────────────────
document.getElementById('btn-clear-telemetry')?.addEventListener('click', async () => {
  if (!confirm('Hapus semua data telemetri?')) return;
  const resp = await fetch('/api/telemetry', { method: 'DELETE' });
  if (resp.ok) {
    showToast('Telemetri dihapus', 'info');
    await loadAndRender();
  } else {
    showToast('Gagal menghapus telemetri', 'error');
  }
});

// ─── Helper ───────────────────────────────────────────────
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ─── Init ─────────────────────────────────────────────────
loadAndRender();
