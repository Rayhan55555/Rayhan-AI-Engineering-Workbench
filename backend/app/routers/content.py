"""Content Studio API Endpoints (Phase 12).

Routes under /api/v1/content:
- POST   /research                  RAG-powered topic research brief
- POST   /generate                  Synthesize draft (article/tutorial/case_study/youtube_script/social_pack)
- POST   /items                     Create pipeline item
- GET    /items                     List & filter pipeline items
- GET    /items/{item_id}           Get content item by ID
- PATCH  /items/{item_id}           Update markdown body, schedule, or metadata
- POST   /items/{item_id}/transition Transition across Idea -> Outline -> Draft -> Approved -> Published
- DELETE /items/{item_id}           Remove content item
- GET    /calendar                  Editorial calendar & stage metrics
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.content.pipeline import (
        ContentPipeline,
        TransitionValidationError,
        STAGE_ORDER,
    )
    from backend.app.content.research import TopicResearcher, ResearchBrief
    from backend.app.database import get_db
    from backend.app.dependencies import get_current_user
    from backend.app.models.content_item import (
        ContentItem,
        ContentTypeEnum,
        ContentStageEnum,
        ContentChannelEnum,
    )
    from backend.app.models.user import User
    from backend.app.tools.article_writer import ArticleWriter
    from backend.app.tools.youtube_script_writer import YouTubeScriptWriter
    from backend.app.tools.social_writer import SocialPostWriter
    from backend.app.tools.case_study_writer import CaseStudyWriter
except ImportError:
    from app.content.pipeline import (
        ContentPipeline,
        TransitionValidationError,
        STAGE_ORDER,
    )
    from app.content.research import TopicResearcher, ResearchBrief
    from app.database import get_db
    from app.dependencies import get_current_user
    from app.models.content_item import (
        ContentItem,
        ContentTypeEnum,
        ContentStageEnum,
        ContentChannelEnum,
    )
    from app.models.user import User
    from app.tools.article_writer import ArticleWriter
    from app.tools.youtube_script_writer import YouTubeScriptWriter
    from app.tools.social_writer import SocialPostWriter
    from app.tools.case_study_writer import CaseStudyWriter


router = APIRouter(prefix="/content", tags=["Content Studio"])


# -------------------------------------------------------------
# Schemas
# -------------------------------------------------------------

class TopicResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(5, ge=1, le=15)


class ContentGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    content_type: Literal["article", "tutorial", "case_study", "youtube_script", "social_pack"] = "article"
    outline_only: bool = False
    target_minutes: int = Field(12, ge=3, le=60)
    use_rag: bool = True
    save_to_pipeline: bool = True
    scheduled_at: Optional[datetime] = None


class ContentItemCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    content_type: Literal["article", "tutorial", "case_study", "youtube_script", "social_pack"] = "article"
    stage: Literal["idea", "outline", "draft"] = "idea"
    channel: Literal["blog", "youtube", "linkedin", "twitter", "cross_platform"] = "blog"
    body_markdown: str = ""
    summary: str = ""
    scheduled_at: Optional[datetime] = None


class ContentItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    body_markdown: Optional[str] = None
    summary: Optional[str] = None
    channel: Optional[Literal["blog", "youtube", "linkedin", "twitter", "cross_platform"]] = None
    scheduled_at: Optional[datetime] = None


class TransitionRequest(BaseModel):
    target_stage: Literal["idea", "outline", "draft", "approved", "published"]
    approved: bool = False


class ContentItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    content_type: str
    stage: str
    channel: str
    body_markdown: str
    summary: str
    rag_sources: Optional[List[Dict[str, Any]]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateContentResponse(BaseModel):
    title: str
    content_type: str
    stage: str
    channel: str
    summary: str
    body_markdown: str
    review_required: bool = True
    rag_citations: List[Dict[str, Any]] = Field(default_factory=list)
    benchmark_flags: List[str] = Field(default_factory=list)
    twitter_thread: List[str] = Field(default_factory=list)
    linkedin_post: Optional[str] = None
    saved_item: Optional[ContentItemResponse] = None


class CalendarResponse(BaseModel):
    stage_counts: Dict[str, int]
    total_items: int
    scheduled_items: List[ContentItemResponse]
    unscheduled_items: List[ContentItemResponse]


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@router.post("/research", response_model=ResearchBrief)
async def research_topic(
    req: TopicResearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run RAG-powered topic research against indexed knowledge base & repository modules."""
    return await TopicResearcher.research_topic(
        topic=req.topic,
        session=db,
        user_id=current_user.id,
        top_k=req.top_k,
    )


