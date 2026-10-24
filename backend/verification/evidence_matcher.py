import re
import numpy as np
from typing import List, Tuple, Optional
from backend.models.schemas import SourceRecord
from backend.retrieval.embeddings import embedding_service
from backend.retrieval.index import vector_index

GEO_EVIDENCE_WORDS = {
    'located', 'situate', 'situated', 'lies', 'lie', 'southern', 'northern',
    'eastern', 'western', 'south', 'north', 'east', 'west', 'southernmost',
    'northernmost', 'subcontinent', 'bordered', 'borders', 'region', 'peninsula',
    'geography', 'geographic',
}

COUNT_EVIDENCE_WORDS = {
    'districts', 'district', 'number', 'total', 'count', 'consist',
    'comprises', 'administrative', 'divisions', 'headquarters',
}

TIME_EVIDENCE_WORDS = {
    'hours', 'timing', 'schedule', 'open', 'close', 'closes', 'am', 'pm',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'weekday', 'weekend', 'morning', 'afternoon', 'evening', 'operates',
}

PERSON_EVIDENCE_WORDS = {
    'appointed', 'elected', 'thiru', 'shri', 'serves as', 'held by',
}

POLICY_EVIDENCE_WORDS = {
    'policy', 'rule', 'regulation', 'requirement', 'mandatory', 'minimum',
    'condonation', 'attendance', 'allowed', 'permitted', 'prohibited',
    'percentage', 'percent', 'credit', 'cgpa', 'gpa', 'marks',
}

_STOPWORDS = {
    'what', 'whats', 'who', 'whos', 'whom', 'whose', 'when', 'where', 'why', 'how',
    'the', 'this', 'that', 'these', 'those', 'are', 'was', 'were', 'been', 'being',
    'have', 'has', 'had', 'does', 'did', 'will', 'would', 'shall', 'should', 'can',
    'could', 'may', 'might', 'must', 'and', 'but', 'for', 'nor', 'yet', 'from',
    'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'under', 'tell', 'explain', 'give', 'show', 'describe', 'please', 'something',
    'which', 'part', 'many', 'much', 'some', 'any', 'all', 'each', 'every',
    'its', 'our', 'their', 'your', 'his', 'her', 'than', 'then', 'such',
    'also', 'just', 'only', 'even', 'both', 'there', 'here', 'very',
}


def _detect_intent(question: str) -> str:
    q = question.lower()
    if any(p in q for p in [
        'in which part', 'in which region', 'in which area',
        'where is', 'where does', 'where located',
        'which part', 'which state', 'which region', 'which country',
        'geograph', 'situated', 'what part', 'what region',
    ]):
        return 'geography'
    if any(p in q for p in [
        'how many', 'number of', 'total number', 'count of', 'how much',
        'how large', 'how big', 'population', 'area of', 'size of',
        'districts', 'headquarters',
    ]):
        return 'count'
    if any(p in q for p in [
        'who is', 'who was', 'who are', 'who were',
        'chief minister', 'minister', 'president', 'director', 'dean',
        'head of', 'named', 'appointed',
    ]):
        return 'person'
    if any(p in q for p in [
        'what time', 'when does', 'when do', 'timing', 'schedule',
        'hours', 'open', 'close', 'closes', 'opens', 'operating hours',
        'start time', 'end time', 'timings',
    ]):
        return 'time'
    if any(p in q for p in [
        'policy', 'rules', 'attendance', 'percentage', 'minimum', 'maximum',
        'mandatory', 'allowed', 'permitted', 'scholarship', 'requirement',
        'condonation', 'gpa', 'cgpa', 'marks', 'credit', 'fee', 'hostel',
    ]):
        return 'policy'
    return 'general'


