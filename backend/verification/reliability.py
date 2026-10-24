from typing import List, Dict, Any, Tuple, Optional
from backend.models.schemas import ClaimVerification, ReliabilityOutput
from backend.config import settings

class ReliabilityEngine:
    """
    Computes overall reliability score and assigns final verdicts:
    
    Verdicts:
    - VERIFIED: All claims verified against local evidence.
    - PARTIALLY VERIFIED: Some claims verified, some unverified/neutral, no contradictions.
    - CONTRADICTION DETECTED: Direct factual conflict detected with local evidence.
    - UNVERIFIED — GENERAL: General-domain knowledge with 0 local evidence (not false!).
    - NOT VERIFIABLE: Claims cannot meaningfully be checked against available evidence.
    """
    def __init__(self):
        self.w_s = settings.w_support
        self.w_c = settings.w_contradiction
        self.w_n = settings.w_neutral
        self.w_i = settings.w_inconsistency

    def calculate(
        self,
        claims: List[ClaimVerification],
        inconsistency_count: int = 0,
        scope: str = "INSTITUTIONAL",
        retrieval_relevance: float = 0.0,
        is_abstained: bool = False
    ) -> Tuple[ReliabilityOutput, str]:
        total = len(claims)
        
        n_sup = sum(1 for c in claims if c.status in ("SUPPORTED", "VERIFIED — LOCAL", "supported"))
        n_con = sum(1 for c in claims if c.status in ("CONTRADICTED", "CONTRADICTION", "contradiction"))
        n_unv = sum(1 for c in claims if c.status in ("UNVERIFIED — GENERAL", "unverified"))
        n_uns = sum(1 for c in claims if c.status in ("UNCERTAIN", "unsupported", "NOT VERIFIABLE"))
        n_neu = sum(1 for c in claims if c.status == "neutral")

        coverage_pct = round((n_sup / max(1, total)) * 100, 1) if total > 0 else 0.0

        # 0. First-Class Abstention
        if is_abstained or (scope == "GENERAL" and total == 0):
            return ReliabilityOutput(
                score=None,
                verdict="ABSTAINED",
                supported_claims=0,
                contradicted_claims=0,
                neutral_claims=0,
                unsupported_claims=0,
                inconsistent_claims=0,
                evidence_coverage_pct=0.0,
                retrieval_relevance=retrieval_relevance
            ), "VERIDEX abstained from generating an ungrounded answer because no authorized local evidence exists."

        # 1. Any direct contradiction against local evidence
        if n_con > 0:
            score = round(max(0.0, 0.35 - (0.15 * n_con)), 2)
            verdict = "CONTRADICTION DETECTED"
            expl = f"VERIDEX CONTRADICTION DETECTED: {n_con} claim(s) conflict directly with indexed institutional records."
            return ReliabilityOutput(
                score=score,
                verdict=verdict,
                supported_claims=n_sup,
                contradicted_claims=n_con,
                neutral_claims=n_neu,
                unsupported_claims=n_unv + n_uns,
                inconsistent_claims=inconsistency_count,
                evidence_coverage_pct=coverage_pct,
                retrieval_relevance=retrieval_relevance
            ), expl

        # 2. Pure general query with no local evidence
        if scope == "GENERAL" or (n_sup == 0 and n_con == 0 and n_unv > 0):
            return ReliabilityOutput(
                score=None,
                verdict="ABSTAINED" if total == 0 else "UNVERIFIED — GENERAL",
                supported_claims=0,
                contradicted_claims=0,
                neutral_claims=n_neu,
                unsupported_claims=total,
                inconsistent_claims=inconsistency_count,
                evidence_coverage_pct=0.0,
                retrieval_relevance=retrieval_relevance
            ), "Outside authorized local knowledge boundary: 0 verified local claims."

        # 3. If zero claims detected
        if total == 0:
            return ReliabilityOutput(
                score=None,
                verdict="NOT VERIFIABLE",
                supported_claims=0,
                contradicted_claims=0,
                neutral_claims=0,
                unsupported_claims=0,
                inconsistent_claims=0,
                evidence_coverage_pct=0.0,
                retrieval_relevance=retrieval_relevance
            ), "No auditable factual claims were extracted from the answer."

        # 4. Institutional or Hybrid calculation
        if n_sup > 0 and (n_unv > 0 or n_neu > 0 or n_uns > 0):
            score = round(n_sup / total, 2)
            verdict = "PARTIAL"
            expl = f"VERIDEX PARTIAL: {n_sup} of {total} claims verified against institutional files; {n_unv + n_uns} claim(s) remain uncertain/unverified locally."
            return ReliabilityOutput(
                score=score,
                verdict=verdict,
                supported_claims=n_sup,
                contradicted_claims=0,
                neutral_claims=n_neu,
                unsupported_claims=n_unv + n_uns,
                inconsistent_claims=inconsistency_count,
                evidence_coverage_pct=coverage_pct,
                retrieval_relevance=retrieval_relevance
            ), expl

        if n_sup == total and total > 0:
            score = 1.0
            verdict = "SUPPORTED"
            expl = f"VERIDEX SUPPORTED: All {total} factual claims are directly substantiated by authorized campus documentation."
            return ReliabilityOutput(
                score=score,
                verdict=verdict,
                supported_claims=n_sup,
                contradicted_claims=0,
                neutral_claims=0,
                unsupported_claims=0,
                inconsistent_claims=0,
                evidence_coverage_pct=100.0,
                retrieval_relevance=retrieval_relevance
            ), expl

        # Default fallback
        score = round(n_sup / max(1, total), 2)
        return ReliabilityOutput(
            score=score if score > 0 else None,
            verdict="PARTIAL" if score > 0 else "NOT VERIFIABLE",
            supported_claims=n_sup,
            contradicted_claims=n_con,
            neutral_claims=n_neu,
            unsupported_claims=n_unv + n_uns,
            inconsistent_claims=inconsistency_count,
            evidence_coverage_pct=coverage_pct,
            retrieval_relevance=retrieval_relevance
        ), "Audit completed with mixed grounded assertions."

reliability_engine = ReliabilityEngine()
