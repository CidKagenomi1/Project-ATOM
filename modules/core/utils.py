import io

def read_file_content(uploaded_file) -> str:
    """
    Read content from an uploaded file.
    Supports: .txt, .md, .py, .json, .csv, .pdf, .html, .css, .js
    """
    try:
        filename = getattr(uploaded_file, "name", "").lower()
        
        # Text-based files
        if filename.endswith(('.txt', '.md', '.py', '.json', '.csv', '.html', '.css', '.js')):
            content = uploaded_file.read()
            if isinstance(content, str):
                return content
            return content.decode('utf-8', errors='ignore')
        
        # PDF files
        elif filename.endswith('.pdf'):
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            except ImportError:
                return "[ERROR] PyPDF2 not installed. Run: pip install PyPDF2"
            except Exception as e:
                return f"[ERROR] Failed to read PDF: {e}"
        
        else:
            return f"[ERROR] Unsupported file type: {filename}"
            
    except Exception as e:
        return f"[ERROR] Failed to read file: {e}"


def scrape_url(url: str) -> str:
    """
    Scrape text content from a URL.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Limit length
        if len(clean_text) > 10000:
            clean_text = clean_text[:10000] + "\n\n[Content truncated...]"
        
        return clean_text
        
    except ImportError:
        return "[ERROR] BeautifulSoup not installed. Run: pip install beautifulsoup4"
    except Exception as e:
        return f"[ERROR] Failed to scrape URL: {e}"

