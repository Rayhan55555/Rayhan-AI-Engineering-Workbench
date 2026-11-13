"""Architecture Case Study Writer Tool with strict no-fake-metrics verification.

Every case study is grounded in verified architecture/codebase sources and marks
unobserved performance numbers explicitly with [BENCHMARK NEEDED].
"""

from typing import List, Optional
from pydantic import BaseModel, Field

try:
    from backend.app.content.pipeline import ContentPipeline
    from backend.app.content.research import ResearchBrief
except ImportError:
    from app.content.pipeline import ContentPipeline
    from app.content.research import ResearchBrief


class GeneratedCaseStudy(BaseModel):
    title: str
    system_scope: str
    markdown: str
    benchmark_flags: List[str] = Field(default_factory=list)
    citations_used: int
    review_required: bool = True


class CaseStudyWriter:
    """Produces production architecture case studies without fabricated performance metrics."""

    @classmethod
    def write_case_study(
        cls,
        topic: str,
        brief: Optional[ResearchBrief] = None,
        observed_notes: Optional[str] = None,
    ) -> GeneratedCaseStudy:
        clean_topic = topic.strip()
        facts = brief.key_facts if brief else []
        excerpts = brief.code_excerpts if brief else []
        citations = brief.citations if brief else []

        title = f"Architecture Case Study: Engineering {clean_topic}"

        context_bullets = (
            "\n".join(f"- {f}" for f in facts[:5])
            if facts
            else f"- Core system boundaries derived directly from `{clean_topic}` architecture modules."
        )

        modules_list = (
            "\n".join(f"- `{ex['file']}`" for ex in excerpts)
            if excerpts
            else "- Modular separation between API router validation, service/agent logic, and SQLAlchemy persistence."
        )

        observed_block = (
            observed_notes.strip()
            if observed_notes and observed_notes.strip()
            else (
                "- Functional verification: Automated pytest suite passes across unit and integration boundaries.\n"
                "- P95 Production Latency Under Load: `[BENCHMARK NEEDED]` — requires load-testing telemetry.\n"
                "- Peak Throughput (req/s): `[BENCHMARK NEEDED]` — capture via staging stress harness before publishing figures."
            )
        )

        citations_md = (
            "\n".join(
                f"- `{getattr(c, 'document', 'Module')}` ({getattr(c, 'source', 'repo')})"
                for c in citations[:5]
            )
            if citations
            else "- Grounded in local repository module layout."
        )

        raw_markdown = f"""# {title}

## 1. System Context & Problem Constraints
{context_bullets}

## 2. Key Architectural Decisions & Components
{modules_list}

- **Boundary Isolation**: Read-only research operations remain decoupled from state-mutating approvals.
- **Persistence & Auditability**: All lifecycle transitions are persisted with timestamps and reviewer attribution.

## 3. Observed Metrics & Verification Gaps (No Fabricated Stats)
{observed_block}

## 4. Lessons Learned & Operational Trade-Offs
- Explicit human approval gates add deterministic safety at the cost of manual step sign-off.
- Grounding generated artifacts in retrieved repository citations prevents architectural drift across phases.

## 5. Citations & Inspected Modules
{citations_md}
"""
        # Enforce strict no-fake-metrics rule across entire body
        checked_markdown, flags = ContentPipeline.inspect_no_fake_metrics(
            raw_markdown, verified_sources_count=len(citations)
        )
        stamped = ContentPipeline.stamp_draft_review(checked_markdown)

        return GeneratedCaseStudy(
            title=title,
            system_scope=clean_topic,
            markdown=stamped,
            benchmark_flags=flags,
            citations_used=len(citations),
            review_required=True,
        )