@router.post("/generate", response_model=GenerateContentResponse)
async def generate_content(
    req: ContentGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate technical article, tutorial, case study, YouTube script, or social thread pack.
    Always stamps [REVIEW REQUIRED] on drafts and NEVER auto-publishes.
    """
    brief = (
        await TopicResearcher.research_topic(topic=req.topic, session=db, user_id=current_user.id)
        if req.use_rag
        else None
    )

    citations_dicts = [c.model_dump() for c in brief.citations] if brief else []
    benchmark_flags: List[str] = []
    twitter_thread: List[str] = []
    linkedin_post: Optional[str] = None

    stage = ContentStageEnum.OUTLINE.value if req.outline_only else ContentStageEnum.DRAFT.value
    channel = ContentChannelEnum.BLOG.value

    if req.content_type in ("article", "tutorial"):
        mode = "tutorial" if req.content_type == "tutorial" else "deep_dive"
        res = ArticleWriter.write_article(
            topic=req.topic,
            mode=mode,
            brief=brief,
            outline_only=req.outline_only,
        )
        title = res.title
        summary = res.summary
        body_markdown = res.markdown
    elif req.content_type == "case_study":
        res = CaseStudyWriter.write_case_study(topic=req.topic, brief=brief)
        title = res.title
        summary = f"Architecture case study for {req.topic}. Zero fabricated performance claims."
        body_markdown = res.markdown
        benchmark_flags = res.benchmark_flags
    elif req.content_type == "youtube_script":
        res = YouTubeScriptWriter.write_script(
            topic=req.topic, brief=brief, target_minutes=req.target_minutes
        )
        title = res.title
        summary = f"~{res.estimated_duration_min}-minute YouTube breakdown script with {len(res.segments)} cues."
        body_markdown = res.markdown
        channel = ContentChannelEnum.YOUTUBE.value
    else:  # social_pack
        res = SocialPostWriter.write_social_pack(topic=req.topic, brief=brief)
        title = f"Social Distribution Pack: {req.topic}"
        summary = f"LinkedIn engineering post + {len(res.twitter_thread)}-tweet thread."
        body_markdown = res.markdown
        channel = ContentChannelEnum.CROSS_PLATFORM.value
        twitter_thread = res.twitter_thread
        linkedin_post = res.linkedin_post

    body_markdown = ContentPipeline.stamp_draft_review(body_markdown)
    metrics = ContentPipeline.compute_metrics(body_markdown)
    if not benchmark_flags:
        benchmark_flags = metrics.benchmark_flags

    saved_item = None
    if req.save_to_pipeline:
        item = ContentItem(
            id=uuid.uuid4(),
            title=title[:255],
            slug=ContentPipeline.slugify(title),
            content_type=req.content_type,
            stage=stage,
            channel=channel,
            body_markdown=body_markdown,
            summary=summary,
            rag_sources=citations_dicts,
            metadata_json={
                "word_count": metrics.word_count,
                "reading_time_min": metrics.reading_time_min,
                "code_blocks_count": metrics.code_blocks_count,
                "review_required": True,
                "benchmark_flags": benchmark_flags,
                "tone": "principal_systems_engineer",
                "twitter_thread": twitter_thread,
                "linkedin_post": linkedin_post,
            },
            scheduled_at=req.scheduled_at,
            created_by=current_user.id,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        saved_item = ContentItemResponse.model_validate(item)

    return GenerateContentResponse(
        title=title,
        content_type=req.content_type,
        stage=stage,
        channel=channel,
        summary=summary,
        body_markdown=body_markdown,
        review_required=True,
        rag_citations=citations_dicts,
        benchmark_flags=benchmark_flags,
        twitter_thread=twitter_thread,
        linkedin_post=linkedin_post,
        saved_item=saved_item,
    )


@router.post("/items", response_model=ContentItemResponse, status_code=status.HTTP_201_CREATED)
async def create_content_item(
    req: ContentItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a manual content pipeline entry (Idea, Outline, or Draft)."""
    body = req.body_markdown
    if req.stage == ContentStageEnum.DRAFT.value:
        body = ContentPipeline.stamp_draft_review(body)
    if req.content_type == ContentTypeEnum.CASE_STUDY.value and body:
        body, _ = ContentPipeline.inspect_no_fake_metrics(body)

    metrics = ContentPipeline.compute_metrics(body)

    item = ContentItem(
        id=uuid.uuid4(),
        title=req.title,
        slug=ContentPipeline.slugify(req.title),
        content_type=req.content_type,
        stage=req.stage,
        channel=req.channel,
        body_markdown=body,
        summary=req.summary,
        rag_sources=[],
        metadata_json={
            "word_count": metrics.word_count,
            "reading_time_min": metrics.reading_time_min,
            "code_blocks_count": metrics.code_blocks_count,
            "review_required": True,
            "benchmark_flags": metrics.benchmark_flags,
            "tone": "principal_systems_engineer",
        },
        scheduled_at=req.scheduled_at,
        created_by=current_user.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


def _ensure_content_access(item: ContentItem, current_user: User) -> None:
    """Block cross-user access unless superuser."""
    if item.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "You do not have permission to access this content item."},
        )


