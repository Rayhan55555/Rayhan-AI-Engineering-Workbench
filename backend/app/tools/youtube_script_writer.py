"""YouTube Script Writer Tool for technical breakdown videos and architecture walkthroughs.

Generates timestamped audiovisual scripts with [SCREEN], [TERMINAL], and [DIAGRAM] cues.
No video/image generation is performed; strictly editorial scripting marked [REVIEW REQUIRED].
"""

from typing import List, Optional
from pydantic import BaseModel, Field

try:
    from backend.app.content.pipeline import ContentPipeline
    from backend.app.content.research import ResearchBrief
except ImportError:
    from app.content.pipeline import ContentPipeline
    from app.content.research import ResearchBrief


class ScriptSegment(BaseModel):
    timestamp: str
    section: str
    visual_cue: str
    narration: str


class GeneratedYouTubeScript(BaseModel):
    title: str
    estimated_duration_min: int
    segments: List[ScriptSegment]
    markdown: str
    citations_used: int
    review_required: bool = True


class YouTubeScriptWriter:
    """Writes principal-engineer style technical YouTube breakdown scripts."""

    @classmethod
    def write_script(
        cls,
        topic: str,
        brief: Optional[ResearchBrief] = None,
        target_minutes: int = 12,
    ) -> GeneratedYouTubeScript:
        clean_topic = topic.strip()
        facts = brief.key_facts if brief else []
        excerpts = brief.code_excerpts if brief else []
        citations = brief.citations if brief else []

        title = f"How Production Teams Engineer {clean_topic} (Architecture + Code Walkthrough)"

        code_ref = excerpts[0]["file"] if excerpts else "backend/app/main.py"
        fact_line = facts[0] if facts else f"Enforcing deterministic safety boundaries around {clean_topic}."

        segments = [
            ScriptSegment(
                timestamp="00:00 - 01:15",
                section="Cold Open & Engineering Hook",
                visual_cue="[SCREEN: Terminal showing failing edge case -> transition to clean architecture diagram]",
                narration=(
                    f"Most demos of {clean_topic} stop the moment the happy path works. "
                    f"In production, that's right where the real engineering begins. Today we're breaking down "
                    f"the exact architecture, permission gates, and testing strategy we use so nothing ships unverified."
                ),
            ),
            ScriptSegment(
                timestamp="01:15 - 04:00",
                section="System Topology & Core Invariants",
                visual_cue=f"[DIAGRAM: Data flow across API boundary -> Validation -> Storage | Source: {code_ref}]",
                narration=(
                    f"Let's zoom out to the system diagram. The core invariant here is simple: {fact_line} "
                    f"Notice how read-only analysis stays completely decoupled from state-mutating operations."
                ),
            ),
            ScriptSegment(
                timestamp="04:00 - 08:30",
                section="Live Code Walkthrough",
                visual_cue=f"[SCREEN: Editor split view open on `{code_ref}` highlighting type contracts]",
                narration=(
                    f"Walking through `{code_ref}`, look closely at how validation happens up front. "
                    f"Instead of trusting unstructured responses, every transition goes through an explicit contract check."
                ),
            ),
            ScriptSegment(
                timestamp="08:30 - 10:45",
                section="Failure Modes & Trade-Offs",
                visual_cue="[TERMINAL: Running pytest regression suite across boundary error cases]",
                narration=(
                    f"Why not skip the approval gate to save a click? Because silent regressions cost 10x more to untangle in production. "
                    f"By keeping drafts tagged [REVIEW REQUIRED] and gating releases behind explicit tests, we trade a tiny bit of friction for reliability."
                ),
            ),
            ScriptSegment(
                timestamp=f"10:45 - {target_minutes:02d}:00",
                section="Recap & Engineering Takeaways",
                visual_cue="[SCREEN: Summary slide with 3 core architecture rules]",
                narration=(
                    f"That's the complete blueprint for {clean_topic}. Build strict boundaries, test the failure paths first, "
                    f"and keep human approval in control of publishing. Links to the repository structure are in the description."
                ),
            ),
        ]

        sections_md = "\n\n".join(
            f"### [{seg.timestamp}] {seg.section}\n"
            f"- **Visual Cue**: `{seg.visual_cue}`\n\n"
            f"{seg.narration}"
            for seg in segments
        )

        citations_md = (
            "\n".join(
                f"- `{getattr(c, 'document', 'Source')}` ({getattr(c, 'source', 'repo')})"
                for c in citations[:4]
            )
            if citations
            else "- Grounded in workbench codebase structure."
        )

        raw_markdown = f"""# {title}

- **Format**: Technical Architecture Breakdown (YouTube)
- **Estimated Runtime**: ~{target_minutes} minutes
- **Target Audience**: Senior & Staff Software Engineers

{sections_md}

## Show Notes & Grounded References
{citations_md}
"""
        stamped = ContentPipeline.stamp_draft_review(raw_markdown)

        return GeneratedYouTubeScript(
            title=title,
            estimated_duration_min=target_minutes,
            segments=segments,
            markdown=stamped,
            citations_used=len(citations),
            review_required=True,
        )
