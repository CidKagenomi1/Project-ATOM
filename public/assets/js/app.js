/**
 * A.T.O.M. — App Utilities & Shared Logic
 * Sidebar toggle, toast notifications, navigation
 */

// ─── Sidebar Toggle (Mobile) ─────────────────────────────
const sidebar = document.getElementById('app-sidebar');
const overlay = document.getElementById('sidebar-overlay');
const menuBtn = document.getElementById('mobile-menu-btn');

function openSidebar() {
  sidebar?.classList.add('open');
  overlay?.classList.add('visible');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  sidebar?.classList.remove('open');
  overlay?.classList.remove('visible');
  document.body.style.overflow = '';
}

menuBtn?.addEventListener('click', openSidebar);
overlay?.addEventListener('click', closeSidebar);

// Close on nav link click (mobile)
document.querySelectorAll('.sidebar-nav a').forEach(link => {
  link.addEventListener('click', closeSidebar);
});


// ─── Toast Notifications ────────────────────────────────
const toastContainer = document.getElementById('toast-container');

function showToast(message, type = 'info', duration = 3500) {
  if (!toastContainer) return;

  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span style="font-size:1.1rem;flex-shrink:0;">${icons[type] || 'ℹ️'}</span>
    <span style="flex:1;font-size:0.85rem;color:var(--text-primary);">${message}</span>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1rem;padding:0;line-height:1;">×</button>
  `;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Global toast function
window.showToast = showToast;


// ─── Telemetry Logger (localStorage) ────────────────────
function logTelemetry(entry) {
  try {
    const key = 'atom_telemetry';
    const existing = JSON.parse(localStorage.getItem(key) || '[]');
    existing.push({
      timestamp: new Date().toISOString(),
      ...entry
    });
    // Keep last 500 entries
    if (existing.length > 500) existing.splice(0, existing.length - 500);
    localStorage.setItem(key, JSON.stringify(existing));
  } catch (e) {
    console.warn('[ATOM] Telemetry log failed:', e);
  }
}

window.logTelemetry = logTelemetry;


// ─── Auto-resize Textarea ────────────────────────────────
function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
}

document.querySelectorAll('textarea').forEach(ta => {
  ta.addEventListener('input', () => autoResize(ta));
});


// ─── Smooth Scroll to Bottom ────────────────────────────
function scrollToBottom(container) {
  if (!container) return;
  container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}
window.scrollToBottom = scrollToBottom;


// ─── Markdown Renderer (via marked.js) ──────────────────
function renderMarkdown(text) {
  if (typeof marked === 'undefined') return escapeHtml(text).replace(/\n/g, '<br>');
  try {
    marked.setOptions({
      gfm: true,
      breaks: true,
      sanitize: false,
    });
    return marked.parse(text);
  } catch {
    return escapeHtml(text).replace(/\n/g, '<br>');
  }
}
window.renderMarkdown = renderMarkdown;

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;


// ─── Status Indicators ─────────────────────────────────
function updateStatusIndicators() {
  // We assume Groq and Gemini are available (cloud keys set on Vercel)
  // We can ping a lightweight check endpoint later
  const dotGroq   = document.getElementById('dot-groq');
  const dotGemini = document.getElementById('dot-gemini');
  const pillGroq   = document.getElementById('pill-groq');
  const pillGemini = document.getElementById('pill-gemini');

  // Optimistically mark as online (will update on first request)
  if (dotGroq)   dotGroq.className   = 'status-dot online';
  if (dotGemini) dotGemini.className = 'status-dot online';
  if (pillGroq)   pillGroq.className   = 'status-pill online';
  if (pillGemini) pillGemini.className = 'status-pill online';
}

updateStatusIndicators();

console.log('%c⚛️ A.T.O.M. v4.0 CORTEX INITIALIZED', 'color:#C9A227;font-size:14px;font-weight:bold;');
