/**
 * A.T.O.M. — Mobile UI/UX Handler
 * Optimizes transitions, grid systems, compacts dropdowns,
 * and handles mobile-specific layouts dynamically.
 */

class MobileUIHandler {
  constructor() {
    this.isMobile = false;
    this.modelSelectWrapper = document.querySelector('.model-select-wrapper');
    this.inputRow = document.getElementById('input-row');
    this.originalParent = this.modelSelectWrapper ? this.modelSelectWrapper.parentElement : null;
    this.originalNextSibling = this.modelSelectWrapper ? this.modelSelectWrapper.nextSibling : null;
    
    this.init();
  }

  init() {
    this.checkViewport();
    window.addEventListener('resize', () => this.checkViewport());
    this.setupSwipeGestures();
    this.setupTouchEffects();
    
    // Watch model select changes to update compact label on mobile
    const nativeSelect = document.getElementById('model-select');
    if (nativeSelect) {
      nativeSelect.addEventListener('change', () => this.updateCompactLabel());
    }
    
    // Initialize compact label after a brief delay to ensure custom select trigger is built
    setTimeout(() => this.updateCompactLabel(), 100);
  }

  checkViewport() {
    const wasMobile = this.isMobile;
    this.isMobile = window.innerWidth <= 768;

    if (this.isMobile && !wasMobile) {
      this.applyMobileOptimizations();
    } else if (!this.isMobile && wasMobile) {
      this.revertToDesktop();
    }
  }

  applyMobileOptimizations() {
    console.log('[MobileUI] Applying mobile enhancements...');
    document.body.classList.add('mobile-mode');

    // 1. Move Model Select inside Chat Bar for maximum vertical space
    if (this.modelSelectWrapper && this.inputRow) {
      this.inputRow.insertBefore(this.modelSelectWrapper, this.inputRow.firstChild);
      this.updateCompactLabel();
    }

    // 2. Enhance Grid Density & Animations
    const bubbleGrid = document.getElementById('bubble-grid');
    if (bubbleGrid) {
      bubbleGrid.classList.add('dense-grid');
    }
  }

  revertToDesktop() {
    console.log('[MobileUI] Reverting to desktop view...');
    document.body.classList.remove('mobile-mode');

    // 1. Restore Model Select to its original position
    if (this.modelSelectWrapper && this.originalParent) {
      if (this.originalNextSibling) {
        this.originalParent.insertBefore(this.modelSelectWrapper, this.originalNextSibling);
      } else {
        this.originalParent.appendChild(this.modelSelectWrapper);
      }
      this.updateCompactLabel();
    }

    const bubbleGrid = document.getElementById('bubble-grid');
    if (bubbleGrid) {
      bubbleGrid.classList.remove('dense-grid');
    }
  }

  updateCompactLabel() {
    const trigger = document.querySelector('.custom-select-trigger');
    const select = document.getElementById('model-select');
    if (!trigger || !select) return;

    const selectedOption = select.options[select.selectedIndex];
    if (!selectedOption) return;

    const fullText = selectedOption.textContent;

    if (this.isMobile) {
      // Extract emoji/icon or first symbol/character
      const emojiMatch = fullText.match(/^[\p{Emoji}\u2600-\u27BF]/u);
      const emoji = emojiMatch ? emojiMatch[0] : '';
      
      // Map icons to short abbreviations
      let label = emoji;
      if (fullText.toLowerCase().includes('groq')) {
        label = '⚡';
      } else if (fullText.toLowerCase().includes('gemini')) {
        label = '♊';
      } else if (fullText.toLowerCase().includes('deepseek')) {
        label = '🐳';
      } else if (fullText.toLowerCase().includes('ollama')) {
        label = '🧠';
      } else if (fullText.toLowerCase().includes('openrouter')) {
        label = '🌐';
      } else if (fullText.toLowerCase().includes('auto')) {
        label = '🤖';
      }
      
      // If we couldn't match a clean emoji, use first 2 letters
      if (!label) {
        label = fullText.trim().substring(0, 2).toUpperCase();
      }

      trigger.innerHTML = `<span class="mobile-logo-badge">${label}</span>`;
      trigger.classList.add('compact-mobile');
    } else {
      trigger.textContent = fullText;
      trigger.classList.remove('compact-mobile');
    }
  }

  setupSwipeGestures() {
    let startX = 0;
    let startY = 0;

    document.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      if (!this.isMobile) return;

      const diffX = e.changedTouches[0].clientX - startX;
      const diffY = e.changedTouches[0].clientY - startY;

      // Ensure horizontal swipe
      if (Math.abs(diffX) > Math.abs(diffY) * 1.5 && Math.abs(diffX) > 80) {
        const sidebar = document.getElementById('app-sidebar');
        const isSidebarOpen = sidebar && sidebar.classList.contains('open');

        if (diffX > 0 && !isSidebarOpen && startX < 50) {
          // Swipe right from edge -> open sidebar
          window.toggleSidebar && window.toggleSidebar();
        } else if (diffX < 0 && isSidebarOpen) {
          // Swipe left -> close sidebar
          window.toggleSidebar && window.toggleSidebar();
        }
      }
    }, { passive: true });
  }

  setupTouchEffects() {
    // Add lightweight active ripple/shrink effect on touch for buttons
    document.addEventListener('touchstart', (e) => {
      const btn = e.target.closest('.btn, .suggestion-chip, .note-item, .bubble-card');
      if (btn) {
        btn.classList.add('touch-active');
      }
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      const btn = e.target.closest('.btn, .suggestion-chip, .note-item, .bubble-card');
      if (btn) {
        btn.classList.remove('touch-active');
      }
    }, { passive: true });
  }
}

// Instantiate on DOM load
document.addEventListener('DOMContentLoaded', () => {
  window.mobileUI = new MobileUIHandler();
});