def _chunk_passes_intent_gate(snippet: str, intent: str) -> bool:
    snip_lower = snippet.lower()
    if intent == 'geography':
        return any(w in snip_lower for w in GEO_EVIDENCE_WORDS)
    if intent == 'count':
        has_number = bool(re.search(r'\b\d{2,}\b', snip_lower))
        has_word = any(w in snip_lower for w in COUNT_EVIDENCE_WORDS)
        return has_number or has_word
    if intent == 'person':
        return any(w in snip_lower for w in PERSON_EVIDENCE_WORDS)
    if intent == 'time':
        return any(w in snip_lower for w in TIME_EVIDENCE_WORDS)
    if intent == 'policy':
        return any(w in snip_lower for w in POLICY_EVIDENCE_WORDS)
    return True


class EvidenceMatcher:
    """
    Three-stage evidence gate:
      A - similarity threshold
      B - intent alignment (chunk must contain the right information type)
      C - entity presence (key nouns must appear in the chunk)

    Prevents tourism docs from counting as geographic evidence just because
    they mention Tamil Nadu.
    """

    def filter_relevant_evidence(
        self,
        question: str,
        sources: List[SourceRecord],
        min_similarity: float = 0.28
    ) -> List[SourceRecord]:
        if not sources:
            return []

        tokens = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        core_kw = [t for t in tokens if t not in _STOPWORDS]

        intent = _detect_intent(question)
        q_lower = question.lower()
        is_person_query = bool(re.search(r'\bwho\b', q_lower)) or any(
            k in core_kw for k in ['minister', 'dean', 'director', 'president', 'officer', 'head', 'collector']
        )

        filtered: List[SourceRecord] = []
        for s in sources:
            # Stage A
            if s.similarity < min_similarity:
                continue
            # Stage B
            if not _chunk_passes_intent_gate(s.snippet, intent):
                continue

            snip_lower = s.snippet.lower()

            # Stage C
            if not core_kw:
                filtered.append(s)
                continue

            matched_kw = [k for k in core_kw if k in snip_lower]
            kw_ratio = len(matched_kw) / len(core_kw)

            if is_person_query:
                if 'minister' in core_kw or 'chief' in core_kw:
                    has_scheme = any(w in snip_lower for w in ['scheme', 'yojana', 'package', 'insurance', 'breakfast', 'thittam'])
                    has_name = any(w in snip_lower for w in ['chief minister is', 'thiru', 'shri', 'elected', 'appointed as'])
                    if has_scheme and not has_name:
                        continue
                if kw_ratio < 0.60:
                    continue
            else:
                if len(matched_kw) == 0 and s.similarity < 0.50:
                    continue

            filtered.append(s)

        return filtered

    def match_claim(
        self,
        claim: str,
        retrieved_sources: List[SourceRecord] = None,
        restrict_to_sources: bool = True
    ) -> List[Tuple[str, float, str]]:
        """
        Finds best evidence for an atomic claim.
        By default restricts to post-gate sources only to prevent false support.
        """
        matches: List[Tuple[str, float, str]] = []

        if retrieved_sources:
            claim_emb = embedding_service.embed_text(claim)
            claim_vec = np.array(claim_emb, dtype=np.float32)
            c_norm = float(np.linalg.norm(claim_vec))
            if c_norm > 0:
                claim_vec = claim_vec / c_norm

            scored = []
            for s in retrieved_sources:
                src_emb = embedding_service.embed_text(s.snippet)
                src_vec = np.array(src_emb, dtype=np.float32)
                s_norm = float(np.linalg.norm(src_vec))
                if s_norm > 0:
                    src_vec = src_vec / s_norm
                sim = float(np.dot(claim_vec, src_vec))
                scored.append((s.snippet, sim, s.document))

            scored.sort(key=lambda x: x[1], reverse=True)
            matches = scored[:3]

        if not matches and not restrict_to_sources:
            claim_emb = embedding_service.embed_text(claim)
            results = vector_index.search(claim_emb, top_k=3, min_similarity=0.20)
            for rec, score in results:
                matches.append((rec['text'], score, rec['document_name']))

        return matches


evidence_matcher = EvidenceMatcher()
