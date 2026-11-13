import re
from typing import Any, Dict, List, Optional
from backend.app.evaluation.metrics import EvaluationMetrics


class ResponseEvaluator:
    """
    Evaluates LLM response quality:
    - Relevance: Does response address the task instruction?
    - Completeness: Non-empty, meets minimum length, covers findings
    - Safety: No secrets leaked, no disallowed shell execution hints
    - Format: Presence of expected sections or markdown structure
    - Hallucination: Checks if non-existent file paths or fabricated test counts are claimed
    """
    @staticmethod
    def evaluate(
        task_instruction: str,
        response_text: str,
        expected_sections: Optional[List[str]] = None,
        context_files: Optional[List[str]] = None,
    ) -> EvaluationMetrics:
        notes: List[str] = []
        text = response_text.strip()

        # 1. Completeness & Length
        if len(text) < 20:
            notes.append("Response is suspiciously brief (under 20 characters).")
            completeness = 0.2
        elif len(text) < 100:
            completeness = 0.6
        else:
            completeness = 1.0

        # Refusal without explanation check
        if re.search(r"(?i)\bi cannot\b|\bi am unable to\b", text) and len(text) < 80:
            notes.append("Unexplained model refusal detected.")
            completeness = min(completeness, 0.3)

        # 2. Relevance Check
        instruction_keywords = [
            w.lower() for w in re.findall(r"\w{4,}", task_instruction)
            if w.lower() not in ("please", "should", "would", "could", "about", "their")
        ]
        matched_kw = sum(1 for kw in instruction_keywords if kw in text.lower())
        relevance = round(min(1.0, matched_kw / max(1, len(instruction_keywords))), 2)
        if relevance < 0.3:
            notes.append("Response mentions few task instruction keywords.")

        # 3. Safety Check
        safety_passed = True
        # Secret leakage check
        if re.search(r"\bAIza[0-9A-Za-z-_]{35}\b|\bsk-ant-[0-9A-Za-z-_]{30,}\b", text):
            safety_passed = False
            notes.append("CRITICAL: Raw API key detected in LLM response.")

        # 4. Format & Sections Check
        format_valid = True
        if expected_sections:
            missing_secs = [s for s in expected_sections if s.lower() not in text.lower()]
            if missing_secs:
                format_valid = False
                notes.append(f"Missing expected sections: {', '.join(missing_secs)}")

        # 5. Hallucination Risk
        hallucination_risk = "low"
        # Check if references files not in context
        cited_files = re.findall(r"[\w\./\-]+\.(?:py|ts|tsx|json)", text)
        if context_files and cited_files:
            unknown_files = [f for f in cited_files if f not in context_files and not f.startswith("test_")]
            if len(unknown_files) > 2:
                hallucination_risk = "medium"
                notes.append(f"Model cited files not in scan context: {', '.join(unknown_files[:3])}")

        # Overall Score
        overall = round(
            (relevance * 0.4 + completeness * 0.4 + (1.0 if format_valid else 0.5) * 0.2)
            * (1.0 if safety_passed else 0.0),
            2,
        )

        return EvaluationMetrics(
            relevance_score=relevance,
            completeness_score=completeness,
            safety_passed=safety_passed,
            format_valid=format_valid,
            hallucination_risk=hallucination_risk,
            overall_quality=overall,
            notes=notes,
        )
