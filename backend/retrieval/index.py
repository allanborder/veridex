import numpy as np
from typing import List, Dict, Any, Tuple
from backend.storage.database import store
from backend.retrieval.embeddings import embedding_service
from backend.config import settings

class VectorIndex:
    """
    In-memory accelerated cosine index synchronizing with SQLite store.
    """
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.embeddings_matrix: np.ndarray = np.empty((0, 384), dtype=np.float32)
        self.reload_from_storage()

    def reload_from_storage(self):
        chunks = store.get_all_chunks()
        self.records = []
        vectors = []
        for c in chunks:
            self.records.append({
                "record_id": c["record_id"],
                "document_id": c["document_id"],
                "document_name": c["document_name"],
                "chunk_id": c["chunk_id"],
                "text": c["text"]
            })
            vectors.append(c["embedding"])

        if vectors:
            self.embeddings_matrix = np.array(vectors, dtype=np.float32)
            # Ensure normalized
            norms = np.linalg.norm(self.embeddings_matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.embeddings_matrix = self.embeddings_matrix / norms
        else:
            self.embeddings_matrix = np.empty((0, 384), dtype=np.float32)

    def search(self, query_vector: List[float], top_k: int = None, min_similarity: float = None) -> List[Tuple[Dict[str, Any], float]]:
        top_k = top_k or settings.top_k
        min_similarity = min_similarity or settings.min_similarity

        if len(self.records) == 0 or self.embeddings_matrix.shape[0] == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # Cosine similarity dot product
        similarities = np.dot(self.embeddings_matrix, q_vec)

        # Filter by threshold and rank
        indices = np.argsort(similarities)[::-1]
        results = []
        for idx in indices:
            score = float(similarities[idx])
            if score >= min_similarity:
                results.append((self.records[idx], score))
            if len(results) >= top_k:
                break

        return results

vector_index = VectorIndex()
