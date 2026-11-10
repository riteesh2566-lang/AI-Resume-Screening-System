"""
parser.py - Extract raw text from PDF, DOCX, and TXT files
"""
import os
import re

def extract_text_from_file(filepath):
    """Extract text from PDF, DOCX, or TXT file."""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.pdf':
            return extract_from_pdf(filepath)
        elif ext in ('.docx', '.doc'):
            return extract_from_docx(filepath)
        elif ext == '.txt':
            return extract_from_txt(filepath)
        else:
            return ""
    except Exception as e:
        print(f"Error extracting text from {filepath}: {e}")
        return ""

def extract_from_pdf(filepath):
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return clean_text(text)
    except ImportError:
        # Fallback: try PyPDF2
        try:
            import PyPDF2
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return clean_text(text)
        except Exception as e:
            return f"[Could not extract PDF text: {e}]"

def extract_from_docx(filepath):
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        # Also extract from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text += "\n" + cell.text
        return clean_text(text)
    except ImportError:
        return "[python-docx not installed]"
    except Exception as e:
        return f"[Could not extract DOCX text: {e}]"

def extract_from_txt(filepath):
    """Extract text from TXT file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return clean_text(f.read())
    except Exception as e:
        return f"[Could not read TXT file: {e}]"

def clean_text(text):
    """Clean and normalize extracted text."""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\n]', ' ', text)
    return text.strip()
