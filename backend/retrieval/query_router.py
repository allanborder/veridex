import re
from typing import List, Tuple, Literal, Optional
from backend.models.schemas import SourceRecord
from backend.config import settings

class QueryRouter:
    """
    Scope Detector & Query Router for VERIDEX.
    
    Classifies the user question into:
    - INSTITUTIONAL: Queries about campus, library, attendance, semester dates, scholarships, hostel, etc.
    - GENERAL: General technical, scientific, historical, or conceptual inquiries (e.g. Python, ML vs DS).
    - HYBRID: Contains both general technical inquiry and institutional campus verification.
    
    The local knowledge base serves as a TRUST ANCHOR, not a restriction.
    """
    
    INSTITUTIONAL_KEYWORDS = {
        "library", "attendance", "semester", "exam", "examination", "scholarship",
        "campus", "college", "university", "school", "dean", "hod", "fee", "fees", "hostel",
        "disbarred", "condonation", "course", "curriculum", "syllabus", "credit",
        "hall ticket", "regulations", "policy", "cgpa", "gpa", "block c", "borrowing",
        "book", "circulation", "working hours", "timing", "schedule", "operating hours", "hours",
        # Tamil Nadu & Public Affairs keywords
        "tamil nadu", "tamilnadu", "chennai", "district", "districts", "collectorate",
        "panchayat", "corporation", "municipality", "esevai", "tnega", "pds",
        "ration", "cmchistn", "naan mudhalvan", "pudhumai penn", "tnhb", "tidco",
        "sipcot", "government order", "secretariat", "tnpsc", "state", "taluk", "revenue"
    }

    CAMPUS_PHRASES = [
        "our college", "our campus", "our university", "in college", "in campus",
        "in university", "does our", "do we have", "is there a course", "offer a",
        "offer an", "at our", "on campus", "in tamil nadu", "of tamil nadu", "state government"
    ]

    def detect_scope(self, question: str, sources: List[SourceRecord]) -> Tuple[Literal["INSTITUTIONAL", "GENERAL", "HYBRID"], Optional[str], Optional[str]]:
        """
        Returns (scope, general_part, institutional_part).
        """
        q_lower = question.lower()

        # Check for hybrid patterns:
        has_campus_phrase = any(phrase in q_lower for phrase in self.CAMPUS_PHRASES)
        
        has_institution_keyword = any(
            re.search(r'\b' + re.escape(kw) + r'\b', q_lower) 
            for kw in self.INSTITUTIONAL_KEYWORDS
        )

        has_general_signals = any(
            phrase in q_lower for phrase in [
                # Question starters
                "what is", "what are", "what does", "what was", "what were",
                "who is", "who was", "who invented", "who created", "who discovered",
                "how does", "how do", "how is", "how are", "how was",
                "explain", "describe", "define", "tell me about",
                "difference between", "compare", "vs ", " versus ",
                "why is", "why are", "why does", "why do",
                "when was", "when did", "when is",
                "where is", "where does",
                # Tech / CS / AI domains
                "machine learning", "deep learning", "neural network", "artificial intelligence",
                "data science", "python", "java", "javascript", "programming",
                "algorithm", "data structure", "recursion", "sorting", "binary",
                "blockchain", "cryptocurrency", "bitcoin", "cloud computing",
                "operating system", "linux", "database", "sql", "api",
                "internet", "networking", "tcp", "http", "encryption",
                "cybersecurity", "hacking", "malware", "firewall",
                # Science / Math
                "quantum", "relativity", "thermodynamics", "photosynthesis",
                "gravity", "evolution", "dna", "genome",
                "calculus", "algebra", "statistics", "probability",
                # Institutions outside campus context
                "harvard", "mit", "stanford", "oxford", "cambridge",
                "nasa", "google", "apple", "microsoft", "amazon",
                "nobel", "turing", "einstein", "newton",
                # General phrasing
                "is machine learning", "is python", "is data science the same",
                "and data science", "is the same", "are the same",
                "tuition cost", "how much does",
            ]
        )

        # Detect Hybrid
        if (has_campus_phrase or (has_institution_keyword and "does our" in q_lower)) and has_general_signals and not has_institution_keyword:
            parts = re.split(r'\s+(?:and|also|while|but)\s+', question, flags=re.IGNORECASE)
            if len(parts) >= 2:
                gen_part = parts[0].strip()
                inst_part = " ".join(parts[1:]).strip()
                return "HYBRID", gen_part, inst_part
            return "HYBRID", question, question

        # Pure Institutional / Authorized Corpus:
        top_similarity = sources[0].similarity if sources else 0.0
        if has_institution_keyword or top_similarity >= 0.40:
            return "INSTITUTIONAL", None, question

        if top_similarity >= settings.min_similarity and not has_general_signals:
            return "INSTITUTIONAL", None, question

        # Otherwise General
        return "GENERAL", question, None

    def route(
        self, 
        question: str,
        sources: List[SourceRecord], 
        min_similarity: float = None
    ) -> Tuple[Literal["INSTITUTIONAL", "GENERAL", "HYBRID"], List[SourceRecord], Optional[str], Optional[str]]:
        threshold = min_similarity if min_similarity is not None else settings.min_similarity
        
        scope, gen_part, inst_part = self.detect_scope(question, sources)

        # For institutional or hybrid, filter relevant local evidence
        valid_sources = [s for s in sources if s.similarity >= threshold]
        
        return scope, valid_sources, gen_part, inst_part

query_router = QueryRouter()
