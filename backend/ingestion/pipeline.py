import os
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any
from backend.ingestion.loader import DocumentLoader
from backend.ingestion.parser import TextParser
from backend.ingestion.chunker import DocumentChunker
from backend.retrieval.embeddings import embedding_service
from backend.storage.database import store
from backend.retrieval.index import vector_index

class IngestionPipeline:
    """
    Complete ingestion pipeline:
    DOCUMENT -> TEXT EXTRACTION -> CLEANING -> CHUNKING -> EMBEDDING -> LOCAL INDEX
    """
    def __init__(self):
        self.loader = DocumentLoader()
        self.parser = TextParser()
        self.chunker = DocumentChunker()

    def process_file(self, file_path: Path) -> Dict[str, Any]:
        raw_text, filename = self.loader.load_file(file_path)
        cleaned = self.parser.clean_text(raw_text)

        if not cleaned:
            return {"filename": filename, "status": "empty", "chunks": 0}

        doc_id = str(uuid.uuid4())[:8]
        chunks = self.chunker.chunk_document(cleaned, filename, doc_id)

        # Generate embeddings
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_documents(texts)
        for i, c in enumerate(chunks):
            c["embedding"] = embeddings[i]

        # If document with same filename already exists, remove old records first
        store.delete_document(filename)

        # Persist
        size_bytes = file_path.stat().st_size if file_path.exists() else len(raw_text.encode("utf-8"))
        indexed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        store.add_document(doc_id, filename, size_bytes, indexed_at, len(chunks))
        store.add_chunks(chunks)

        # Synchronize vector index
        vector_index.reload_from_storage()

        return {
            "document_id": doc_id,
            "filename": filename,
            "status": "indexed",
            "chunks": len(chunks)
        }

    def process_directory(self, dir_path: Path) -> List[Dict[str, Any]]:
        results = []
        for p in dir_path.glob("*"):
            if p.is_file() and p.suffix.lower() in self.loader.SUPPORTED_EXTENSIONS:
                try:
                    res = self.process_file(p)
                    results.append(res)
                except Exception as e:
                    print(f"[Pipeline] Error processing {p.name}: {e}")
        return results

ingestion_pipeline = IngestionPipeline()
