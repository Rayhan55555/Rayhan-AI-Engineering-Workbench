"""Unit tests for Phase 12 Content Pipeline & Verification Rules."""

import uuid
import pytest

from backend.app.content.pipeline import (
    ContentPipeline,
    TransitionValidationError,
    REVIEW_MARKER,
)
from backend.app.models.content_item import ContentItem, ContentStageEnum


def test_draft_always_stamped_review_required():
    """Every draft must prominently contain [REVIEW REQUIRED]."""
    raw = "# Deep Dive on Vector Search\n\nTechnical breakdown..."
    stamped = ContentPipeline.stamp_draft_review(raw)
    assert REVIEW_MARKER in stamped
    # Idempotent if already present
    stamped_twice = ContentPipeline.stamp_draft_review(stamped)
    assert stamped_twice.count(REVIEW_MARKER) == 1


def test_no_fake_metrics_flags_unverified_claims():
    """Unverified percentage or multiplier performance claims are flagged [BENCHMARK NEEDED]."""
    fabricated = (
        "# System Overview\n\n"
        "This redesign achieved 99.9% uptime and ran 10x faster throughput while achieving "
        "45% reduction in latency across microservices."
    )
    checked, flags = ContentPipeline.inspect_no_fake_metrics(fabricated)
    assert "[BENCHMARK NEEDED]" in checked
    assert len(flags) >= 2


def test_pipeline_strict_five_stage_lifecycle():
    """Verify Idea -> Outline -> Draft -> Approved -> Published with strict approval gates."""
    reviewer_id = uuid.uuid4()
    item = ContentItem(
        id=uuid.uuid4(),
        title="Testing Pipeline Boundaries",
        slug="testing-pipeline-boundaries-123",
        content_type="article",
        stage=ContentStageEnum.IDEA.value,
        channel="blog",
        body_markdown="# Initial Idea",
        summary="Summary",
    )

    # 1. Idea -> Outline
    ContentPipeline.transition_stage(item, "outline")
    assert item.stage == "outline"

    # 2. Cannot jump Outline -> Published (auto-publish prohibited)
    with pytest.raises(TransitionValidationError):
        ContentPipeline.transition_stage(item, "published", approved=True, reviewer_id=reviewer_id)

    # 3. Outline -> Draft (automatically stamps [REVIEW REQUIRED])
    ContentPipeline.transition_stage(item, "draft")
    assert item.stage == "draft"
    assert REVIEW_MARKER in item.body_markdown

    # 4. Cannot approve without approved=True
    with pytest.raises(TransitionValidationError, match="requires explicit approval=True"):
        ContentPipeline.transition_stage(item, "approved", approved=False, reviewer_id=reviewer_id)

    # 5. Approve with approved=True
    ContentPipeline.transition_stage(item, "approved", approved=True, reviewer_id=reviewer_id)
    assert item.stage == "approved"
    assert item.approved_by == reviewer_id
    assert item.approved_at is not None

    # 6. Cannot publish without approved=True
    with pytest.raises(TransitionValidationError):
        ContentPipeline.transition_stage(item, "published", approved=False, reviewer_id=reviewer_id)

    # 7. Publish with explicit approval
    ContentPipeline.transition_stage(item, "published", approved=True, reviewer_id=reviewer_id)
    assert item.stage == "published"
    assert item.published_at is not None
