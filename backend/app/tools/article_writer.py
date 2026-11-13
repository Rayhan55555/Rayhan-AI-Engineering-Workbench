"""Article Writer Tool for Technical Deep Dives and Step-by-Step Developer Tutorials.

Editorial voice: Principal systems engineer & technical founder.
Every draft is stamped [REVIEW REQUIRED] and grounded in RAG citations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

try:
    from backend.app.content.pipeline import ContentPipeline
    from backend.app.content.research import ResearchBrief
except ImportError:
    from app.content.pipeline import ContentPipeline
    from app.content.research import ResearchBrief


class GeneratedArticle(BaseModel):
    title: str
    mode: str  # "deep_dive" or "tutorial"
    summary: str
    markdown: str
    word_count: int
    reading_time_min: int
    citations_used: int
    review_required: bool = True


class ArticleWriter:
    """Synthesizes engineering deep dives and step-by-step developer tutorials."""

    @classmethod
    def write_article(
        cls,
        topic: str,
        mode: str = "deep_dive",
        brief: Optional[ResearchBrief] = None,
        outline_only: bool = False,
    ) -> GeneratedArticle:
        clean_topic = topic.strip()
        mode_norm = "tutorial" if mode.lower().strip() == "tutorial" else "deep_dive"
        facts = brief.key_facts if brief else []
        excerpts = brief.code_excerpts if brief else []
        citations = brief.citations if brief else []

        if mode_norm == "tutorial":
            title = f"Implementing {clean_topic}: A Production Engineering Walkthrough"
            summary = (
                f"Step-by-step developer tutorial covering architecture setup, safe implementation patterns, "
                f"and verification tests for {clean_topic}."
            )
            if outline_only:
                body = cls._build_tutorial_outline(clean_topic, facts)
            else:
                body = cls._build_tutorial_draft(clean_topic, facts, excerpts, citations)
        else:
            title = f"Inside {clean_topic}: Architectural Trade-offs & Production Boundaries"
            summary = (
                f"Principal systems engineering deep dive examining failure modes, permission boundaries, "
                f"and design rationale behind {clean_topic}."
            )
            if outline_only:
                body = cls._build_deep_dive_outline(clean_topic, facts)
            else:
                body = cls._build_deep_dive_draft(clean_topic, facts, excerpts, citations)

        stamped = ContentPipeline.stamp_draft_review(body)
        metrics = ContentPipeline.compute_metrics(stamped)

        return GeneratedArticle(
            title=title,
            mode=mode_norm,
            summary=summary,
            markdown=stamped,
            word_count=metrics.word_count,
            reading_time_min=metrics.reading_time_min,
            citations_used=len(citations),
            review_required=True,
        )

    @classmethod
    def _build_deep_dive_outline(cls, topic: str, facts: List[str]) -> str:
        fact_bullets = "\n".join(f"  - Grounded Anchor: {f}" for f in facts[:3]) or "  - Grounded Anchor: System module inspection"
        return f"""# Inside {topic}: Architectural Trade-offs & Production Boundaries

## Structured Outline
1. **Why Naive Implementations Fail in Production**
   - Silent failure modes, permission boundary leaks, and ungrounded outputs
2. **Core System Topology & Invariants**
{fact_bullets}
3. **Failure Modes, Guardrails & Safety Gates**
   - Explicit approval boundaries and rollback invariants
4. **Operational Trade-offs**
   - Latency vs. determinism and strict schema validation
5. **Key Engineering Takeaways**
"""

    @classmethod
    def _build_tutorial_outline(cls, topic: str, facts: List[str]) -> str:
        fact_bullets = "\n".join(f"  - Reference: {f}" for f in facts[:3]) or "  - Reference: Existing project interfaces"
        return f"""# Implementing {topic}: A Production Engineering Walkthrough

## Tutorial Outline
1. **Prerequisites & Environment Boundaries**
2. **Step 1: Defining Data Contracts & Safety Invariants**
{fact_bullets}
3. **Step 2: Core Pipeline Implementation**
4. **Step 3: Integrating Verification & Regression Tests**
5. **Production Checklist & Next Steps**
"""

    @classmethod
    def _build_deep_dive_draft(
        cls,
        topic: str,
        facts: List[str],
        excerpts: List[dict],
        citations: List[object],
    ) -> str:
        facts_section = (
            "\n".join(f"- {f}" for f in facts[:5])
            if facts
            else f"- Core system boundaries derived directly from workbench architecture for `{topic}`."
        )
        code_section = ""
        if excerpts:
            first = excerpts[0]
            code_section = f"""
