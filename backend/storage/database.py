import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import settings

class LocalStore:
    """
    Persistent SQLite + JSON storage for chunks, embeddings and documents.
    Does not require external PostgreSQL for local execution.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.index_dir / "veridex_store.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT UNIQUE,
                    size_bytes INTEGER,
                    indexed_at TEXT,
                    chunk_count INTEGER
                )
            """)
            # Chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    record_id TEXT PRIMARY KEY,
                    document_id TEXT,
                    document_name TEXT,
                    chunk_id INTEGER,
                    text TEXT,
                    embedding TEXT,
                    FOREIGN KEY(document_id) REFERENCES documents(document_id)
                )
            """)
            conn.commit()

    def add_document(self, doc_id: str, filename: str, size_bytes: int, indexed_at: str, chunk_count: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents (document_id, filename, size_bytes, indexed_at, chunk_count)
                VALUES (?, ?, ?, ?, ?)
            """, (doc_id, filename, size_bytes, indexed_at, chunk_count))
            conn.commit()

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for chunk in chunks:
                emb_str = json.dumps(chunk["embedding"]) if isinstance(chunk["embedding"], list) else json.dumps(chunk["embedding"].tolist())
                cursor.execute("""
                    INSERT OR REPLACE INTO chunks (record_id, document_id, document_name, chunk_id, text, embedding)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    chunk["record_id"],
                    chunk["document_id"],
                    chunk["document_name"],
                    chunk["chunk_id"],
                    chunk["text"],
                    emb_str
                ))
            conn.commit()

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT record_id, document_id, document_name, chunk_id, text, embedding FROM chunks")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append({
                    "record_id": row[0],
                    "document_id": row[1],
                    "document_name": row[2],
                    "chunk_id": row[3],
                    "text": row[4],
                    "embedding": json.loads(row[5])
                })
            return results

    def get_documents(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT document_id, filename, size_bytes, indexed_at, chunk_count FROM documents")
            rows = cursor.fetchall()
            return [
                {
                    "document_id": r[0],
                    "filename": r[1],
                    "size_bytes": r[2],
                    "indexed_at": r[3],
                    "chunk_count": r[4]
                }
                for r in rows
            ]

    def delete_document(self, filename: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT document_id FROM documents WHERE filename = ?", (filename,))
            row = cursor.fetchone()
            doc_id = row[0] if row else None
            if doc_id:
                cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
                cursor.execute("DELETE FROM documents WHERE document_id = ?", (doc_id,))
            # Also purge any chunks matching document_name
            cursor.execute("DELETE FROM chunks WHERE document_name = ?", (filename,))
            conn.commit()
            return True

    def total_chunks_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks")
            row = cursor.fetchone()
            return row[0] if row else 0

store = LocalStore()
