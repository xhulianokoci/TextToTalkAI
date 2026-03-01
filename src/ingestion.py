# ============================================================
# ingestion.py — Document Parsing + Chunking
# ============================================================
# Responsibilities:
#   - Accept PDF or .txt files
#   - Extract raw text
#   - Split text into overlapping chunks
#   - Return chunks with metadata (source, page, chunk index)
# ============================================================

import fitz  # PyMuPDF
import tiktoken
from pathlib import Path


# --- Constants ---
CHUNK_SIZE = 800      # Max tokens per chunk
CHUNK_OVERLAP = 100   # Overlap between consecutive chunks to preserve context

# Tokenizer matching OpenAI's embedding model
TOKENIZER = tiktoken.get_encoding("cl100k_base")


def extract_text_from_pdf(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Extract text from a PDF file page by page.
    Returns a list of dicts: { text, page_number, source }
    """
    pages = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        if text:  # Skip blank pages
            pages.append({
                "text": text,
                "page_number": page_num + 1,  # Human-readable (1-indexed)
                "source": filename
            })

    doc.close()
    return pages


def extract_text_from_txt(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Extract text from a plain text file.
    Treated as a single 'page' for consistency.
    """
    text = file_bytes.decode("utf-8", errors="ignore").strip()
    return [{"text": text, "page_number": 1, "source": filename}]


def chunk_text(text: str, page_number: int, source: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split a block of text into overlapping token-based chunks.

    Why token-based and not character-based?
    Because embedding models have token limits. Counting tokens
    directly ensures we never exceed the model's input window.

    Returns a list of chunk dicts with metadata.
    """
    tokens = TOKENIZER.encode(text)
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text_decoded = TOKENIZER.decode(chunk_tokens)

        chunks.append({
            "text": chunk_text_decoded,
            "source": source,
            "page_number": page_number,
            "chunk_index": chunk_index,
            # Unique ID for Pinecone upsert
            "chunk_id": f"{source}__page{page_number}__chunk{chunk_index}"
        })

        chunk_index += 1
        start += chunk_size - overlap  # Slide window with overlap

    return chunks


def process_uploaded_file(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Master function: takes raw file bytes + filename,
    returns a flat list of all chunks with metadata.

    This is the only function called by the outside world.
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        pages = extract_text_from_pdf(file_bytes, filename)
    elif suffix == ".txt":
        pages = extract_text_from_txt(file_bytes, filename)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Please upload PDF or TXT files.")

    all_chunks = []
    for page in pages:
        chunks = chunk_text(
            text=page["text"],
            page_number=page["page_number"],
            source=page["source"]
        )
        all_chunks.extend(chunks)

    return all_chunks
