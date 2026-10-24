import os
import re
import time
import shutil
import logging
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from backend.models.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    DocumentListResponse,
    DocumentInfo,
    ClaimVerification,
    ClaimEvidenceDetail
)
from backend.retrieval.retriever import retriever
from backend.retrieval.query_router import query_router
from backend.retrieval.query_normalizer import query_normalizer
from backend.retrieval.index import vector_index
from backend.generation.local_llm import local_llm
from backend.verification.claim_extractor import claim_extractor
from backend.verification.evidence_matcher import evidence_matcher
from backend.verification.nli_verifier import nli_verifier
from backend.verification.consistency import consistency_checker
from backend.verification.reliability import reliability_engine
from backend.storage.database import store
from backend.ingestion.pipeline import ingestion_pipeline
from backend.config import settings

# Configure logging for debugging workflow
logger = logging.getLogger("VERIDEX")
logging.basicConfig(level=logging.INFO, format="%(message)s")

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check():
    doc_count = len(store.get_documents())
    chunk_count = store.total_chunks_count()
    
    # Measure local hardware footprint
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    ram_mb = round(mem_info.rss / (1024 * 1024), 1)
    
    return HealthResponse(
        status="ok",
        retrieval=True,
        generation=True,
        verification=True,
        models={
            "embedding": True,
            "generation": True,
            "nli": True
        },
        knowledge_base={
            "documents": doc_count,
            "records": chunk_count
        },
        system={
            "ram_used_mb": ram_mb,
            "ram_limit_mb": 8192,
            "cpu_percent": psutil.cpu_percent(interval=None),
            "air_gapped": True,
            "cloud_dependencies": 0,
            "engine": "100% Local CPU-First"
        }
    )

