"""Content pipeline lifecycle, review stamping, and no-fake-metrics verification rules."""

import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

try:
    from backend.app.models.content_item import ContentItem, ContentStageEnum
except ImportError:
    from app.models.content_item import ContentItem, ContentStageEnum


REVIEW_MARKER = "[REVIEW REQUIRED]"

# Ordered stages: Idea -> Outline -> Draft -> Approved -> Published
STAGE_ORDER = [
    ContentStageEnum.IDEA.value,
    ContentStageEnum.OUTLINE.value,
    ContentStageEnum.DRAFT.value,
    ContentStageEnum.APPROVED.value,
    ContentStageEnum.PUBLISHED.value,
]

ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    ContentStageEnum.IDEA.value: [ContentStageEnum.OUTLINE.value, ContentStageEnum.DRAFT.value],
    ContentStageEnum.OUTLINE.value: [ContentStageEnum.IDEA.value, ContentStageEnum.DRAFT.value],
    ContentStageEnum.DRAFT.value: [ContentStageEnum.OUTLINE.value, ContentStageEnum.APPROVED.value],
    ContentStageEnum.APPROVED.value: [ContentStageEnum.DRAFT.value, ContentStageEnum.PUBLISHED.value],
    ContentStageEnum.PUBLISHED.value: [ContentStageEnum.APPROVED.value],
}

# Detect ungrounded performance claims that must not appear in engineering case studies without verification
SUSPICIOUS_METRIC_PATTERNS = [
    re.compile(r"\b\d+(?:\.\d+)?%\s*(?:faster|reduction|improvement|increase|latency drop|uptime|sla)\b", re.IGNORECASE),
    re.compile(r"\b\d+x\s*(?:faster|throughput|speedup|improvement|cheaper)\b", re.IGNORECASE),
    re.compile(r"\b(?:reduced|cut|improved)\s+(?:latency|cost|errors)\s+by\s+\d+(?:\.\d+)?%", re.IGNORECASE),
]


class TransitionValidationError(ValueError):
    """Raised when a content lifecycle transition violates approval or stage rules."""


class ContentMetrics(BaseModel):
    word_count: int
    reading_time_min: int
    code_blocks_count: int
    has_review_marker: bool
    benchmark_flags: List[str] = Field(default_factory=list)


class ContentPipeline:
    """Enforces 5-stage editorial pipeline, draft stamping, and honest metrics verification."""

    @staticmethod
    def slugify(title: str) -> str:
        base = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
        if not base:
            base = "content-piece"
        short_uid = uuid.uuid4().hex[:6]
        return f"{base[:64]}-{short_uid}"

    @classmethod
    def stamp_draft_review(cls, markdown: str) -> str:
        """Guarantees every generated draft carries a visible [REVIEW REQUIRED] banner."""
        cleaned = (markdown or "").strip()
        if REVIEW_MARKER in cleaned:
            return cleaned
        banner = f"> **{REVIEW_MARKER}** — Synthesized draft awaiting technical & factual review before approval.\n\n"
        return banner + cleaned

    @classmethod
    def inspect_no_fake_metrics(cls, markdown: str, verified_sources_count: int = 0) -> Tuple[str, List[str]]:
        """
        Inspects content for unverified quantitative benchmark claims.
        Replaces or flags ungrounded metric assertions with [BENCHMARK NEEDED].
        Never fabricates numbers.
        """
        flags: List[str] = []
        updated = markdown

        for pattern in SUSPICIOUS_METRIC_PATTERNS:
            for match in pattern.finditer(markdown):
                phrase = match.group(0)
                flags.append(f"Unverified metric claim detected: '{phrase}' -> marked [BENCHMARK NEEDED]")
                if "[BENCHMARK NEEDED]" not in updated[max(0, match.start() - 30):match.end() + 30]:
                    updated = updated.replace(phrase, f"{phrase} [BENCHMARK NEEDED]")

        if "[BENCHMARK NEEDED]" in updated and not flags:
            flags.append("Case study explicitly contains [BENCHMARK NEEDED] placeholders awaiting production telemetry.")

        return updated, flags

    @classmethod
    def compute_metrics(cls, markdown: str) -> ContentMetrics:
        text_only = re.sub(r"```[\s\S]*?```", "", markdown or "")
        words = [w for w in re.split(r"\s+", text_only.strip()) if w]
        word_count = len(words)
        reading_time_min = max(1, round(word_count / 200)) if word_count > 0 else 1
        code_blocks = len(re.findall(r"```", markdown or "")) // 2
        _, flags = cls.inspect_no_fake_metrics(markdown or "")
        return ContentMetrics(
            word_count=word_count,
            reading_time_min=reading_time_min,
            code_blocks_count=code_blocks,
            has_review_marker=REVIEW_MARKER in (markdown or ""),
            benchmark_flags=flags,
        )

    @classmethod
    def transition_stage(
        cls,
        item: ContentItem,
        target_stage: str,
        approved: bool = False,
        reviewer_id: Optional[uuid.UUID] = None,
    ) -> ContentItem:
        """
        Transitions a ContentItem across the 5-stage pipeline:
        Idea -> Outline -> Draft -> Approved -> Published
        Strict rules:
        - Auto-publishing prohibited: cannot jump from Idea/Outline/Draft directly to Published.
        - Moving to 'approved' requires explicit approved=True.
        - Moving to 'published' requires current stage == 'approved' and explicit approved=True.
        """
        current = item.stage
        target = target_stage.lower().strip()

        if target not in STAGE_ORDER:
            raise TransitionValidationError(f"Invalid target stage '{target_stage}'. Allowed: {STAGE_ORDER}")

        if target == current:
            return item

        allowed = ALLOWED_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise TransitionValidationError(
                f"Invalid pipeline transition '{current}' -> '{target}'. "
                f"Allowed next stages from '{current}': {allowed}. Auto-publish bypass is prohibited."
            )

        now = datetime.now(timezone.utc)

        if target == ContentStageEnum.APPROVED.value:
            if not approved:
                raise TransitionValidationError(
                    "Approval gate triggered: transitioning a draft to 'approved' requires explicit approval=True."
                )
            item.approved_by = reviewer_id
            item.approved_at = now

        if target == ContentStageEnum.PUBLISHED.value:
            if current != ContentStageEnum.APPROVED.value:
                raise TransitionValidationError(
                    "Cannot publish directly without prior 'approved' stage."
                )
            if not approved:
                raise TransitionValidationError(
                    "Auto-publish prohibited: transitioning to 'published' requires explicit human approval."
                )
            item.published_at = now
            if not item.approved_by and reviewer_id:
                item.approved_by = reviewer_id
                item.approved_at = now

        if target == ContentStageEnum.DRAFT.value:
            item.body_markdown = cls.stamp_draft_review(item.body_markdown)

        item.stage = target
        return item
