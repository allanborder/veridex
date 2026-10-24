import uuid
from typing import List, Dict, Any
from backend.config import settings

class DocumentChunker:
    """
    Configurable chunker using character/word token approximation.
    Avoids splitting mid-sentence whenever possible.
    """
    def __init__(self, chunk_size: int = None, overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap

    def chunk_document(self, text: str, document_name: str, document_id: str) -> List[Dict[str, Any]]:
        # Split into paragraphs or logical sections
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk_words = []
        current_chunk_len = 0
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            words = para.split()
            # If a single paragraph is larger than chunk_size, split by word window
            if len(words) > self.chunk_size:
                start = 0
                while start < len(words):
                    end = start + self.chunk_size
                    slice_words = words[start:end]
                    chunk_text = " ".join(slice_words)
                    record_id = f"rec_{document_id[:6]}_{chunk_idx:03d}"
                    chunks.append({
                        "record_id": record_id,
                        "document_id": document_id,
                        "document_name": document_name,
                        "chunk_id": chunk_idx,
                        "text": chunk_text
                    })
                    chunk_idx += 1
                    start += (self.chunk_size - self.overlap)
                continue

            if current_chunk_len + len(words) > self.chunk_size and current_chunk_words:
                chunk_text = " ".join(current_chunk_words)
                record_id = f"rec_{document_id[:6]}_{chunk_idx:03d}"
                chunks.append({
                    "record_id": record_id,
                    "document_id": document_id,
                    "document_name": document_name,
                    "chunk_id": chunk_idx,
                    "text": chunk_text
                })
                chunk_idx += 1
                
                # Retain overlap words
                overlap_words = current_chunk_words[-self.overlap:] if len(current_chunk_words) >= self.overlap else current_chunk_words
                current_chunk_words = overlap_words + words
                current_chunk_len = len(current_chunk_words)
            else:
                current_chunk_words.extend(words)
                current_chunk_len += len(words)

        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            record_id = f"rec_{document_id[:6]}_{chunk_idx:03d}"
            chunks.append({
                "record_id": record_id,
                "document_id": document_id,
                "document_name": document_name,
                "chunk_id": chunk_idx,
                "text": chunk_text
            })

        return chunks
