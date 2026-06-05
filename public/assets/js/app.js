/**
 * A.T.O.M. — App Utilities & Shared Logic
 * Sidebar toggle, toast notifications, navigation
 */

// ─── Sidebar Toggle (Desktop & Mobile) ────────────────────
const sidebar = document.getElementById('app-sidebar');
const overlay = document.getElementById('sidebar-overlay');
const menuBtn = document.getElementById('mobile-menu-btn');
const appMain = document.querySelector('.app-main');

function toggleSidebar() {
  const isMobile = window.innerWidth <= 768;
  if (isMobile) {
    sidebar?.classList.toggle('open');
    overlay?.classList.toggle('visible');
    if (sidebar?.classList.contains('open')) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  } else {
    sidebar?.classList.toggle('collapsed');
    appMain?.classList.toggle('sidebar-collapsed');
    
    // Save state to localStorage
    const isCollapsed = sidebar?.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isCollapsed ? 'true' : 'false');
  }
}

function closeSidebar() {
  sidebar?.classList.remove('open');
  overlay?.classList.remove('visible');
  document.body.style.overflow = '';
}

menuBtn?.addEventListener('click', toggleSidebar);
overlay?.addEventListener('click', closeSidebar);

// Close on nav link click (mobile only)
document.querySelectorAll('.sidebar-nav a').forEach(link => {
  link.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
      closeSidebar();
    }
  });
});

// Restore sidebar state on load & inject close button
document.addEventListener('DOMContentLoaded', () => {
  // Restore sidebar state
  if (window.innerWidth > 768) {
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
      sidebar?.classList.add('collapsed');
      appMain?.classList.add('sidebar-collapsed');
    }
  }

  // Inject close button in sidebar header on desktop
  const sidebarHeader = document.querySelector('.sidebar-header');
  if (sidebarHeader) {
    const closeBtn = document.createElement('button');
    closeBtn.className = 'sidebar-close-btn';
    closeBtn.innerHTML = '◀';
    closeBtn.title = 'Collapse Sidebar';
    closeBtn.type = 'button';
    closeBtn.addEventListener('click', toggleSidebar);
    sidebarHeader.appendChild(closeBtn);
  }

  // Initialize Vapor Chamber particle system if canvas is present
  if (document.getElementById('vapor-canvas') && window.VaporChamber) {
    window.vaporChamberInstance = new window.VaporChamber('vapor-canvas');
  }
});

// ─── Flashlight Cursor Glow ──────────────────────────────
const cursorGlow = document.createElement('div');
cursorGlow.className = 'cursor-glow';
document.body.appendChild(cursorGlow);

document.addEventListener('mousemove', (e) => {
  cursorGlow.style.setProperty('--mouse-x', `${e.clientX}px`);
  cursorGlow.style.setProperty('--mouse-y', `${e.clientY}px`);
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
async function logTelemetry(entry) {
  try {
    await fetch('/api/telemetry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry)
    });
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
async function updateStatusIndicators() {
  try {
    const resp = await fetch('/api/status');
    if (!resp.ok) return;
    const status = await resp.json();

    const services = ['local', 'groq', 'crew', 'gemini'];
    services.forEach(srv => {
      const isOnline = status[srv] === 'online';
      
      const dot = document.getElementById(`dot-${srv}`);
      if (dot) {
        dot.className = `status-dot ${isOnline ? 'online' : 'offline'}`;
      }
      
      const pill = document.getElementById(`pill-${srv}`);
      if (pill) {
        pill.className = `status-pill ${isOnline ? 'online' : 'offline'}`;
      }
    });
  } catch (e) {
    console.warn('[ATOM] Failed to fetch dynamic status:', e);
  }
}

updateStatusIndicators();

console.log('%c⚛️ A.T.O.M. v4.0 CORTEX INITIALIZED', 'color:#C9A227;font-size:14px;font-weight:bold;');
