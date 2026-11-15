"""
A.T.O.M. Smart Notes - Multi-Format Document Importer
Parses uploaded documents (.pdf, .docx, .xlsx, .pptx, .csv, .tsv, .md, .txt, .json, .html, code files)
into structured Markdown ready for Crew Notes viewing and Co-Pilot AI analysis.
"""

import base64
import csv
import io
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any, Dict, List, Tuple


BINARY_EXTENSIONS = {"pdf", "docx", "xlsx", "xlsm", "pptx"}

CODE_LANG_MAP = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "sql": "sql",
    "yaml": "yaml",
    "yml": "yaml",
    "xml": "xml",
    "css": "css",
    "sh": "bash",
    "bat": "bat",
    "ps1": "powershell",
    "java": "java",
    "go": "go",
    "rs": "rust",
    "c": "c",
    "cpp": "cpp",
    "php": "php",
    "rb": "ruby",
}

MAX_TABLE_ROWS = 150


class _FallbackHTMLTextExtractor(HTMLParser):
    """Minimal stdlib HTML-to-text parser used if BeautifulSoup is unavailable."""

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Any]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1
        elif tag.lower() in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data.strip() + " ")

    def get_text(self) -> str:
        raw = "".join(self._chunks)
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return "\n\n".join(lines)


def _decode_raw_payload(raw_content: str, ext: str) -> bytes:
    """Decode Data URL, base64 payload, or plain UTF-8 string into raw bytes."""
    if not raw_content:
        return b""

    payload = raw_content.strip()
    if payload.startswith("data:"):
        _, _, b64_part = payload.partition(",")
        return base64.b64decode(b64_part, validate=False)

    if ext in BINARY_EXTENSIONS:
        try:
            return base64.b64decode(payload, validate=True)
        except Exception:
            try:
                return base64.b64decode(payload, validate=False)
            except Exception:
                return raw_content.encode("utf-8", errors="ignore")

    return raw_content.encode("utf-8", errors="replace")


