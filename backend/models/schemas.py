from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class SourceRecord(BaseModel):
    record_id: str
    document: str
    snippet: str
    similarity: float
    section: Optional[str] = None
    page: Optional[int] = None
    authority: Optional[str] = "Authorized Local Knowledge"

class ClaimEvidenceDetail(BaseModel):
    document: str
    section: Optional[str] = None
    page: Optional[str] = None
    snippet: str
    relevance: float = 0.9
    relation: Literal["supports", "conflicts", "neutral"] = "supports"

class ClaimVerification(BaseModel):
    claim_id: str
    text: str
    scope: Literal["institutional", "general"] = "general"
    status: Literal[
        "SUPPORTED",
        "UNCERTAIN",
        "CONTRADICTED",
        "ABSTAINED",
        "VERIFIED — LOCAL",
        "CONTRADICTION",
        "UNVERIFIED — GENERAL",
        "NOT VERIFIABLE",
        "supported",
        "contradiction",
        "unverified",
        "unsupported",
        "neutral"
    ]
    evidence: List[str] = Field(default_factory=list)
    conflicting_evidence: List[str] = Field(default_factory=list)
    evidence_details: List[ClaimEvidenceDetail] = Field(default_factory=list)
    reason: str
    confidence: float = 1.0

class ReliabilityOutput(BaseModel):
    score: Optional[float] = None
    verdict: Literal[
        "SUPPORTED",
        "PARTIAL",
        "CONTRADICTION DETECTED",
        "ABSTAINED",
        "VERIFIED",
        "PARTIALLY VERIFIED",
        "UNVERIFIED — GENERAL",
        "NOT VERIFIABLE",
        "trustworthy",
        "partially_reliable",
        "misleading",
        "contradiction",
        "unverified",
        "fabricated"
    ]
    supported_claims: int = 0
    contradicted_claims: int = 0
    neutral_claims: int = 0
    unsupported_claims: int = 0
    inconsistent_claims: int = 0
    evidence_coverage_pct: float = 100.0
    retrieval_relevance: float = 0.0

class AskRequest(BaseModel):
    question: str
    user_id: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    detected_scope: Literal["INSTITUTIONAL", "GENERAL", "HYBRID"]
    mode: Literal["institutional", "general", "hybrid"]
    verification_status: Literal[
        "SUPPORTED",
        "PARTIAL",
        "CONTRADICTION DETECTED",
        "ABSTAINED",
        "VERIFIED — LOCAL",
        "PARTIALLY VERIFIED",
        "UNVERIFIED — GENERAL",
        "NOT VERIFIABLE",
        "verified",
        "unverified",
        "contradicted",
        "unsupported"
    ]
    decision: Literal["PRESENT_VERIFIED", "QUALIFY_UNCERTAINTY", "BLOCK_AND_CORRECT", "ABSTAIN"] = "PRESENT_VERIFIED"
    sources: List[SourceRecord]
    claims: List[ClaimVerification]
    reliability: ReliabilityOutput
    explanation: str
    message: str
    why_trust: List[str] = Field(default_factory=list)
    normalized_query: Optional[str] = None
    query_normalization: Optional[Dict[str, Any]] = None
    telemetry: Optional[Dict[str, Any]] = None
    raw_llm_comparison: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    retrieval: bool
    generation: bool
    verification: bool
    models: Dict[str, bool] = Field(default_factory=dict)
    knowledge_base: Dict[str, int] = Field(default_factory=dict)
    system: Optional[Dict[str, Any]] = None

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    size_bytes: int
    indexed_at: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total_chunks: int
