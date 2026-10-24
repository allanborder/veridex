import pytest
from backend.ingestion.parser import TextParser
from backend.ingestion.chunker import DocumentChunker
from backend.verification.claim_extractor import claim_extractor
from backend.verification.nli_verifier import nli_verifier
from backend.verification.consistency import consistency_checker
from backend.verification.reliability import reliability_engine
from backend.models.schemas import ClaimVerification

def test_chunking_and_parsing():
    raw = "Section 1: Test\r\n\r\nThis is paragraph one with several words.\n\nParagraph two."
    clean = TextParser.clean_text(raw)
    assert "\r" not in clean
    chunker = DocumentChunker(chunk_size=10, overlap=2)
    chunks = chunker.chunk_document(clean, "test.md", "doc123")
    assert len(chunks) >= 1

def test_claim_extraction():
    ans = "The library closes at 9 PM on weekdays. The library closes at 6 PM on weekends. [SOURCE: rec_001]"
    claims = claim_extractor.extract_claims(ans)
    assert len(claims) >= 2
    assert any("9 PM" in c for c in claims)

def test_nli_support():
    evidence = "The library closes at 9 PM on weekdays."
    claim = "The library closes at 9 PM on weekdays."
    res = nli_verifier.verify(evidence, claim)
    assert res["label"] == "support"

def test_nli_contradiction():
    evidence = "The library closes at 9 PM on weekdays."
    claim = "The library closes at 8 PM on weekdays."
    res = nli_verifier.verify(evidence, claim)
    assert res["label"] == "contradiction"

def test_internal_inconsistency():
    claims = [
        "The library closes at 8 PM.",
        "The library closes at 9 PM."
    ]
    conflicts = consistency_checker.check_consistency(claims)
    assert len(conflicts) > 0

def test_reliability_scoring():
    claims = [
        ClaimVerification(claim_id="c1", text="Supported claim", status="VERIFIED — LOCAL", evidence=["test"], reason="OK"),
        ClaimVerification(claim_id="c2", text="Neutral claim", status="neutral", evidence=[], reason="Neutral")
    ]
    rel, expl = reliability_engine.calculate(claims, scope="INSTITUTIONAL")
    assert rel.score is not None
    assert 0.0 <= rel.score <= 1.0
    assert rel.verdict in ["VERIFIED", "PARTIAL", "PARTIALLY VERIFIED", "CONTRADICTION DETECTED"]

    # General mode test
    gen_claims = [
        ClaimVerification(claim_id="c3", text="General claim", status="UNVERIFIED — GENERAL", evidence=[], reason="General knowledge")
    ]
    gen_rel, gen_expl = reliability_engine.calculate(gen_claims, scope="GENERAL")
    assert gen_rel.score is None
    assert gen_rel.verdict == "UNVERIFIED — GENERAL"

def test_hard_evidence_gate():
    from backend.verification.evidence_matcher import evidence_matcher
    from backend.models.schemas import SourceRecord

    # Irrelevant sources must be discarded by the evidence gate
    fake_sources = [
        SourceRecord(record_id="r1", document="05_Health_and_Public_Health.md", snippet="The Chief Minister's Comprehensive Health Insurance Scheme provides cashless health coverage.", similarity=0.35),
        SourceRecord(record_id="r2", document="Attendance_Policy.md", snippet="Mandatory minimum attendance is 75 percent.", similarity=0.30)
    ]
    relevant = evidence_matcher.filter_relevant_evidence("Who is the Chief Minister of Tamil Nadu?", fake_sources)
    assert len(relevant) == 0

    # Relevant sources must pass
    valid_sources = [
        SourceRecord(record_id="r3", document="Attendance_Policy.md", snippet="Mandatory minimum attendance requirement is 75% for all students.", similarity=0.45)
    ]
    passed = evidence_matcher.filter_relevant_evidence("What is the mandatory attendance requirement?", valid_sources)
    assert len(passed) == 1

