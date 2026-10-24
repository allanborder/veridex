import re
from typing import List

class ClaimExtractor:
    """
    Deconstructs generated answers into atomic factual assertions.
    
    Principles:
    - Atomizes statements into independently auditable factual claims.
    - Strips citation tags and section prefixes (e.g. 'GENERAL:', 'INSTITUTIONAL:').
    - NEVER creates claims from the user's question.
    - NEVER creates meaningless claims like 'X is a recognized topic'.
    """
    def extract_claims(self, answer: str) -> List[str]:
        if not answer or answer.strip().startswith("No sufficient local evidence") or answer.strip().startswith("VERIDEX could not find"):
            return []

        # Remove source tags like [SOURCE: rec_001]
        cleaned = re.sub(r"\[SOURCE:\s*[^\]]+\]", "", answer).strip()
        
        # Remove hybrid section markers if present
        cleaned = re.sub(r"^(?:GENERAL|INSTITUTIONAL):\s*", "", cleaned, flags=re.MULTILINE)

        # Remove document memo headers if leaked into synthesis
        cleaned = re.sub(r"^(?:Mandatory\s+Minimum\s+Attendance|Medical\s+Condonation|Library\s+Operating\s+Hours)\s+", "", cleaned, flags=re.IGNORECASE)

        # Split into main sentences safely without breaking decimal numbers like 74.9%
        raw_sentences = [s.strip() for s in re.split(r'(?<!\d)(?<=[.?!])(?!\d)\s+', cleaned) if s.strip()]

        claims = []
        for s in raw_sentences:
            s_clean = s.strip(" ,.;")
            # Strip heading artifacts
            s_clean = re.sub(r"^(?:Section\s+\d+[^:]*:\s*|Medical\s+Condonation\s+|Mandatory\s+Minimum\s+Attendance\s+)", "", s_clean, flags=re.IGNORECASE).strip()
            if not s_clean or len(s_clean.split()) < 3:
                continue

            # Check if sentence contains multiple atomic propositions joined by coordinating conjunctions
            # Never split on percentage ranges or decimals (e.g. 65% and 74.9%)
            clauses = re.split(r'\s+(?:,\s*and|and(?=\s+(?:every|each|students|the|classes|regular|failure)\b)|while|whereas|;)\s*', s_clean, flags=re.IGNORECASE)
            
            if len(clauses) > 1 and all(len(c.split()) >= 4 for c in clauses):
                for c in clauses:
                    c_clean = c.strip(" ,.;")
                    if c_clean and len(c_clean.split()) >= 4:
                        c_clean = re.sub(r'^(?:and|while|whereas|but)\s+', '', c_clean, flags=re.IGNORECASE).strip()
                        claims.append(c_clean[0].upper() + c_clean[1:] + ".")
            else:
                claims.append(s_clean[0].upper() + s_clean[1:] + ".")

        # Filter out trivial, generic boilerplate claims
        filtered = []
        for c in claims:
            c_low = c.lower()
            if "recognized subject in general literature" in c_low or "recognized topic" in c_low:
                continue
            if len(c.split()) < 3:
                continue
            filtered.append(c)

        return filtered if filtered else [cleaned]

claim_extractor = ClaimExtractor()