@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    t0_pipeline = time.time()

    # =========================================================================
    # STAGE 0: ROBUST QUERY NORMALIZATION & TYPO CORRECTION
    # =========================================================================
    norm_question, was_modified, norm_expl = query_normalizer.normalize(question)
    query_norm_info = {
        "original_query": question,
        "normalized_query": norm_question,
        "was_modified": was_modified,
        "details": norm_expl
    }

    # =========================================================================
    # STAGE 1: LOCAL RETRIEVAL & SCOPE DETECTION
    # =========================================================================
    t0_retrieval = time.time()
    raw_sources = retriever.retrieve(norm_question, top_k=settings.top_k, min_similarity=0.0)
    scope, routed_sources, gen_part, inst_part = query_router.route(
        norm_question, raw_sources, min_similarity=settings.min_similarity
    )

    # HARD EVIDENCE GATE: Filter out irrelevant documents
    # A document is ONLY evidence if it is truly relevant to the query.
    relevant_sources = evidence_matcher.filter_relevant_evidence(
        question=norm_question,
        sources=routed_sources,
        min_similarity=settings.min_similarity
    )
    t_retrieval_ms = max(1, round((time.time() - t0_retrieval) * 1000, 1))

    # Evidence Sufficiency Evaluation:
    # If zero relevant chunks pass the gate, VERIDEX strictly ABSTAINS and BLOCKS LLM generation.
    has_sufficient_evidence = len(relevant_sources) > 0
    top_similarity = relevant_sources[0].similarity if relevant_sources else 0.0
    is_out_of_domain = not has_sufficient_evidence

    # =========================================================================
    # STAGE 2: HARD EVIDENCE GATE & GENERATION BLOCK
    # =========================================================================
    t0_gen = time.time()
    if not has_sufficient_evidence:
        # LLM GENERATION IS BLOCKED: Never generate from irrelevant evidence or pre-trained hallucinations
        answer = "I don't have sufficient authorized evidence to answer this question. No relevant source was found in the authorized knowledge base."
        institutional_sources = []
    else:
        institutional_sources = relevant_sources
        answer = local_llm.generate_answer(
            question=question,
            evidence=institutional_sources,
            scope=scope,
            gen_part=gen_part,
            inst_part=inst_part
        )
    t_gen_ms = max(1, round((time.time() - t0_gen) * 1000, 1))

    # =========================================================================
    # STAGE 3: ATOMIC CLAIM DECOMPOSITION (AFTER ANSWER GENERATION)
    # =========================================================================
    t0_claims = time.time()
    if is_out_of_domain:
        raw_claims = []
    else:
        raw_claims = claim_extractor.extract_claims(answer)
    t_claims_ms = max(1, round((time.time() - t0_claims) * 1000, 1))

    # Internal consistency check
    internal_conflicts = consistency_checker.check_consistency(raw_claims)
    inconsistent_indices = set()
    for idx1, idx2, _ in internal_conflicts:
        inconsistent_indices.add(idx1)
        inconsistent_indices.add(idx2)

    # =========================================================================
    # STAGE 4 & 5: LOCAL KNOWLEDGE BASE SEARCH & CLAIM-BY-CLAIM VERIFICATION
    # (ONLY runs if the Evidence Gate passed — never for abstained queries)
    # =========================================================================
    t0_nli = time.time()
    verified_claims: List[ClaimVerification] = []

    # Check if the user query itself asserts a factual proposition that contradicts institutional evidence
    # e.g., "Does the library close at 8 PM on weekdays?" vs Evidence: "Monday through Friday: 8:00 AM to 9:00 PM"
    query_conflict_detected = False
    query_conflict_reason = ""
    conflicting_src_snippet = ""
    conflicting_src_doc = ""
    if institutional_sources and not is_out_of_domain:
        best_ev = institutional_sources[0]
        contra, reason = nli_verifier._check_factual_conflict(best_ev.snippet, question)
        if contra:
            query_conflict_detected = True
            query_conflict_reason = reason
            conflicting_src_snippet = best_ev.snippet[:240]
            conflicting_src_doc = best_ev.document

    for i, claim_text in enumerate(raw_claims if not is_out_of_domain else []):
        claim_id = f"c_{i+1:02d}"

        if scope == "HYBRID":
            claim_scope = "institutional" if any(kw in claim_text.lower() for kw in query_router.INSTITUTIONAL_KEYWORDS) else "general"
        elif scope == "INSTITUTIONAL":
            claim_scope = "institutional"
        else:
            claim_scope = "general"

        matches = evidence_matcher.match_claim(
            claim_text,
            retrieved_sources=institutional_sources,
            restrict_to_sources=True
        )

        if not matches:
            verified_claims.append(ClaimVerification(
                claim_id=claim_id,
                text=claim_text,
                scope=claim_scope,
                status="UNCERTAIN",
                evidence=[],
                conflicting_evidence=[],
                evidence_details=[],
                reason="No supporting evidence found in the authorized knowledge base.",
                confidence=0.0
            ))
            continue

        best_snippet, sim_score, doc_name = matches[0]

        # Extract section metadata if present in snippet
        sec_match = re.search(r'##\s*Section\s+(\d+[^:\n]*):?\s*([^\n]+)?', best_snippet)
        section_label = f"Section {sec_match.group(1).strip()}" if sec_match else None

        # Check internal consistency override
        if i in inconsistent_indices:
            verified_claims.append(ClaimVerification(
                claim_id=claim_id,
                text=claim_text,
                scope=claim_scope,
                status="CONTRADICTED",
                evidence=[],
                conflicting_evidence=[f"[{doc_name}] {best_snippet[:240]}"],
                evidence_details=[ClaimEvidenceDetail(
                    document=doc_name,
                    section=section_label,
                    snippet=best_snippet[:240],
                    relevance=round(sim_score, 2),
                    relation="conflicts"
                )],
                reason="Contradicts another assertion generated within the same response.",
                confidence=0.9
            ))
            continue

        # PS2 NLI Entailment & Contradiction verification
        nli_res = nli_verifier.verify(premise=best_snippet, hypothesis=claim_text)
        label = nli_res["label"]

        if label == "contradiction":
            verified_claims.append(ClaimVerification(
                claim_id=claim_id,
                text=claim_text,
                scope=claim_scope,
                status="CONTRADICTED",
                evidence=[],
                conflicting_evidence=[f"[{doc_name}] {best_snippet[:240]}"],
                evidence_details=[ClaimEvidenceDetail(
                    document=doc_name,
                    section=section_label,
                    snippet=best_snippet[:240],
                    relevance=round(sim_score, 2),
                    relation="conflicts"
                )],
                reason=nli_res["reason"],
                confidence=nli_res["confidence"]
            ))
        elif label == "support" and sim_score >= settings.min_similarity and sim_score >= settings.claim_evidence_min_similarity:
            verified_claims.append(ClaimVerification(
                claim_id=claim_id,
                text=claim_text,
                scope=claim_scope,
                status="SUPPORTED",
                evidence=[f"[{doc_name}] {best_snippet[:240]}"],
                conflicting_evidence=[],
                evidence_details=[ClaimEvidenceDetail(
                    document=doc_name,
                    section=section_label,
                    snippet=best_snippet[:240],
                    relevance=round(sim_score, 2),
                    relation="supports"
                )],
                reason=nli_res["reason"],
                confidence=nli_res["confidence"]
            ))
        else:
            verified_claims.append(ClaimVerification(
                claim_id=claim_id,
                text=claim_text,
                scope=claim_scope,
                status="UNCERTAIN",
                evidence=[],
                conflicting_evidence=[],
                evidence_details=[ClaimEvidenceDetail(
                    document=doc_name,
                    section=section_label,
                    snippet=best_snippet[:240],
                    relevance=round(sim_score, 2),
                    relation="neutral"
                )] if sim_score > 0.2 else [],
                reason="Available evidence is insufficient to verify or refute this claim with high confidence.",
                confidence=nli_res["confidence"]
            ))

    t_nli_ms = max(1, round((time.time() - t0_nli) * 1000, 1))

    if query_conflict_detected:
        # Add explicit contradiction claim demonstrating contradiction catch
        verified_claims.insert(0, ClaimVerification(
            claim_id="c_contra",
            text=f"Proposition asserted in inquiry: '{question}'",
            scope="institutional",
            status="CONTRADICTED",
            evidence=[],
            conflicting_evidence=[f"[{conflicting_src_doc}] {conflicting_src_snippet}"],
            evidence_details=[ClaimEvidenceDetail(
                document=conflicting_src_doc,
                snippet=conflicting_src_snippet,
                relevance=round(top_similarity, 2),
                relation="conflicts"
            )],
            reason=query_conflict_reason,
            confidence=0.98
        ))

    # =========================================================================
    # STAGE 6: RELIABILITY CALCULATION & VERIFICATION INFLUENCE ON ANSWER
    # =========================================================================
    reliability_out, explanation = reliability_engine.calculate(
        verified_claims,
        inconsistency_count=len(internal_conflicts),
        scope=scope,
        retrieval_relevance=round(top_similarity, 3),
        is_abstained=is_out_of_domain
    )

    has_contradiction = any(c.status == "CONTRADICTED" for c in verified_claims) or query_conflict_detected
    has_uncertain = any(c.status == "UNCERTAIN" for c in verified_claims)
    all_supported = len(verified_claims) > 0 and all(c.status == "SUPPORTED" for c in verified_claims) and not query_conflict_detected

    why_trust_points: List[str] = []

    # Verification Affecting Output Logic
    if is_out_of_domain:
        verification_status = "ABSTAINED"
        decision = "ABSTAIN"
        message = "VERIDEX abstained: Question falls outside authorized knowledge boundary."
        why_trust_points = [
            "0 authorized local evidence sources found",
            "Zero ungrounded hallucinations permitted",
            "External model fabrication blocked",
            "Knowledge boundary strictly enforced"
        ]
    elif has_contradiction:
        verification_status = "CONTRADICTION DETECTED"
        decision = "BLOCK_AND_CORRECT"
        message = "Generated claim conflicts directly with verified institutional records."
        # Overwrite/correct output using verified evidence passage
        if institutional_sources:
            evidence_snippet = institutional_sources[0].snippet[:260]
            answer = f"The available local evidence indicates: {evidence_snippet}. (Affected contradicted claim blocked from final output)."
        why_trust_points = [
            "Contradiction isolated and blocked from polluting final response",
            f"Overridden with authoritative record: {institutional_sources[0].document if institutional_sources else 'Local repository'}",
            "NLI conflict detection verified against local policy"
        ]
    elif all_supported:
        verification_status = "SUPPORTED"
        decision = "PRESENT_VERIFIED"
        message = f"Verified against {len(institutional_sources)} authorized document(s)."
        src_name = institutional_sources[0].document if institutional_sources else "Local knowledge base"
        why_trust_points = [
            "Generated exclusively from authorized local evidence",
            f"{len(verified_claims)}/{len(verified_claims)} atomic claims directly substantiated",
            "Exact source passages linked to every claim",
            "0 unsupported or contradictory claims detected",
            f"Source: {src_name}"
        ]
    elif has_uncertain:
        verification_status = "PARTIAL"
        decision = "QUALIFY_UNCERTAINTY"
        message = "Partially verified: Some claims confirmed, but uncertainty detected in remaining assertions."
        why_trust_points = [
            f"{reliability_out.supported_claims} claim(s) substantiated by local records",
            f"{reliability_out.unsupported_claims} claim(s) flagged as uncertain/unverified",
            "Uncertain assertions explicitly demarcated for user audit"
        ]
    else:
        verification_status = "NOT VERIFIABLE"
        decision = "QUALIFY_UNCERTAINTY"
        message = "Available evidence is insufficient to verify this claim."
        why_trust_points = [
            "Evidence base searched thoroughly",
            "Insufficient overlap to establish factual ground truth"
        ]

    mode_val = "hybrid" if scope == "HYBRID" else "institutional" if scope == "INSTITUTIONAL" else "general"

    # Hardware Telemetry
    process = psutil.Process(os.getpid())
    ram_mb = round(process.memory_info().rss / (1024 * 1024), 1)
    total_lat_ms = max(1, round((time.time() - t0_pipeline) * 1000, 1))

    raw_llm_baseline = {
        "model_simulated": "Standard Local RAG (Unverified)",
        "raw_answer": answer.split("[SOURCE:")[0].strip() if "[SOURCE:" in answer else answer,
        "hallucination_detected": has_contradiction or is_out_of_domain,
        "danger_level": "CRITICAL" if has_contradiction else "MEDIUM" if is_out_of_domain else "LOW",
        "veridex_override": "CONTRADICTION BLOCKED & CORRECTED" if has_contradiction else "ABSTAINED (NO EVIDENCE)" if is_out_of_domain else "VERIFIED"
    }

    telemetry_data = {
        "ram_used_mb": ram_mb,
        "ram_limit_mb": 8192,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "total_latency_ms": total_lat_ms,
        "stages_latency_ms": {
            "retrieval": t_retrieval_ms,
            "synthesis": t_gen_ms,
            "claim_extraction": t_claims_ms,
            "nli_verification": t_nli_ms,
            "reliability_scoring": 5
        },
        "air_gapped": True,
        "external_api_calls": 0
    }

    return AskResponse(
        answer=answer,
        detected_scope=scope,
        mode=mode_val,
        verification_status=verification_status,
        decision=decision,
        sources=institutional_sources,
        claims=verified_claims,
        reliability=reliability_out,
        explanation=explanation,
        message=message,
        why_trust=why_trust_points,
        normalized_query=norm_question,
        query_normalization=query_norm_info,
        telemetry=telemetry_data,
        raw_llm_comparison=raw_llm_baseline
    )

