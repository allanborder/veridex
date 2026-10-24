import re

class TextParser:
    """
    Cleans, normalizes and extracts structural cues from raw text.
    """
    @staticmethod
    def clean_text(raw_text: str) -> str:
        if not raw_text:
            return ""
        # Normalize carriage returns and line endings
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        # Remove null bytes or non-printable controls
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Collapse multiple horizontal whitespace while preserving newlines
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse excess empty lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
