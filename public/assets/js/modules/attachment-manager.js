// ─── ATOM Shared Module: Universal Attachment Manager ───────────────
(function(window) {
  'use strict';

  async function parseFile(file) {
    const isImage = file.type?.startsWith('image/');
    const ext = (file.name || '').split('.').pop().toLowerCase();
    const isPdf = ext === 'pdf' || file.type === 'application/pdf';
    const isDocx = ext === 'docx' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    
    const maxSize = isImage ? 15 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > maxSize) {
      if (typeof showToast === 'function') {
        showToast(`File "${file.name}" melebihi batas (${isImage ? '15MB' : '10MB'})`, 'warning');
      }
      return null;
    }

    if (typeof showToast === 'function') {
      showToast(`Memproses ${file.name}...`, 'info');
    }

    // 1. Image
    if (isImage) {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          resolve({ name: file.name || 'image.png', type: file.type || 'image/png', content: e.target.result });
        };
        reader.readAsDataURL(file);
      });
    }

    // 2. PDF Document
    if (isPdf) {
      try {
        if (window.pdfjsLib) {
          window.pdfjsLib.GlobalWorkerOptions.workerSrc =
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
          const arrayBuffer = await file.arrayBuffer();
          const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
          let fullText = `[DOKUMEN PDF: ${file.name} - Total ${pdf.numPages} Halaman]\n\n`;
          for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const pageStrings = textContent.items.map(item => item.str).join(' ');
            fullText += `--- Halaman ${i} ---\n${pageStrings}\n\n`;
          }
          if (typeof showToast === 'function') {
            showToast(`Dokumen PDF "${file.name}" diuraikan (${pdf.numPages} hal)`, 'success');
          }
          return { name: file.name, type: 'application/pdf', content: fullText };
        }
      } catch (err) {
        console.warn('[PDF PARSE ERROR]', err);
      }
      // Fallback text reader
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve({ name: file.name, type: 'application/pdf', content: e.target.result });
        reader.readAsText(file);
      });
    }

    // 3. Word Document (DOCX)
    if (isDocx) {
      try {
        if (window.mammoth) {
          const arrayBuffer = await file.arrayBuffer();
          const result = await window.mammoth.extractRawText({ arrayBuffer });
          const text = `[DOKUMEN WORD: ${file.name}]\n\n${result.value}`;
          if (typeof showToast === 'function') {
            showToast(`Dokumen Word "${file.name}" diuraikan`, 'success');
          }
          return { name: file.name, type: 'application/docx', content: text };
        }
      } catch (err) {
        console.warn('[DOCX PARSE ERROR]', err);
      }
    }

    // 4. Plain Text / Code Fallback
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (typeof showToast === 'function') {
          showToast(`File teks "${file.name}" terlampir`, 'success');
        }
        resolve({ name: file.name, type: file.type || 'text/plain', content: e.target.result });
      };
      reader.readAsText(file);
    });
  }

  function renderAttachmentPill(file, index, removeHandlerName) {
    const isImg = file.type?.startsWith('image/');
    const previewHtml = isImg
      ? `<img src="${file.content}" style="width: 24px; height: 24px; border-radius: 4px; object-fit: cover;" />`
      : `<span style="font-size: 14px;">📄</span>`;

    return `
      <div class="attachment-pill" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 4px 8px; font-size: 11px; position: relative;">
        ${previewHtml}
        <span style="max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-primary);">${file.name}</span>
        <button onclick="${removeHandlerName}(${index})" class="attachment-remove-btn" title="Hapus file" style="background: #ef4444; color: white; border: none; border-radius: 50%; width: 14px; height: 14px; font-size: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; line-height: 1; margin-left: 4px;">×</button>
      </div>
    `;
  }

  window.ATOM_AttachmentManager = {
    parseFile,
    renderAttachmentPill
  };
})(window);

