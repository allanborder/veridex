import re
from typing import List, Tuple

class ConsistencyChecker:
    """
    Evaluates claims against each other without requiring external evidence.
    Identifies internal contradictions generated within the same response.
    """
    def check_consistency(self, claims: List[str]) -> List[Tuple[int, int, str]]:
        """
        Returns list of (claim_idx_1, claim_idx_2, reason) of internal contradictions.
        """
        conflicts = []
        if len(claims) < 2:
            return conflicts

        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1 = claims[i].lower()
                c2 = claims[j].lower()

                # Check for clock time contradictions between statements (e.g., 9:00 AM vs 8:00 PM)
                time_pat = r'\b(\d{1,2}:\d{2}(?:\s*[ap]m)?|\d{1,2}\s*[ap]m)\b'
                t1 = set(re.findall(time_pat, c1))
                t2 = set(re.findall(time_pat, c2))

                # Check shared subject
                words1 = set(re.findall(r'\w+', c1))
                words2 = set(re.findall(r'\w+', c2))
                subject_overlap = len(words1.intersection(words2))

                # Do not trigger internal conflict if one statement is an explicit negative clarifying the other
                # (e.g. "schedule is 8 AM to 9 PM" and "does NOT close at 8 PM")
                has_negation_1 = "not" in words1 or "never" in words1
                has_negation_2 = "not" in words2 or "never" in words2

                if subject_overlap >= 4 and t1 and t2 and (has_negation_1 == has_negation_2):
                    p1_clean = {re.sub(r'\s+', '', t) for t in t1}
                    p2_clean = {re.sub(r'\s+', '', t) for t in t2}
                    if not p1_clean.intersection(p2_clean):
                        conflicts.append((
                            i,
                            j,
                            f"Internal conflict: Claim {i+1} mentions {list(t1)[0]} while Claim {j+1} asserts {list(t2)[0]}."
                        ))

        return conflicts

consistency_checker = ConsistencyChecker()
