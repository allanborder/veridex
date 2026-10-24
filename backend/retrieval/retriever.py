from typing import List, Tuple, Optional
from backend.models.schemas import SourceRecord
from backend.retrieval.embeddings import embedding_service
from backend.retrieval.index import vector_index
from backend.retrieval.query_normalizer import query_normalizer
from backend.config import settings

class LocalRetriever:
    """
    Core semantic retriever with query normalization, case insensitivity,
    typo resilience, and minimum similarity safety thresholds.
    """
    def retrieve(
        self, 
        question: str, 
        top_k: int = None, 
        min_similarity: float = None
    ) -> List[SourceRecord]:
        # 1. Normalize query: strip whitespace, fix typos, standardize casing
        norm_query, was_modified, explanation = query_normalizer.normalize(question)
        
        # 2. Semantic query expansion for temporal phrasings (e.g., 'start and finish' -> 'hours schedule')
        enriched_query = query_normalizer.expand_query_intent(norm_query)

        # 3. Vector search using primary normalized & enriched query
        query_emb = embedding_service.embed_text(enriched_query)
        matches = vector_index.search(
            query_vector=query_emb,
            top_k=top_k or settings.top_k,
            min_similarity=min_similarity or settings.min_similarity
        )

        sources = []
        for record, score in matches:
            raw_text = record["text"]
            snippet = raw_text[:800] + "..." if len(raw_text) > 800 else raw_text

            sources.append(SourceRecord(
                record_id=record["record_id"],
                document=record["document_name"],
                snippet=snippet,
                similarity=round(score, 4)
            ))
        return sources

retriever = LocalRetriever()