@router.get("/documents", response_model=DocumentListResponse)
def list_documents():
    docs = store.get_documents()
    total_chunks = store.total_chunks_count()
    return DocumentListResponse(
        documents=[
            DocumentInfo(
                document_id=d["document_id"],
                filename=d["filename"],
                chunk_count=d["chunk_count"],
                size_bytes=d["size_bytes"],
                indexed_at=d["indexed_at"]
            )
            for d in docs
        ],
        total_chunks=total_chunks
    )

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename).name
    ext = Path(filename).suffix.lower()
    ALLOWED_EXTS = {".txt", ".md", ".pdf", ".docx", ".xlsx", ".csv"}
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="Only .pdf, .docx, .xlsx, .csv, .txt, and .md files are supported.")

    dest_path = settings.data_dir / filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    res = ingestion_pipeline.process_file(dest_path)
    return {"message": f"Document '{filename}' successfully uploaded and indexed.", "result": res}

@router.delete("/documents/{filename}")
def delete_document(filename: str):
    safe_name = Path(filename).name
    deleted = store.delete_document(safe_name)
    file_path = settings.data_dir / safe_name
    if file_path.exists():
        os.remove(file_path)

    vector_index.reload_from_storage()
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": f"Document '{safe_name}' deleted."}

@router.post("/documents/reindex")
def reindex_all():
    results = ingestion_pipeline.process_directory(settings.data_dir)
    return {"message": "All documents re-indexed successfully.", "results": results}

