"""Unit & integration tests for ContentAgent (masterclass-synth) & Content Writers (Phase 12)."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.base_agent import AgentTask, ExecutionContext, TaskScope
from backend.app.agents.implementations.content_agent import ContentAgent
from backend.app.content.pipeline import REVIEW_MARKER
from backend.app.models.user import User
from backend.app.models.knowledge_document import KnowledgeDocument, DocType, AccessLevel
from backend.app.models.document_chunk import DocumentChunk
from backend.app.tools.article_writer import ArticleWriter
from backend.app.tools.youtube_script_writer import YouTubeScriptWriter
from backend.app.tools.social_writer import SocialPostWriter
from backend.app.tools.case_study_writer import CaseStudyWriter


def test_article_writer_deep_dive_and_tutorial():
    """Verify deep-dive and tutorial articles both stamp [REVIEW REQUIRED]."""
    deep = ArticleWriter.write_article("pgvector Retrieval", mode="deep_dive")
    assert deep.mode == "deep_dive"
    assert deep.review_required is True
    assert REVIEW_MARKER in deep.markdown
    assert deep.word_count > 50

    tut = ArticleWriter.write_article("pgvector Retrieval", mode="tutorial")
    assert tut.mode == "tutorial"
    assert "Walkthrough" in tut.title
    assert REVIEW_MARKER in tut.markdown


def test_youtube_script_writer_has_timestamps_and_cues():
    """Verify YouTube breakdown script generates visual cues and timestamps."""
    yt = YouTubeScriptWriter.write_script("Phase 11 DevOps Rollback", target_minutes=14)
    assert yt.estimated_duration_min == 14
    assert len(yt.segments) >= 4
    assert "[SCREEN:" in yt.markdown or "[DIAGRAM:" in yt.markdown
    assert REVIEW_MARKER in yt.markdown


def test_social_post_writer_enforces_tweet_character_limit():
    """Verify every generated tweet strictly conforms to <= 280 chars."""
    pack = SocialPostWriter.write_social_pack(
        "Multi-Tenant Asynchronous FastAPI Agent Orchestration With Strict Permission Boundaries"
    )
    assert len(pack.twitter_thread) >= 4
    assert pack.all_tweets_within_limit is True
    for tweet in pack.twitter_thread:
        assert len(tweet) <= 280
    assert len(pack.linkedin_post) > 50
    assert REVIEW_MARKER in pack.markdown


def test_case_study_writer_never_fabricates_metrics():
    """Verify CaseStudyWriter uses honest [BENCHMARK NEEDED] markers and no invented stats."""
    cs = CaseStudyWriter.write_case_study("Rayhan AI Workbench RAG Pipeline")
    assert "[BENCHMARK NEEDED]" in cs.markdown
    assert REVIEW_MARKER in cs.markdown


@pytest.mark.asyncio
async def test_content_agent_executes_with_rag_grounding(db_session: AsyncSession):
    """Verify ContentAgent pulls indexed RAG documents and returns simulated=False."""
    user = User(
        id=uuid.uuid4(),
        email="content_rag@example.com",
        username="content_author",
        hashed_password="pw",
    )
    db_session.add(user)
    await db_session.flush()

    doc = KnowledgeDocument(
        id=uuid.uuid4(),
        title="Agent Sandbox Architecture",
        source="docs/sandbox.md",
        doc_type=DocType.markdown,
        content_hash="hash_sandbox_doc",
        total_chunks=1,
        owner_id=user.id,
        access_level=AccessLevel.public,
    )
    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="Agent Sandbox isolates tool file access to project paths and blocks /etc or .env reads.",
        embedding=[0.8] + [0.0] * 767,
        token_count=16,
        metadata_json={"page": 1, "strategy": "SEMANTIC"},
    )
    db_session.add_all([doc, chunk])
    await db_session.commit()

    agent = ContentAgent()
    assert agent.slug == "masterclass-synth"

    task = AgentTask(
        agent_slug="masterclass-synth",
        requested_by=user.id,
        instruction="Write a deep dive article about Agent Sandbox Architecture",
        scope=TaskScope.suggest,
        context={"topic": "Agent Sandbox Architecture", "content_type": "article"},
    )
    exec_ctx = ExecutionContext(user_id=user.id, task_id=task.task_id, is_interactive=False)

    result = await agent.execute(task, exec_ctx)
    assert result.success is True
    assert result.simulated is False
    assert REVIEW_MARKER in result.output
    assert len(result.artifacts) == 1
    assert any(ev.source == "topic_researcher" for ev in result.evidence)


@pytest.mark.asyncio
async def test_content_agent_blocks_auto_publish_and_unapproved_implement():
    """Verify ContentAgent rejects auto_publish=True and unapproved IMPLEMENT mutations."""
    agent = ContentAgent()
    uid = uuid.uuid4()
    exec_ctx = ExecutionContext(user_id=uid, task_id=uuid.uuid4(), is_interactive=False)

    # 1. Auto-publish attempt rejected
    task_auto = AgentTask(
        agent_slug="masterclass-synth",
        requested_by=uid,
        instruction="Write article on DevOps",
        scope=TaskScope.suggest,
        context={"topic": "DevOps", "auto_publish": True},
    )
    res_auto = await agent.execute(task_auto, exec_ctx)
    assert res_auto.success is False
    assert "AUTO-PUBLISH PROHIBITED" in res_auto.output

    # 2. IMPLEMENT without approved=True rejected
    task_impl = AgentTask(
        agent_slug="masterclass-synth",
        requested_by=uid,
        instruction="Save case study on DevOps",
        scope=TaskScope.implement,
        context={"topic": "DevOps", "content_type": "case_study", "approved": False},
    )
    res_impl = await agent.execute(task_impl, exec_ctx)
    assert res_impl.success is False
    assert "APPROVAL REQUIRED" in res_impl.output
