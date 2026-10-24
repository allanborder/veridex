import re
import difflib
from typing import Tuple, Optional, Dict, Set

class QueryNormalizer:
    """
    Robust query normalization & lightweight typo correction for VERIDEX.
    
    Principles:
    1. Case insensitivity (safe normalization).
    2. Punctuation and whitespace cleanup without destroying meaning.
    3. Lightweight vocabulary-backed typo correction for common domain terms.
    4. Conservative behavior: preserves query intent and never blindly replaces proper nouns.
    5. Query expansion for temporal start/finish / open/close semantics.
    """
    
    # Common academic & institutional domain vocabulary
    DOMAIN_VOCABULARY: Dict[str, str] = {
        # Typos -> standard domain term
        "schol": "school",
        "scool": "school",
        "schoo": "school",
        "shool": "school",
        "timng": "timing",
        "timmings": "timing",
        "timmimg": "timing",
        "timings": "timing",
        "attendence": "attendance",
        "atendance": "attendance",
        "attandance": "attendance",
        "attndance": "attendance",
        "libary": "library",
        "librry": "library",
        "libarary": "library",
        "exm": "exam",
        "exms": "exams",
        "examinaton": "examination",
        "examinatons": "examinations",
        "examinations": "examinations",
        "semster": "semester",
        "semister": "semester",
        "schlarship": "scholarship",
        "scolarship": "scholarship",
        "hostle": "hostel",
        "polcy": "policy",
        "plocy": "policy",
        "requirment": "requirement",
        "requirments": "requirements",
        "minmum": "minimum",
        "manadatory": "mandatory",
        "operatng": "operating",
        "oprating": "operating",
        "clos": "close",
        "clsoing": "closing",
        "schedul": "schedule",
        "schedual": "schedule",
        # Tamil Nadu & geography typos (both spaced and compound forms)
        "tamilnadu": "tamil nadu",   # compound no-space form — single token
        "tamilandu": "tamil nadu",
        "tamilnad": "tamil nadu",
        "tamilndu": "tamil nadu",
        "tamilnaadu": "tamil nadu",
        "tnadu": "tamil nadu",
        # District / geography
        "distrcts": "districts",
        "distrct": "district",
        "distric": "district",
        "districs": "districts",
        "distrcits": "districts",
        "headquater": "headquarters",
        "headquaters": "headquarters",
        "headqurter": "headquarters",
        "locted": "located",
        "locatin": "location",
        # People / governance
        "minstr": "minister",
        "ministr": "minister",
        "cheif": "chief",
        "goverment": "government",
        "govrnment": "government",
        "capitl": "capital",
        "captial": "capital",
    }

    # Slang & colloquial expansions
    COLLOQUIAL_MAP: Dict[str, str] = {
        "wat": "what",
        "wats": "what is",
        "wht": "what",
        "wen": "when",
        "hw": "how",
        "mny": "many",
        "r": "are",
        "thr": "there",
        "plz": "please",
        "pls": "please",
        "hrs": "hours",
        "hr": "hour"
    }

    # Canonical dictionary of domain words to check fuzzy distance against
    KNOWN_WORDS: Set[str] = {
        "school", "hours", "timing", "timings", "schedule", "open", "close", "start", "finish",
        "library", "attendance", "minimum", "mandatory", "requirement", "medical", "condonation",
        "examination", "exam", "rules", "calculator", "scholarship", "guidelines", "quota", "borrowing",
        "campus", "college", "university", "academic", "policy", "regulations", "students", "lecture",
        "tamil", "nadu", "chennai", "district", "districts", "minister", "chief", "governance",
        "located", "location", "capital", "headquarters", "government", "population", "language"
    }

    def clean_text(self, text: str) -> str:
        """
        Normalize whitespace and standard punctuation while preserving questions and digits.
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text).strip()
        return cleaned

    def normalize(self, query: str) -> Tuple[str, bool, Optional[str]]:
        """
        Normalizes query for retrieval.
        Returns: (normalized_query, was_modified, explanation)
        """
        raw = query.strip()
        if not raw:
            return "", False, None

        # 1. Clean extra whitespace
        cleaned = re.sub(r'\s+', ' ', raw)

        # 2. Tokenize into words preserving punctuation
        tokens = re.findall(r"[A-Za-z0-9]+|[^\w\s]", cleaned)

        modified = False
        normalized_tokens = []
        corrections = []

        for token in tokens:
            lower_token = token.lower()
            
            # Check colloquial map
            if lower_token in self.COLLOQUIAL_MAP:
                replacement = self.COLLOQUIAL_MAP[lower_token]
                normalized_tokens.append(replacement)
                modified = True
                corrections.append(f"'{token}' -> '{replacement}'")
                continue

            # Check exact typo dictionary
            if lower_token in self.DOMAIN_VOCABULARY:
                replacement = self.DOMAIN_VOCABULARY[lower_token]
                normalized_tokens.append(replacement)
                modified = True
                corrections.append(f"'{token}' -> '{replacement}'")
                continue

            # Fuzzy match only for alphabetic words of length >= 4 that are NOT in known domain words
            if len(lower_token) >= 4 and lower_token.isalpha() and lower_token not in self.KNOWN_WORDS:
                # Find close matches in KNOWN_WORDS
                matches = difflib.get_close_matches(lower_token, list(self.KNOWN_WORDS), n=1, cutoff=0.82)
                if matches and matches[0] != lower_token:
                    replacement = matches[0]
                    normalized_tokens.append(replacement)
                    modified = True
                    corrections.append(f"'{token}' -> '{replacement}'")
                    continue

            # Keep token as is
            normalized_tokens.append(token)

        # Reconstruct normalized string cleanly
        norm_str = ""
        for i, tok in enumerate(normalized_tokens):
            if re.match(r'^[,\.?!;:]$', tok):
                norm_str = norm_str.rstrip() + tok
            else:
                if norm_str and not norm_str.endswith(" "):
                    norm_str += " "
                norm_str += tok

        explanation = f"Normalized: {', '.join(corrections)}" if corrections else None
        return norm_str, modified, explanation

    def expand_query_intent(self, query: str) -> str:
        """
        Lightweight semantic expansion to pull vector search toward the correct
        document type. Preserves the original query as the primary anchor.
        """
        q_lower = query.lower()
        additions = []

        # ── Geography / Location queries ──────────────────────────────────────
        # "in which part", "where is X located", "which state", "which region"
        if any(term in q_lower for term in [
            "in which part", "in which region", "in which area",
            "where is", "where does", "where located",
            "which part", "which state", "which country",
            "geographically", "geograph"
        ]):
            additions.append("located situated southern northern eastern western region state")

        # ── District / count queries ──────────────────────────────────────────
        if any(term in q_lower for term in [
            "how many districts", "number of districts", "total districts",
            "district count", "many districts"
        ]):
            additions.append("districts headquarters administrative divisions")

        # ── Capital city queries ──────────────────────────────────────────────
        if any(term in q_lower for term in ["capital", "capital city", "capital of"]):
            additions.append("capital city Chennai headquarters")

        # ── Operating hours & schedule variations ────────────────────────────
        if any(term in q_lower for term in ["start and finish", "start and close", "open and close", "start and end", "begin and end"]):
            if "hours" not in q_lower and "schedule" not in q_lower:
                additions.append("hours schedule timing")

        if any(term in q_lower for term in ["when does school start", "what time does school start", "when does school open"]):
            if "hours" not in q_lower:
                additions.append("operating hours schedule")

        # ── Exam commencement & dates ─────────────────────────────────────────
        if any(term in q_lower for term in ["when do exams start", "when does exam start", "exam start", "exams start", "exam date", "exams date"]):
            additions.append("semester examination schedule commence")

        if additions:
            return f"{query} {' '.join(additions)}"
        return query

query_normalizer = QueryNormalizer()
