"""Content Agent (masterclass-synth) full implementation for Phase 12 Content Studio.

Capabilities:
- READ_ONLY: RAG-powered topic research, pipeline inventory, draft review audit
- SUGGEST: Draft deep-dive articles, tutorials, YouTube scripts, LinkedIn/Twitter social packs, architecture case studies (all stamped [REVIEW REQUIRED])
- IMPLEMENT (approval required): Persist generated content into Content Studio DB, schedule on calendar, approve/publish via explicit approval gate (no auto-publishing)
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from backend.app.agents.base_agent import (
        AgentResult,
        AgentTask,
        Artifact,
        BaseAgent,
        CapabilityDescription,
        Evidence,
        ExecutionContext,
        TaskScope,
        ValidationResult,
    )
    import backend.app.database as db_module
    from backend.app.content.pipeline import ContentPipeline, REVIEW_MARKER
    from backend.app.content.research import TopicResearcher
    from backend.app.models.content_item import (
        ContentItem,
        ContentTypeEnum,
        ContentStageEnum,
        ContentChannelEnum,
    )
    from backend.app.tools.article_writer import ArticleWriter
    from backend.app.tools.youtube_script_writer import YouTubeScriptWriter
    from backend.app.tools.social_writer import SocialPostWriter
    from backend.app.tools.case_study_writer import CaseStudyWriter
except ImportError:
    from app.agents.base_agent import (
        AgentResult,
        AgentTask,
        Artifact,
        BaseAgent,
        CapabilityDescription,
        Evidence,
        ExecutionContext,
        TaskScope,
        ValidationResult,
    )
    import app.database as db_module
    from app.content.pipeline import ContentPipeline, REVIEW_MARKER
    from app.content.research import TopicResearcher
    from app.models.content_item import (
        ContentItem,
        ContentTypeEnum,
        ContentStageEnum,
        ContentChannelEnum,
    )
    from app.tools.article_writer import ArticleWriter
    from app.tools.youtube_script_writer import YouTubeScriptWriter
    from app.tools.social_writer import SocialPostWriter
    from app.tools.case_study_writer import CaseStudyWriter


class ContentAgent(BaseAgent):
    """Full implementation of the Phase 12 Content Studio Synthesizer Agent."""

    slug = "masterclass-synth"
    name = "Content Studio & Synthesizer Agent"
    purpose = (
        "RAG-grounded synthesis of technical deep-dive articles, step-by-step developer tutorials, "
        "YouTube breakdown scripts, LinkedIn/Twitter threads, and verified architecture case studies "
        "with strict [REVIEW REQUIRED] gating."
    )
    phase = 12
    version = "1.0.0"
    allowed_tools = [
        "topic_researcher",
        "article_writer",
        "youtube_script_writer",
        "social_post_writer",
        "case_study_writer",
        "content_pipeline",
    ]
    required_permissions = ["READ_ONLY", "SUGGEST", "IMPLEMENT"]
    limitations = [
        "No fabricated metrics or benchmark numbers allowed in case studies ([BENCHMARK NEEDED] flagged)",
        "Auto-publishing strictly prohibited — every transition to Approved or Published requires explicit approval",
        "All generated drafts carry mandatory [REVIEW REQUIRED] marker",
        "Does not generate video or raster image media assets",
    ]

    async def validate_input(self, task: AgentTask) -> ValidationResult:
        if not task.instruction or len(task.instruction.strip()) < 3:
            return ValidationResult(valid=False, error="Instruction must be at least 3 characters.")
        return ValidationResult(valid=True)

    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        instruction = task.instruction.strip()
        inst_lower = instruction.lower()
        params: Dict[str, Any] = getattr(task, "context", {}) or {}

        evidence: List[Evidence] = []
        artifacts: List[Artifact] = []

        topic = str(params.get("topic") or instruction).strip()

        # Run RAG + codebase topic research when DB session available
        brief = None
        try:
            async with db_module.AsyncSessionLocal() as session:
                brief = await TopicResearcher.research_topic(
                    topic=topic,
                    session=session,
                    user_id=task.requested_by,
                    top_k=int(params.get("top_k", 5)),
                )
        except Exception:
            brief = await TopicResearcher.research_topic(topic=topic, session=None, user_id=None)

        evidence.append(
            Evidence(
                source="topic_researcher",
                snippet=f"Research brief for '{topic}': {brief.rag_chunks_found} RAG chunks, {brief.repo_files_inspected} codebase files.",
                confidence=1.0,
            )
        )

        # -------------------------------------------------------------
        # 1. READ_ONLY: Topic Research / Pipeline Inspection
        # -------------------------------------------------------------
        if any(kw in inst_lower for kw in ["research topic", "rag research", "find sources"]) and not any(
            kw in inst_lower for kw in ["write", "draft", "article", "script", "case study", "post", "thread"]
        ):
            citations_md = (
                "\n".join(
                    f"- **{c.document}** (`{c.source}`, score `{c.score}`): {c.chunk}"
                    for c in brief.citations[:6]
                )
                if brief.citations
                else "No matching indexed chunks or modules found for this topic."
            )
            output = (
                f"### RAG Topic Research Brief: `{topic}`\n\n"
                f"- **RAG Chunks Retrieved**: {brief.rag_chunks_found}\n"
                f"- **Codebase Modules Inspected**: {brief.repo_files_inspected}\n"
                f"- **Note**: {brief.honest_note}\n\n"
                f"**Grounded Citations**:\n{citations_md}"
            )
            return AgentResult(
                success=True,
                output=output,
                artifacts=artifacts,
                evidence=evidence,
                limitations=self.limitations,
                simulated=False,
            )

        # -------------------------------------------------------------
        # 2. Content Synthesis (SUGGEST / IMPLEMENT)
        # -------------------------------------------------------------
        content_type = str(params.get("content_type", "")).lower().strip()
        generated_title = ""
        generated_markdown = ""
        generated_summary = ""
        channel = ContentChannelEnum.BLOG.value
        stage = ContentStageEnum.DRAFT.value

        # A. Architecture Case Study
        if content_type == "case_study" or "case study" in inst_lower or "case-study" in inst_lower:
            cs = CaseStudyWriter.write_case_study(
                topic=topic,
                brief=brief,
                observed_notes=params.get("observed_notes"),
            )
            generated_title = cs.title
            generated_markdown = cs.markdown
            generated_summary = f"Architecture case study on {topic}. Zero fabricated benchmarks."
            channel = ContentChannelEnum.BLOG.value
            evidence.append(
                Evidence(
                    source="case_study_writer",
                    snippet=f"Generated case study '{cs.title}' (benchmark flags: {len(cs.benchmark_flags)}, citations: {cs.citations_used})",
                    confidence=1.0,
                )
            )
            artifacts.append(
                Artifact(
                    name=f"case-study-{ContentPipeline.slugify(topic)}.md",
                    artifact_type="case_study",
                    content=generated_markdown,
                    metadata={"review_required": True, "benchmark_flags": cs.benchmark_flags},
                )
            )

        # B. YouTube Video Script
        elif content_type == "youtube_script" or any(kw in inst_lower for kw in ["youtube", "video script", "script"]):
            yt = YouTubeScriptWriter.write_script(
                topic=topic,
                brief=brief,
                target_minutes=int(params.get("target_minutes", 12)),
            )
            generated_title = yt.title
            generated_markdown = yt.markdown
            generated_summary = f"~{yt.estimated_duration_min}-min technical YouTube script with {len(yt.segments)} segments."
            channel = ContentChannelEnum.YOUTUBE.value
            evidence.append(
                Evidence(
                    source="youtube_script_writer",
                    snippet=f"Generated YouTube script '{yt.title}' ({len(yt.segments)} timestamped segments).",
                    confidence=1.0,
                )
            )
            artifacts.append(
                Artifact(
                    name=f"youtube-script-{ContentPipeline.slugify(topic)}.md",
                    artifact_type="youtube_script",
                    content=generated_markdown,
                    metadata={"review_required": True, "duration_min": yt.estimated_duration_min},
                )
            )

        # C. LinkedIn / Twitter Social Pack
        elif content_type == "social_pack" or any(kw in inst_lower for kw in ["linkedin", "twitter", "tweet", "social", "thread"]):
            social = SocialPostWriter.write_social_pack(topic=topic, brief=brief)
            generated_title = f"Social Distribution Pack: {topic}"
            generated_markdown = social.markdown
            generated_summary = f"LinkedIn engineering post + {len(social.twitter_thread)}-tweet thread (all <= 280 chars)."
            channel = ContentChannelEnum.CROSS_PLATFORM.value
            evidence.append(
                Evidence(
                    source="social_post_writer",
                    snippet=f"Generated social pack: 1 LinkedIn post + {len(social.twitter_thread)} tweets (all <=280 chars: {social.all_tweets_within_limit}).",
                    confidence=1.0,
                )
            )
            artifacts.append(
                Artifact(
                    name=f"social-pack-{ContentPipeline.slugify(topic)}.md",
                    artifact_type="social_pack",
                    content=generated_markdown,
                    metadata={"review_required": True, "all_tweets_within_limit": social.all_tweets_within_limit},
                )
            )

        # D. Outline-Only Mode or Article (Deep Dive / Tutorial)
        else:
            is_outline = "outline" in inst_lower or params.get("outline_only", False)
            mode = "tutorial" if (content_type == "tutorial" or "tutorial" in inst_lower or "how to" in inst_lower) else "deep_dive"
            art = ArticleWriter.write_article(
                topic=topic,
                mode=mode,
                brief=brief,
                outline_only=bool(is_outline),
            )
            generated_title = art.title
            generated_markdown = art.markdown
            generated_summary = art.summary
            channel = ContentChannelEnum.BLOG.value
            stage = ContentStageEnum.OUTLINE.value if is_outline else ContentStageEnum.DRAFT.value
            evidence.append(
                Evidence(
                    source="article_writer",
                    snippet=f"Generated {art.mode} article '{art.title}' ({art.word_count} words, {art.citations_used} citations).",
                    confidence=1.0,
                )
            )
            artifacts.append(
                Artifact(
                    name=f"{mode}-{ContentPipeline.slugify(topic)}.md",
                    artifact_type="article",
                    content=generated_markdown,
                    metadata={"review_required": True, "mode": mode, "word_count": art.word_count},
                )
            )

        # Guarantee [REVIEW REQUIRED] marker is ALWAYS present on every draft output
        generated_markdown = ContentPipeline.stamp_draft_review(generated_markdown)

        # Enforce no auto-publish rule under all scopes
        if params.get("auto_publish") is True:
            return AgentResult(
                success=False,
                output=(
                    f"{REVIEW_MARKER} **AUTO-PUBLISH PROHIBITED**: ContentAgent never auto-publishes drafts. "
                    f"Use explicit human review & approval transitions in Content Studio."
                ),
                artifacts=artifacts,
                evidence=evidence,
                limitations=self.limitations,
                simulated=False,
            )

        # Optional IMPLEMENT step: persist draft to ContentItem DB if scope=implement & approved=True
        saved_id = None
        if task.scope == TaskScope.implement or params.get("save_to_pipeline"):
            if not params.get("approved", False) and task.scope == TaskScope.implement:
                return AgentResult(
                    success=False,
                    output=(
                        f"{REVIEW_MARKER} **APPROVAL REQUIRED (IMPLEMENT Scope)**:\n"
                        f"Persisting draft `{generated_title}` into the Content Studio database requires explicit `approved=True`."
                    ),
                    artifacts=artifacts,
                    evidence=evidence,
                    limitations=self.limitations,
                    simulated=False,
                )
            try:
                async with db_module.AsyncSessionLocal() as session:
                    metrics = ContentPipeline.compute_metrics(generated_markdown)
                    new_item = ContentItem(
                        id=uuid.uuid4(),
                        title=generated_title[:255],
                        slug=ContentPipeline.slugify(generated_title),
                        content_type=content_type or ContentTypeEnum.ARTICLE.value,
                        stage=stage,
                        channel=channel,
                        body_markdown=generated_markdown,
                        summary=generated_summary,
                        rag_sources=[c.model_dump() for c in brief.citations[:8]],
                        metadata_json={
                            "word_count": metrics.word_count,
                            "reading_time_min": metrics.reading_time_min,
                            "code_blocks_count": metrics.code_blocks_count,
                            "review_required": True,
                            "benchmark_flags": metrics.benchmark_flags,
                            "tone": "principal_systems_engineer",
                        },
                        created_by=task.requested_by,
                    )
                    session.add(new_item)
                    await session.commit()
                    saved_id = str(new_item.id)
            except Exception:
                saved_id = None

        save_note = f"\n\n- **Saved Pipeline Draft ID**: `{saved_id}` (Stage: `{stage.upper()}`)" if saved_id else ""
        output = (
            f"### {generated_title}\n\n"
            f"- **Grounding**: {brief.honest_note}\n"
            f"- **Pipeline Stage**: `{stage.upper()}` (`{REVIEW_MARKER}`)\n"
            f"{save_note}\n\n"
            f"---\n\n{generated_markdown}"
        )

        return AgentResult(
            success=True,
            output=output,
            artifacts=artifacts,
            evidence=evidence,
            limitations=self.limitations,
            simulated=False,
        )

    async def describe_capabilities(self) -> CapabilityDescription:
        return CapabilityDescription(
            slug=self.slug,
            name=self.name,
            purpose=self.purpose,
            phase=self.phase,
            version=self.version,
            allowed_tools=self.allowed_tools,
            required_permissions=self.required_permissions,
            limitations=self.limitations,
        )
