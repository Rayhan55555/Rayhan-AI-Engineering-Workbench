import re
from typing import List, Tuple

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b"),
    re.compile(r"(?i)\byou\s+are\s+now\s+DAN\b"),
    re.compile(r"(?i)\bsystem\s+override\b"),
    re.compile(r"(?i)\bdisregard\s+safety\s+guidelines\b"),
]

MAX_PROMPT_CHARS = 12000


class PromptValidator:
    """
    Validates user prompts for length limits and obvious jailbreak attempts.
    """
    @staticmethod
    def validate(text: str) -> Tuple[bool, str]:
        if len(text.strip()) < 3:
            return False, "Prompt is too short (minimum 3 characters required)."
        if len(text) > MAX_PROMPT_CHARS:
            return False, f"Prompt exceeds maximum character length of {MAX_PROMPT_CHARS}."

        for pat in PROMPT_INJECTION_PATTERNS:
            if pat.search(text):
                return False, "Input rejected: potential prompt injection pattern detected."

        return True, "Valid"

    @staticmethod
    def sanitize(text: str) -> str:
        # Strip potential API key leakage patterns
        cleaned = re.sub(r"AIza[0-9A-Za-z\-_]{30,}", "[REDACTED_GEMINI_KEY]", text)
        cleaned = re.sub(r"sk-ant-[0-9A-Za-z\-_]{20,}", "[REDACTED_CLAUDE_KEY]", cleaned)
        return cleaned