def _decode_text_bytes(data: bytes) -> str:
    """Decode text bytes trying UTF-8 (with BOM) first, then common Windows encodings."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _clean_cell(value: Any) -> str:
    """Normalize a table cell value so it renders cleanly inside a Markdown pipe table."""
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text).strip().replace("|", "\\|")


def _rows_to_markdown_table(rows: List[List[Any]], max_rows: int = MAX_TABLE_ROWS) -> Tuple[str, int]:
    """Convert a 2D list of cells into a Markdown table and return (markdown, total_rows)."""
    non_empty = [r for r in rows if any(str(c).strip() for c in r if c is not None)]
    if not non_empty:
        return "_(Tabel kosong)_", 0

    total_rows = len(non_empty)
    sliced = non_empty[:max_rows]
    col_count = max(len(r) for r in sliced)
    if col_count == 0:
        return "_(Tabel kosong)_", 0

    normalized = []
    for row in sliced:
        padded = [_clean_cell(row[i] if i < len(row) else "") for i in range(col_count)]
        normalized.append(padded)

    header = "| " + " | ".join(normalized[0]) + " |"
    divider = "| " + " | ".join(["---"] * col_count) + " |"
    body = ["| " + " | ".join(r) + " |" for r in normalized[1:]]

    md_lines = [header, divider, *body]
    if total_rows > max_rows:
        md_lines.append("")
        md_lines.append(f"_*(Menampilkan {max_rows} dari {total_rows} baris pertama)*_")
    return "\n".join(md_lines), total_rows


def _parse_pdf_bytes(data: bytes) -> Tuple[str, Dict[str, Any]]:
    """Extract page-by-page text from PDF bytes using available Python PDF readers."""
    pages_text: List[str] = []

    # 1. pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                txt = (page.extract_text() or "").strip()
                pages_text.append(f"### 📄 Halaman {idx}\n\n{txt or '_(Halaman tidak memiliki teks terbaca)_'}")
            if pages_text:
                return "\n\n".join(pages_text), {"pages": len(pdf.pages)}
    except Exception:
        pass

    # 2. pypdfium2
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(data)
        total = len(doc)
        for idx in range(total):
            page = doc[idx]
            textpage = page.get_textpage()
            txt = (textpage.get_text_range() or "").strip()
            pages_text.append(f"### 📄 Halaman {idx + 1}\n\n{txt or '_(Halaman tidak memiliki teks terbaca)_'}")
        if pages_text:
            return "\n\n".join(pages_text), {"pages": total}
    except Exception:
        pass

    # 3. pdfminer.six
    try:
        from pdfminer.high_level import extract_text
        raw_txt = (extract_text(io.BytesIO(data)) or "").strip()
        if raw_txt:
            raw_pages = [p.strip() for p in raw_txt.split("\x0c") if p.strip()]
            for idx, p in enumerate(raw_pages, start=1):
                pages_text.append(f"### 📄 Halaman {idx}\n\n{p}")
            return "\n\n".join(pages_text), {"pages": len(raw_pages)}
    except Exception:
        pass

    # 4. PyPDF2
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        for idx, page in enumerate(reader.pages, start=1):
            txt = (page.extract_text() or "").strip()
            pages_text.append(f"### 📄 Halaman {idx}\n\n{txt or '_(Halaman tidak memiliki teks terbaca)_'}")
        if pages_text:
            return "\n\n".join(pages_text), {"pages": len(reader.pages)}
    except Exception:
        pass

    raise RuntimeError(
        "Gagal mengekstrak teks PDF (file mungkin terenkripsi, rusak, atau berupa PDF scan gambar)."
    )


def _local_tag(elem: ET.Element) -> str:
    """Return XML local tag name stripped of namespace URI."""
    return elem.tag.split("}", 1)[-1] if "}" in elem.tag else elem.tag


def _docx_paragraph_to_markdown(p_elem: ET.Element) -> str:
    """Convert a WordprocessingML <w:p> element into Markdown text (headings, lists, paragraphs)."""
    ns_w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    texts = []
    for node in p_elem.iter():
        tag = _local_tag(node)
        if tag == "t" and node.text:
            texts.append(node.text)
        elif tag == "tab":
            texts.append("  ")
        elif tag == "br":
            texts.append("\n")

    line = "".join(texts).strip()
    if not line:
        return ""

    p_pr = p_elem.find(f"{ns_w}pPr")
    style_val = ""
    has_num = False
    if p_pr is not None:
        p_style = p_pr.find(f"{ns_w}pStyle")
        if p_style is not None:
            style_val = (p_style.attrib.get(f"{ns_w}val") or p_style.attrib.get("val") or "").lower()
        has_num = p_pr.find(f"{ns_w}numPr") is not None

    if "title" == style_val:
        return f"# {line}"
    if "heading1" in style_val or style_val == "1":
        return f"## {line}"
    if "heading2" in style_val or style_val == "2":
        return f"### {line}"
    if "heading3" in style_val or style_val == "3":
        return f"#### {line}"
    if "heading" in style_val:
        return f"#### {line}"
    if has_num or "list" in style_val:
        return f"- {line}"
    return line


def _docx_table_to_markdown(tbl_elem: ET.Element) -> str:
    """Convert a WordprocessingML <w:tbl> element into a Markdown table."""
    ns_w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    rows: List[List[str]] = []
    for tr in tbl_elem.findall(f"{ns_w}tr"):
        row_cells: List[str] = []
        for tc in tr.findall(f"{ns_w}tc"):
            cell_parts = []
            for p in tc.findall(f".//{ns_w}p"):
                txt = "".join(t.text for t in p.findall(f".//{ns_w}t") if t.text).strip()
                if txt:
                    cell_parts.append(txt)
            row_cells.append(" ".join(cell_parts))
        if row_cells:
            rows.append(row_cells)

    table_md, _ = _rows_to_markdown_table(rows)
    return table_md


def _parse_docx_bytes(data: bytes) -> Tuple[str, Dict[str, Any]]:
    """Parse DOCX zip/XML directly via stdlib without requiring python-docx."""
    ns_w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    blocks: List[str] = []

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        if "word/document.xml" not in zf.namelist():
            raise RuntimeError("File DOCX tidak valid (word/document.xml tidak ditemukan).")
        xml_bytes = zf.read("word/document.xml")

    root = ET.fromstring(xml_bytes)
    body = root.find(f"{ns_w}body")
    if body is None:
        return "_(Dokumen DOCX kosong)_", {}

    for child in body:
        tag = _local_tag(child)
        if tag == "p":
            md = _docx_paragraph_to_markdown(child)
            if md:
                blocks.append(md)
        elif tag == "tbl":
            tbl_md = _docx_table_to_markdown(child)
            if tbl_md:
                blocks.append(tbl_md)

    return ("\n\n".join(blocks) if blocks else "_(Dokumen DOCX tidak berisi teks)_"), {}


def _col_ref_to_index(cell_ref: str) -> int:
    """Convert Excel cell coordinate like 'AB12' to 0-based column index."""
    col_letters = "".join(ch for ch in cell_ref if ch.isalpha()).upper()
    idx = 0
    for ch in col_letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return max(0, idx - 1)


def _parse_xlsx_bytes(data: bytes) -> Tuple[str, Dict[str, Any]]:
    """Parse XLSX workbooks into Markdown tables using openpyxl or stdlib XML."""
    sections: List[str] = []

    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = [list(row) for row in ws.iter_rows(values_only=True)]
            table_md, total_rows = _rows_to_markdown_table(rows)
            sections.append(f"### 📊 Sheet: {sheet_name} ({total_rows} baris)\n\n{table_md}")
        wb.close()
        if sections:
            return "\n\n".join(sections), {"sheets": len(sections)}
    except Exception:
        sections = []

    # Pure-stdlib XML fallback for .xlsx
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            sst_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sst_root:
                if _local_tag(si) == "si":
                    parts = [el.text for el in si.iter() if _local_tag(el) == "t" and el.text]
                    shared_strings.append("".join(parts))

        sheet_names: List[str] = []
        if "xl/workbook.xml" in zf.namelist():
            wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
            for el in wb_root.iter():
                if _local_tag(el) == "sheet" and el.attrib.get("name"):
                    sheet_names.append(el.attrib["name"])

        sheet_paths = sorted(
            [p for p in zf.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", p)],
            key=lambda p: int(re.search(r"(\d+)", p).group(1))
        )

        for idx, sp in enumerate(sheet_paths):
            sheet_title = sheet_names[idx] if idx < len(sheet_names) else f"Sheet {idx + 1}"
            s_root = ET.fromstring(zf.read(sp))
            rows: List[List[str]] = []
            for row_el in s_root.iter():
                if _local_tag(row_el) != "row":
                    continue
                row_vals: Dict[int, str] = {}
                max_col = -1
                for c_el in row_el:
                    if _local_tag(c_el) != "c":
                        continue
                    ref = c_el.attrib.get("r", "")
                    col_idx = _col_ref_to_index(ref) if ref else (max_col + 1)
                    max_col = max(max_col, col_idx)
                    c_type = c_el.attrib.get("t", "")
                    val = ""
                    if c_type == "inlineStr":
                        val = "".join(t.text for t in c_el.iter() if _local_tag(t) == "t" and t.text)
                    else:
                        v_el = next((ch for ch in c_el if _local_tag(ch) == "v"), None)
                        raw_v = v_el.text if (v_el is not None and v_el.text) else ""
                        if c_type == "s" and raw_v.isdigit():
                            s_idx = int(raw_v)
                            val = shared_strings[s_idx] if s_idx < len(shared_strings) else raw_v
                        else:
                            val = raw_v
                    row_vals[col_idx] = val
                if max_col >= 0:
                    rows.append([row_vals.get(i, "") for i in range(max_col + 1)])

            table_md, total_rows = _rows_to_markdown_table(rows)
            sections.append(f"### 📊 Sheet: {sheet_title} ({total_rows} baris)\n\n{table_md}")

    if not sections:
        return "_(Workbook XLSX kosong)_", {"sheets": 0}
    return "\n\n".join(sections), {"sheets": len(sections)}


def _parse_pptx_bytes(data: bytes) -> Tuple[str, Dict[str, Any]]:
    """Extract slide-by-slide text from PPTX presentation XML."""
    slides_md: List[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        slide_paths = sorted(
            [p for p in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", p)],
            key=lambda p: int(re.search(r"slide(\d+)\.xml$", p).group(1))
        )
        for idx, sp in enumerate(slide_paths, start=1):
            s_root = ET.fromstring(zf.read(sp))
            lines: List[str] = []
            for p_el in s_root.iter():
                if _local_tag(p_el) == "p":
                    text_runs = [t.text for t in p_el.iter() if _local_tag(t) == "t" and t.text]
                    line = "".join(text_runs).strip()
                    if line:
                        lines.append(f"- {line}")
            body = "\n".join(lines) if lines else "_(Slide tanpa teks)_"
            slides_md.append(f"### 🖥️ Slide {idx}\n\n{body}")

    if not slides_md:
        return "_(Presentasi PPTX kosong)_", {"slides": 0}
    return "\n\n".join(slides_md), {"slides": len(slides_md)}


def _parse_csv_bytes(data: bytes, ext: str) -> Tuple[str, Dict[str, Any]]:
    """Parse CSV/TSV text into a Markdown table."""
    text = _decode_text_bytes(data)
    delimiter = "\t" if ext == "tsv" else ","
    if ext == "csv":
        sample = text[:2048]
        if sample.count(";") > sample.count(","):
            delimiter = ";"

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [row for row in reader]
    table_md, total_rows = _rows_to_markdown_table(rows)
    return table_md, {"rows": total_rows}


def _parse_html_bytes(data: bytes) -> Tuple[str, Dict[str, Any]]:
    """Extract readable text from HTML markup."""
    raw_html = _decode_text_bytes(data)
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")
        for el in soup(["script", "style", "noscript"]):
            el.decompose()
        lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
        return "\n\n".join(lines), {}
    except ImportError:
        parser = _FallbackHTMLTextExtractor()
        parser.feed(raw_html)
        return parser.get_text(), {}


def parse_uploaded_document(filename: str, raw_content: str, mime_type: str = "") -> Dict[str, Any]:
    """
    Parse an uploaded document payload into structured Markdown and note metadata.
    Supports PDF, DOCX, XLSX/XLSM, PPTX, CSV/TSV, JSON, HTML, Markdown, TXT, and source code.
    """
    clean_name = os.path.basename(filename or "document.txt").strip() or "document.txt"
    stem, dot_ext = os.path.splitext(clean_name)
    ext = dot_ext.lstrip(".").lower() or "txt"
    raw_bytes = _decode_raw_payload(raw_content, ext)

    meta: Dict[str, Any] = {}
    if ext == "pdf":
        body_md, meta = _parse_pdf_bytes(raw_bytes)
    elif ext == "docx":
        body_md, meta = _parse_docx_bytes(raw_bytes)
    elif ext in {"xlsx", "xlsm"}:
        body_md, meta = _parse_xlsx_bytes(raw_bytes)
    elif ext == "pptx":
        body_md, meta = _parse_pptx_bytes(raw_bytes)
    elif ext in {"csv", "tsv"}:
        body_md, meta = _parse_csv_bytes(raw_bytes, ext)
    elif ext == "json":
        text = _decode_text_bytes(raw_bytes).strip()
        try:
            pretty = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
        except Exception:
            pretty = text
        body_md = f"```json\n{pretty}\n```"
    elif ext in {"html", "htm"}:
        body_md, meta = _parse_html_bytes(raw_bytes)
    elif ext in CODE_LANG_MAP:
        lang = CODE_LANG_MAP[ext]
        code_text = _decode_text_bytes(raw_bytes).strip()
        body_md = f"```{lang}\n{code_text}\n```"
    else:
        body_md = _decode_text_bytes(raw_bytes).strip()

    body_md = body_md.strip() or "_(Dokumen tidak berisi teks terbaca)_"
    word_count = len(re.findall(r"\S+", body_md))

    meta_parts = [f"📄 **Dokumen Terimpor:** `{clean_name}`", f"**Format:** {ext.upper()}"]
    if meta.get("pages"):
        meta_parts.append(f"**Halaman:** {meta['pages']}")
    if meta.get("sheets"):
        meta_parts.append(f"**Sheet:** {meta['sheets']}")
    if meta.get("slides"):
        meta_parts.append(f"**Slide:** {meta['slides']}")
    if meta.get("rows"):
        meta_parts.append(f"**Baris:** {meta['rows']}")
    meta_parts.append(f"**Estimasi:** {word_count:,} kata")

    full_markdown = "> " + " · ".join(meta_parts) + "\n\n---\n\n" + body_md
    clean_title = re.sub(r"[_-]+", " ", stem).strip() or clean_name

    return {
        "filename": clean_name,
        "title": clean_title[:80],
        "ext": ext,
        "markdown": full_markdown,
        "raw_text": body_md,
        "tags": ["imported", ext],
        "word_count": word_count,
    }
