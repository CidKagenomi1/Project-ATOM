// ─── ATOM Shared Module: Universal Attachment Manager ───────────────
(function(window) {
  'use strict';

  const CODE_LANG_MAP = {
    py: 'python',
    js: 'javascript',
    ts: 'typescript',
    sql: 'sql',
    yaml: 'yaml',
    yml: 'yaml',
    xml: 'xml',
    css: 'css',
    sh: 'bash',
    bat: 'bat',
    ps1: 'powershell',
    java: 'java',
    go: 'go',
    rs: 'rust',
    c: 'c',
    cpp: 'cpp',
    php: 'php',
    rb: 'ruby'
  };

  function getCleanTitle(filename) {
    const base = (filename || 'Dokumen Baru').replace(/\.[^/.]+$/, '');
    const cleaned = base.replace(/[_-]+/g, ' ').trim();
    return (cleaned || filename || 'Dokumen Baru').slice(0, 80);
  }

  function countWords(text) {
    if (!text) return 0;
    return String(text).trim().split(/\s+/).filter(Boolean).length;
  }

  function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error(`Gagal membaca file ${file.name}`));
      reader.readAsDataURL(file);
    });
  }

  function readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result || '');
      reader.onerror = () => reject(new Error(`Gagal membaca teks ${file.name}`));
      reader.readAsText(file);
    });
  }

  function convertCsvTextToMarkdown(csvText, delimiter = ',') {
    const lines = String(csvText || '').replace(/\r\n/g, '\n').split('\n').filter(l => l.trim().length > 0);
    if (lines.length === 0) return '_(CSV kosong)_';

    const sample = lines[0] || '';
    if (delimiter === ',' && (sample.match(/;/g) || []).length > (sample.match(/,/g) || []).length) {
      delimiter = ';';
    }

    const parseRow = (line) => {
      const cells = [];
      let cur = '';
      let inQuotes = false;
      for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (ch === '"') {
          if (inQuotes && line[i + 1] === '"') {
            cur += '"';
            i++;
          } else {
            inQuotes = !inQuotes;
          }
        } else if (ch === delimiter && !inQuotes) {
          cells.push(cur.trim());
          cur = '';
        } else {
          cur += ch;
        }
      }
      cells.push(cur.trim());
      return cells.map(c => c.replace(/\s+/g, ' ').replace(/\|/g, '\\|'));
    };

    const maxRows = 150;
    const rows = lines.slice(0, maxRows).map(parseRow);
    const colCount = Math.max(...rows.map(r => r.length));
    const norm = rows.map(r => Array.from({ length: colCount }, (_, i) => r[i] || ''));

    const header = `| ${norm[0].join(' | ')} |`;
    const divider = `| ${Array(colCount).fill('---').join(' | ')} |`;
    const body = norm.slice(1).map(r => `| ${r.join(' | ')} |`);
    const out = [header, divider, ...body];
    if (lines.length > maxRows) {
      out.push('', `*(Menampilkan ${maxRows} dari ${lines.length} baris pertama)*`);
    }
    return out.join('\n');
  }

  function wrapDocumentMarkdown(filename, ext, bodyText) {
    const cleanBody = String(bodyText || '').trim() || '_(Dokumen kosong)_';
    const words = countWords(cleanBody);
    return `> 📄 **Dokumen Terimpor:** \`${filename}\` · **Format:** ${(ext || 'txt').toUpperCase()} · **Estimasi:** ${words.toLocaleString('id-ID')} kata\n\n---\n\n${cleanBody}`;
  }

  async function callBackendFileParser(file, createNote = false) {
    const dataUrl = await readFileAsDataURL(file);
    const resp = await fetch('/api/notes/import_file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: file.name || 'document.txt',
        content: dataUrl,
        mime_type: file.type || '',
        create_note: Boolean(createNote)
      })
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || err.error || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    return data.parsed ? data : { parsed: data, note: null };
  }

  async function parsePdfWithBrowser(file) {
    if (!window.pdfjsLib) return null;
    window.pdfjsLib.GlobalWorkerOptions.workerSrc =
      'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

    const arrayBuffer = await file.arrayBuffer();
    const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    const pages = [];
    let rawCharCount = 0;

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      let pageText = '';
      for (const item of (textContent.items || [])) {
        const str = item.str || '';
        pageText += str + (item.hasEOL ? '\n' : ' ');
      }
      const cleanedPage = pageText
        .replace(/[ \t]+\n/g, '\n')
        .replace(/\n{3,}/g, '\n\n')
        .trim();
      rawCharCount += cleanedPage.length;
      pages.push(`### 📄 Halaman ${i}\n\n${cleanedPage || '_(Halaman tidak memiliki teks terbaca)_'}`);
    }

    if (rawCharCount < 10) {
      return null; // Allow backend PDF parser fallback if client extraction got almost nothing
    }

    return {
      numPages: pdf.numPages,
      body: pages.join('\n\n')
    };
  }

  async function parseFile(file, options = {}) {
    if (!file) return null;
    const isImage = file.type?.startsWith('image/');
    const filename = file.name || 'document.txt';
    const ext = (filename.split('.').pop() || 'txt').toLowerCase();
    const isPdf = ext === 'pdf' || file.type === 'application/pdf';
    const isDocx = ext === 'docx' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    const isSpreadsheetOrDeck = ['xlsx', 'xlsm', 'pptx'].includes(ext);
    const isTabularText = ['csv', 'tsv'].includes(ext);
    const silent = Boolean(options.silent);

    const maxSize = isImage ? 15 * 1024 * 1024 : 20 * 1024 * 1024;
    if (file.size > maxSize) {
      if (typeof showToast === 'function') {
        showToast(`File "${filename}" melebihi batas (${isImage ? '15MB' : '20MB'})`, 'warning');
      }
      return null;
    }

    if (!silent && typeof showToast === 'function') {
      showToast(`Memproses ${filename}...`, 'info');
    }

    // 1. Image
    if (isImage) {
      const content = await readFileAsDataURL(file);
      return {
        name: filename,
        title: getCleanTitle(filename),
        type: file.type || 'image/png',
        ext,
        content,
        markdown: `![${filename}](${content})`,
        tags: ['imported', 'image'],
        wordCount: 0
      };
    }

    // 2. Office & Structured Documents (DOCX, XLSX, PPTX, CSV/TSV) -> Backend rich Markdown parser first
    if (isDocx || isSpreadsheetOrDeck || isTabularText) {
      try {
        const res = await callBackendFileParser(file, false);
        const p = res.parsed;
        if (p && (p.markdown || p.raw_text)) {
          if (!silent && typeof showToast === 'function') {
            showToast(`Dokumen "${filename}" berhasil diuraikan (${p.word_count || countWords(p.raw_text)} kata)`, 'success');
          }
          return {
            name: p.filename || filename,
            title: p.title || getCleanTitle(filename),
            type: file.type || `application/${ext}`,
            ext: p.ext || ext,
            content: p.raw_text || p.markdown,
            markdown: p.markdown,
            tags: p.tags || ['imported', ext],
            wordCount: p.word_count || countWords(p.raw_text)
          };
        }
      } catch (err) {
        console.warn('[BACKEND PARSE FALLBACK]', err);
      }

      // Client-side DOCX fallback via Mammoth.js
      if (isDocx && window.mammoth) {
        try {
          const arrayBuffer = await file.arrayBuffer();
          const result = await window.mammoth.extractRawText({ arrayBuffer });
          const body = `[DOKUMEN WORD: ${filename}]\n\n${result.value || ''}`;
          const md = wrapDocumentMarkdown(filename, ext, result.value || '');
          if (!silent && typeof showToast === 'function') {
            showToast(`Dokumen Word "${filename}" diuraikan`, 'success');
          }
          return {
            name: filename,
            title: getCleanTitle(filename),
            type: 'application/docx',
            ext,
            content: body,
            markdown: md,
            tags: ['imported', 'docx'],
            wordCount: countWords(result.value)
          };
        } catch (mErr) {
          console.warn('[MAMMOTH FALLBACK ERROR]', mErr);
        }
      }

      // Client-side CSV / TSV fallback
      if (isTabularText) {
        const raw = await readFileAsText(file);
        const tableMd = convertCsvTextToMarkdown(raw, ext === 'tsv' ? '\t' : ',');
        const md = wrapDocumentMarkdown(filename, ext, tableMd);
        if (!silent && typeof showToast === 'function') {
          showToast(`Tabel "${filename}" diuraikan`, 'success');
        }
        return {
          name: filename,
          title: getCleanTitle(filename),
          type: file.type || 'text/csv',
          ext,
          content: tableMd,
          markdown: md,
          tags: ['imported', ext],
          wordCount: countWords(raw)
        };
      }

      throw new Error(`Format .${ext} membutuhkan parser server yang aktif.`);
    }

    // 3. PDF Document -> Client PDF.js first, Backend parser fallback
    if (isPdf) {
      try {
        const clientPdf = await parsePdfWithBrowser(file);
        if (clientPdf && clientPdf.body) {
          const content = `[DOKUMEN PDF: ${filename} - Total ${clientPdf.numPages} Halaman]\n\n${clientPdf.body}`;
          const words = countWords(clientPdf.body);
          const md = `> 📄 **Dokumen Terimpor:** \`${filename}\` · **Format:** PDF · **Halaman:** ${clientPdf.numPages} · **Estimasi:** ${words.toLocaleString('id-ID')} kata\n\n---\n\n${clientPdf.body}`;
          if (!silent && typeof showToast === 'function') {
            showToast(`Dokumen PDF "${filename}" diuraikan (${clientPdf.numPages} hal)`, 'success');
          }
          return {
            name: filename,
            title: getCleanTitle(filename),
            type: 'application/pdf',
            ext: 'pdf',
            content,
            markdown: md,
            tags: ['imported', 'pdf'],
            wordCount: words
          };
        }
      } catch (pdfErr) {
        console.warn('[PDF.JS PARSE ERROR]', pdfErr);
      }

      // Fallback to Backend Python PDF parser
      try {
        const res = await callBackendFileParser(file, false);
        const p = res.parsed;
        if (p && (p.markdown || p.raw_text)) {
          if (!silent && typeof showToast === 'function') {
            showToast(`Dokumen PDF "${filename}" diuraikan via server`, 'success');
          }
          return {
            name: p.filename || filename,
            title: p.title || getCleanTitle(filename),
            type: 'application/pdf',
            ext: 'pdf',
            content: p.raw_text || p.markdown,
            markdown: p.markdown,
            tags: p.tags || ['imported', 'pdf'],
            wordCount: p.word_count || countWords(p.raw_text)
          };
        }
      } catch (srvErr) {
        console.warn('[PDF BACKEND PARSE ERROR]', srvErr);
        throw srvErr;
      }
    }

    // 4. Plain Text / Markdown / JSON / Code Fallback
    const rawText = await readFileAsText(file);
    let formattedBody = rawText;
    if (ext === 'json') {
      try {
        const pretty = JSON.stringify(JSON.parse(rawText), null, 2);
        formattedBody = `\`\`\`json\n${pretty}\n\`\`\``;
      } catch {
        formattedBody = `\`\`\`json\n${rawText}\n\`\`\``;
      }
    } else if (CODE_LANG_MAP[ext]) {
      formattedBody = `\`\`\`${CODE_LANG_MAP[ext]}\n${rawText}\n\`\`\``;
    }

    const md = (ext === 'md' || ext === 'markdown')
      ? rawText
      : wrapDocumentMarkdown(filename, ext, formattedBody);

    if (!silent && typeof showToast === 'function') {
      showToast(`File "${filename}" berhasil dibaca`, 'success');
    }

    return {
      name: filename,
      title: getCleanTitle(filename),
      type: file.type || 'text/plain',
      ext,
      content: rawText,
      markdown: md,
      tags: ['imported', ext],
      wordCount: countWords(rawText)
    };
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
    callBackendFileParser,
    renderAttachmentPill
  };
})(window);