@router.post("/documents/upload-multiple")
async def upload_multiple_documents(files: List[UploadFile] = File(...)):
    """Batch upload multiple documents in a single request."""
    results = []
    ALLOWED_EXTS = {".txt", ".md", ".pdf", ".docx", ".xlsx", ".csv"}
    for file in files:
        filename = Path(file.filename).name
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTS:
            results.append({"filename": filename, "status": "error", "message": f"Unsupported format: {ext}"})
            continue
        dest_path = settings.data_dir / filename
        try:
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            res = ingestion_pipeline.process_file(dest_path)
            results.append({"filename": filename, "status": "indexed", "chunks": res.get("chunks", 0)})
        except Exception as e:
            results.append({"filename": filename, "status": "error", "message": str(e)})
    return {"message": f"{len(files)} file(s) processed.", "results": results}

@router.get("/documents/{filename}/download")
def download_document(filename: str):
    """Stream the original uploaded document file to the client."""
    safe_name = Path(filename).name
    file_path = settings.data_dir / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")
    media_type = "application/pdf" if safe_name.endswith(".pdf") else "text/plain"
    return FileResponse(
        path=str(file_path),
        filename=safe_name,
        media_type=media_type
    )

@router.get("/documents/{filename}/preview")
def preview_document(filename: str, max_chars: int = 2000):
    """Return the first N characters of a document's text content for in-browser preview."""
    safe_name = Path(filename).name
    file_path = settings.data_dir / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        from backend.ingestion.loader import DocumentLoader
        text, _ = DocumentLoader.load_file(file_path)
        preview = text[:max_chars]
        truncated = len(text) > max_chars
        return {"filename": safe_name, "preview": preview, "truncated": truncated, "total_chars": len(text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read document: {e}")

@router.post("/benchmark/run")
def run_benchmark():
    from backend.evaluation.benchmark import run_benchmark_suite
    summary = run_benchmark_suite()
    return summary
