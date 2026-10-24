import os
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

# Base Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / os.getenv("VERIDEX_DATA_DIR", "data/documents")
INDEX_DIR = BASE_DIR / os.getenv("VERIDEX_INDEX_DIR", "data/index")

DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    # Models
    embedding_model_name: str = os.getenv("VERIDEX_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    llm_provider: str = os.getenv("VERIDEX_LLM_PROVIDER", "extractive")
    llm_model_name: str = os.getenv("VERIDEX_LLM_MODEL", "google/flan-t5-base")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    nli_model_name: str = os.getenv("VERIDEX_NLI_MODEL", "cross-encoder/nli-distilroberta-base")

    # Ingestion & Chunking
    chunk_size: int = int(os.getenv("VERIDEX_CHUNK_SIZE", "150"))
    chunk_overlap: int = int(os.getenv("VERIDEX_CHUNK_OVERLAP", "20"))

    # Retrieval
    top_k: int = int(os.getenv("VERIDEX_TOP_K", "5"))             # fetch more candidates
    top_k_candidates: int = int(os.getenv("VERIDEX_TOP_K_CANDIDATES", "8"))  # pre-filter pool
    min_similarity: float = float(os.getenv("VERIDEX_MIN_SIMILARITY", "0.25"))

    # Claim-level verification thresholds
    # A claim is SUPPORTED only when BOTH NLI says 'support' AND
    # the cosine similarity between the claim and its best evidence chunk
    # meets this threshold. Prevents weak semantic overlaps from producing
    # false SUPPORTED verdicts.
    claim_evidence_min_similarity: float = float(os.getenv("VERIDEX_CLAIM_EVIDENCE_MIN_SIM", "0.30"))

    # Evidence gate — intent alignment enabled/disabled
    evidence_intent_gate_enabled: bool = True

    # Reliability Formula Weights (Proposed formulation)
    w_support: float = float(os.getenv("VERIDEX_SUPPORT_WEIGHT", "1.0"))
    w_contradiction: float = float(os.getenv("VERIDEX_CONTRADICTION_WEIGHT", "1.8"))
    w_neutral: float = float(os.getenv("VERIDEX_NEUTRAL_WEIGHT", "0.3"))
    w_inconsistency: float = float(os.getenv("VERIDEX_INCONSISTENCY_WEIGHT", "1.2"))

    # Illustrative Thresholds
    threshold_trustworthy: float = float(os.getenv("VERIDEX_TRUSTWORTHY_THRESHOLD", "0.85"))
    threshold_partial: float = float(os.getenv("VERIDEX_PARTIAL_THRESHOLD", "0.60"))
    threshold_misleading: float = float(os.getenv("VERIDEX_MISLEADING_THRESHOLD", "0.35"))

    # Directories
    data_dir: Path = DATA_DIR
    index_dir: Path = INDEX_DIR

settings = Settings()