@router.get("/items", response_model=List[ContentItemResponse])
async def list_content_items(
    stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List content items across pipeline stages with user isolation and filtering."""
    stmt = select(ContentItem).order_by(desc(ContentItem.updated_at))
    if not current_user.is_superuser:
        stmt = stmt.where(ContentItem.created_by == current_user.id)
    if stage:
        stmt = stmt.where(ContentItem.stage == stage)
    if content_type:
        stmt = stmt.where(ContentItem.content_type == content_type)
    if channel:
        stmt = stmt.where(ContentItem.channel == channel)
    if search:
        pat = f"%{search.strip()}%"
        stmt = stmt.where(or_(ContentItem.title.ilike(pat), ContentItem.summary.ilike(pat)))

    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/items/{item_id}", response_model=ContentItemResponse)
async def get_content_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(ContentItem).where(ContentItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Content item {item_id} not found."},
        )
    _ensure_content_access(item, current_user)
    return item


@router.patch("/items/{item_id}", response_model=ContentItemResponse)
async def update_content_item(
    item_id: uuid.UUID,
    req: ContentItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(ContentItem).where(ContentItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Content item {item_id} not found."},
        )
    _ensure_content_access(item, current_user)

    if req.title is not None:
        item.title = req.title
    if req.summary is not None:
        item.summary = req.summary
    if req.channel is not None:
        item.channel = req.channel
    if req.scheduled_at is not None:
        item.scheduled_at = req.scheduled_at
    if req.body_markdown is not None:
        body = req.body_markdown
        if item.content_type == ContentTypeEnum.CASE_STUDY.value:
            body, _ = ContentPipeline.inspect_no_fake_metrics(body)
        if item.stage == ContentStageEnum.DRAFT.value:
            body = ContentPipeline.stamp_draft_review(body)
        item.body_markdown = body
        metrics = ContentPipeline.compute_metrics(body)
        meta = dict(item.metadata_json or {})
        meta.update(
            {
                "word_count": metrics.word_count,
                "reading_time_min": metrics.reading_time_min,
                "code_blocks_count": metrics.code_blocks_count,
                "benchmark_flags": metrics.benchmark_flags,
            }
        )
        item.metadata_json = meta

    await db.commit()
    await db.refresh(item)
    return item


@router.post("/items/{item_id}/transition", response_model=ContentItemResponse)
async def transition_content_stage(
    item_id: uuid.UUID,
    req: TransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Advance content item along Idea -> Outline -> Draft -> Approved -> Published.
    Rejects unapproved approvals/publishes and disallows skipping stages.
    """
    res = await db.execute(select(ContentItem).where(ContentItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Content item {item_id} not found."},
        )
    _ensure_content_access(item, current_user)

    try:
        ContentPipeline.transition_stage(
            item=item,
            target_stage=req.target_stage,
            approved=req.approved,
            reviewer_id=current_user.id,
        )
    except TransitionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_transition", "message": str(exc)},
        )

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(ContentItem).where(ContentItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Content item {item_id} not found."},
        )
    _ensure_content_access(item, current_user)
    await db.delete(item)
    await db.commit()
    return None


@router.get("/calendar", response_model=CalendarResponse)
async def get_content_calendar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return scheduled release timeline and pipeline stage counts (user-isolated)."""
    stmt = select(ContentItem).order_by(desc(ContentItem.updated_at))
    if not current_user.is_superuser:
        stmt = stmt.where(ContentItem.created_by == current_user.id)
    res = await db.execute(stmt)
    items = list(res.scalars().all())

    stage_counts: Dict[str, int] = {stage: 0 for stage in STAGE_ORDER}
    scheduled: List[ContentItemResponse] = []
    unscheduled: List[ContentItemResponse] = []

    for it in items:
        stage_counts[it.stage] = stage_counts.get(it.stage, 0) + 1
        dto = ContentItemResponse.model_validate(it)
        if it.scheduled_at is not None:
            scheduled.append(dto)
        else:
            unscheduled.append(dto)

    def _sort_key(item: ContentItemResponse) -> datetime:
        dt = item.scheduled_at or datetime.min.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    scheduled.sort(key=_sort_key)

    return CalendarResponse(
        stage_counts=stage_counts,
        total_items=len(items),
        scheduled_items=scheduled,
        unscheduled_items=unscheduled,
    )
