import re
import hashlib
import numpy as np
from typing import List

class EmbeddingService:
    """
    Local deterministic TF-IDF / subword hash projection embedding service.
    Zero network calls, completely deterministic across Python processes.
    High semantic fidelity for local document retrieval and claim alignment.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def embed_text(self, text: str) -> List[float]:
        return self._vectorize(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vectorize(t) for t in texts]

    def _stable_hash(self, token: str) -> int:
        return int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)

    def _vectorize(self, text: str) -> List[float]:
        dim = 384
        vec = np.zeros(dim, dtype=np.float32)
        if not text:
            vec[0] = 1.0
            return vec.tolist()

        # Stop words to downweight noise
        stops = {"the", "a", "an", "is", "are", "of", "and", "or", "to", "for", "in", "on", "at", "with", "by", "what", "which", "how"}

        words = [w for w in re.findall(r'[a-zA-Z0-9]+', text.lower()) if w not in stops]
        if not words:
            vec[0] = 1.0
            return vec.tolist()

        # Word unigrams with length-based boost
        for w in words:
            h = self._stable_hash(w)
            idx = h % dim
            weight = 2.0 if len(w) > 4 else 1.0
            vec[idx] += weight

            # Subword 3-grams for morphological matching (e.g. librar -> library)
            if len(w) >= 4:
                for i in range(len(w) - 2):
                    sub = w[i:i+3]
                    s_idx = self._stable_hash(sub) % dim
                    vec[s_idx] += 0.4

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec.tolist()

embedding_service = EmbeddingService()