### Grounded Implementation Snapshot (`{first['file']}`)

```python
{first['snippet']}
```
"""
        citations_section = (
            "\n".join(
                f"- `{getattr(c, 'document', 'Source')}` ({getattr(c, 'source', 'repo')}) — relevance `{getattr(c, 'score', 0.0)}`"
                for c in citations[:5]
            )
            if citations
            else "- No external RAG chunks matched verbatim; assertions reflect structural workbench invariants."
        )

        return f"""# Inside {topic}: Architectural Trade-offs & Production Boundaries

When engineering teams move **{topic}** from a weekend prototype into a multi-tenant production system, the hardest problems rarely live inside the happy path. They emerge at the seams: state transitions, permission boundaries, schema drift, and silent hallucinations.

As builders, we optimize for explicit contracts over implicit magic. Below is an engineering breakdown of how **{topic}** is structured to hold up under real operational constraints.

## 1. Grounded Architectural Context

{facts_section}
{code_section}
## 2. Core Design Trade-Offs

1. **Determinism vs. Flexibility**: Unconstrained pipelines are easy to demo and fragile to operate. Enforcing typed schemas and explicit stage boundaries adds upfront boilerplate, but eliminates entire classes of runtime surprises.
2. **Human-in-the-Loop Approval Gates**: Autonomous execution ends where irreversible state mutation begins. Separating `READ_ONLY` and `SUGGEST` analysis from `IMPLEMENT` / `PUBLISHED` actions guarantees an auditable safety boundary.
3. **Honest Telemetry Over Vanity Metrics**: Every latency, coverage, or accuracy figure must trace back to an observed run or remain explicitly marked `[BENCHMARK NEEDED]` until measured under load.

## 3. Operational Checklist Before Shipping

- Validate schema invariants and migration paths before runtime deployment.
- Keep audit trails immutable across every state transition and approval event.
- Verify automated regression suites pass across both unit and integration boundaries.

## References & Grounding Sources

{citations_section}
"""

    @classmethod
    def _build_tutorial_draft(
        cls,
        topic: str,
        facts: List[str],
        excerpts: List[dict],
        citations: List[object],
    ) -> str:
        facts_section = (
            "\n".join(f"- {f}" for f in facts[:4])
            if facts
            else f"- Align module boundaries with strict Pydantic contracts and async SQLAlchemy sessions."
        )
        code_block = (
            f"```python\n# Reference: {excerpts[0]['file']}\n{excerpts[0]['snippet']}\n```"
            if excerpts
            else """```python
# Core pattern: validate preconditions before mutating persistent state
async def execute_step(item_id: str, approved: bool = False) -> dict:
    if not approved:
        raise PermissionError("Explicit review approval required before mutation.")
    return {"item_id": item_id, "status": "verified"}
```"""
        )
        citations_section = (
            "\n".join(
                f"- `{getattr(c, 'document', 'Doc')}` — `{getattr(c, 'source', 'codebase')}`"
                for c in citations[:5]
            )
            if citations
            else "- Workbench internal implementation patterns."
        )

        return f"""# Implementing {topic}: A Production Engineering Walkthrough

In this hands-on guide, we build **{topic}** cleanly from first principles: strict data models, deterministic state transitions, explicit approval gates, and automated verification tests.

## Prerequisites & Context

{facts_section}

## Step 1: Establish Strict Type Contracts

Before writing business logic, lock down input validation and state invariants so invalid payloads fail fast at the API boundary.

## Step 2: Implement the Core Workflow

{code_block}

## Step 3: Add Explicit Safety & Approval Checks

Never allow background tasks or generated drafts to auto-publish without human sign-off. Enforce stage transitions in a dedicated pipeline helper so both the UI and API endpoints share a single source of truth.

## Step 4: Verify with Automated Integration Tests

```bash
python3 -m pytest backend/tests -v
```

Confirm both happy-path execution and `403`/`400` boundary rejections pass without regressions.

## Grounding Sources

{citations_section}
"""
