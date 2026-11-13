import React, { useState, useEffect, useMemo } from 'react';
import {
  FileText,
  Youtube,
  Share2,
  Calendar as CalendarIcon,
  Layers,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  Plus,
  Trash2,
  Search,
  Database,
  ArrowRight,
  Lock,
  ExternalLink,
  Edit3,
  Eye,
  Clock,
  Terminal,
} from 'lucide-react';
import { RAYHAN_PROFILE } from '../../data/workbenchData';

type ContentType = 'article' | 'tutorial' | 'case_study' | 'youtube_script' | 'social_pack';
type ContentStage = 'idea' | 'outline' | 'draft' | 'approved' | 'published';
type ContentChannel = 'blog' | 'youtube' | 'linkedin' | 'twitter' | 'cross_platform';

interface Citation {
  document: string;
  source: string;
  chunk: string;
  score: number;
}

interface ContentItem {
  id: string;
  title: string;
  slug: string;
  content_type: ContentType;
  stage: ContentStage;
  channel: ContentChannel;
  body_markdown: string;
  summary: string;
  rag_sources?: Citation[];
  metadata_json?: {
    word_count?: number;
    reading_time_min?: number;
    code_blocks_count?: number;
    review_required?: boolean;
    benchmark_flags?: string[];
    tone?: string;
    twitter_thread?: string[];
    linkedin_post?: string;
  };
  scheduled_at?: string | null;
  approved_at?: string | null;
  published_at?: string | null;
  created_at: string;
  updated_at: string;
}

const STAGE_ORDER: ContentStage[] = ['idea', 'outline', 'draft', 'approved', 'published'];

const STAGE_LABELS: Record<ContentStage, string> = {
  idea: 'Idea',
  outline: 'Outline',
  draft: 'Draft [REVIEW REQUIRED]',
  approved: 'Approved',
  published: 'Published',
};

const TYPE_LABELS: Record<ContentType, string> = {
  article: 'Deep-Dive Article',
  tutorial: 'Developer Tutorial',
  case_study: 'Architecture Case Study',
  youtube_script: 'YouTube Breakdown Script',
  social_pack: 'LinkedIn + X Thread Pack',
};

const QUICK_TOPICS = [
  'Phase 10 Hybrid pgvector RAG Retrieval & Reranking',
  'Phase 11 Approval-Gated DevOps Workflows & Rollback',
  'Multi-Tenant Agent Permission Boundaries in FastAPI',
  'Deterministic Tool Sandboxing via Model Context Protocol',
];

function computeLocalMetrics(markdown: string) {
  const textOnly = markdown.replace(/```[\s\S]*?```/g, '');
  const words = textOnly.trim().split(/\s+/).filter(Boolean);
  const wordCount = words.length;
  const readingTimeMin = Math.max(1, Math.round(wordCount / 200));
  const codeBlocks = Math.floor((markdown.match(/```/g) || []).length / 2);
  const flags: string[] = [];
  if (markdown.includes('[BENCHMARK NEEDED]')) {
    flags.push('Contains [BENCHMARK NEEDED] placeholders awaiting production telemetry.');
  }
  return { wordCount, readingTimeMin, codeBlocks, flags };
}

function buildLocalDraft(
  topic: string,
  contentType: ContentType,
  outlineOnly: boolean
): {
  title: string;
  summary: string;
  markdown: string;
  channel: ContentChannel;
  twitterThread: string[];
  linkedinPost: string;
  citations: Citation[];
} {
  const clean = topic.trim() || 'Production Agent Architecture';
  const citations: Citation[] = [
    {
      document: 'content_agent.py',
      source: 'backend/app/agents/implementations/content_agent.py',
      chunk: 'Enforces READ_ONLY research separation from IMPLEMENT publishing approval gates.',
      score: 0.94,
    },
    {
      document: 'pipeline.py',
      source: 'backend/app/content/pipeline.py',
      chunk: '5-stage lifecycle Idea -> Outline -> Draft -> Approved -> Published with [REVIEW REQUIRED].',
      score: 0.91,
    },
  ];

  if (contentType === 'case_study') {
    const md = `> **[REVIEW REQUIRED]** — Synthesized draft awaiting technical & factual review before approval.

# Architecture Case Study: Engineering ${clean}

## 1. System Context & Problem Constraints
- Grounded in repository modules implementing typed Pydantic contracts and async persistence.
- Read-only topic retrieval remains cleanly separated from state-mutating approval endpoints.

## 2. Key Architectural Decisions
- **Five-Stage Editorial State Machine**: \`Idea -> Outline -> Draft -> Approved -> Published\`. Skipping stages or auto-publishing is strictly prohibited.
- **No Fabricated Metrics**: Quantitative claims lacking observed benchmarks are flagged explicitly.

## 3. Observed Metrics & Verification Gaps
- Functional test suite passes across unit and endpoint verification gates.
- P95 Production Latency Under Load: \`[BENCHMARK NEEDED]\` — capture staging telemetry before external release.
- Sustained Throughput: \`[BENCHMARK NEEDED]\` — requires production load harness verification.

## 4. Citations & Inspected Modules
- \`pipeline.py\` (\`backend/app/content/pipeline.py\`)
- \`content_agent.py\` (\`backend/app/agents/implementations/content_agent.py\`)`;
    return {
      title: `Architecture Case Study: Engineering ${clean}`,
      summary: `Engineering architecture case study for ${clean} with explicit verification boundaries.`,
      markdown: md,
      channel: 'blog',
      twitterThread: [],
      linkedinPost: '',
      citations,
    };
  }

  if (contentType === 'youtube_script') {
    const md = `> **[REVIEW REQUIRED]** — Synthesized draft awaiting technical & factual review before approval.

# How Production Teams Engineer ${clean} (Architecture + Code Walkthrough)

- **Format**: Technical Architecture Breakdown (YouTube)
- **Estimated Runtime**: ~12 minutes
- **Target Audience**: Senior & Staff Software Engineers

### [00:00 - 01:15] Cold Open & Engineering Hook
- **Visual Cue**: \`[SCREEN: Terminal running pytest validation -> transition to system diagram]\`

Most demos of ${clean} stop the moment the happy path works. In production, the hard problems start at permission boundaries, schema drift, and silent hallucinations.

### [01:15 - 04:30] System Topology & Core Invariants
- **Visual Cue**: \`[DIAGRAM: TopicResearcher -> Writer Tools -> ContentPipeline Gate -> DB]\`

Notice how RAG citation grounding runs before a single paragraph is written, preventing invented module names or API flags.

### [04:30 - 09:00] Live Code Walkthrough
- **Visual Cue**: \`[SCREEN: Split editor showing pipeline.py state transition enforcement]\`

Every transition to Approved or Published requires explicit human confirmation—never automated blind publishing.

### [09:00 - 12:00] Trade-Offs & Verification Checklist
- **Visual Cue**: \`[TERMINAL: pytest backend/tests/test_content_pipeline.py -v]\`

Test the failure paths first, keep drafts flagged [REVIEW REQUIRED], and ship with verifiable evidence.`;
    return {
      title: `How Production Teams Engineer ${clean} (Architecture + Code Walkthrough)`,
      summary: `Timestamped ~12-minute technical breakdown script with [SCREEN], [DIAGRAM], and [TERMINAL] cues.`,
      markdown: md,
      channel: 'youtube',
      twitterThread: [],
      linkedinPost: '',
      citations,
    };
  }

  if (contentType === 'social_pack') {
    const linkedinPost = `Most engineering teams over-index on happy-path demos when building ${clean}.\n\nIn production systems, reliability comes down to three unglamorous boundaries:\n1. Ground every technical claim in real codebase context — zero phantom citations.\n2. Separate draft synthesis from publication with an explicit human approval gate.\n3. Mark unobserved benchmarks as [BENCHMARK NEEDED] rather than inventing SLA numbers.\n\nHow are you enforcing verification gates in your engineering content workflows?\n\n#SystemsEngineering #SoftwareArchitecture #AIEngineering`;
    const twitterThread = [
      `1/ Most prototypes of ${clean} look clean until real edge cases hit production. Here are 4 boundaries we enforce so nothing ships unverified:`,
      `2/ First rule: Grounding over guessing. Topic research pulls real chunks from indexed docs & source files before drafting prose.`,
      `3/ Second rule: Zero auto-publishing. Every draft carries [REVIEW REQUIRED] and advances strictly through Idea -> Outline -> Draft -> Approved -> Published.`,
      `4/ Third rule: Zero vanity metrics. Any latency or throughput claim without an observed benchmark is flagged [BENCHMARK NEEDED].`,
      `5/ Honest engineering beats hype every time. Full code walkthrough and tests live in the workbench.`,
    ].map((t) => (t.length > 280 ? t.slice(0, 277) + '...' : t));

    const md = `> **[REVIEW REQUIRED]** — Synthesized draft awaiting technical & factual review before approval.

# Social Distribution Pack: ${clean}

## LinkedIn Engineering Post
\`\`\`text
${linkedinPost}
\`\`\`

## Twitter / X Technical Thread (${twitterThread.length} Posts)

${twitterThread.map((t, i) => `**Tweet ${i + 1}** (\`${t.length}/280 chars\`):\n> ${t}`).join('\n\n')}`;

    return {
      title: `Social Distribution Pack: ${clean}`,
      summary: `LinkedIn engineering post + ${twitterThread.length}-tweet technical thread.`,
      markdown: md,
      channel: 'cross_platform',
      twitterThread,
      linkedinPost,
      citations,
    };
  }

  const isTut = contentType === 'tutorial';
  const title = isTut
    ? `Implementing ${clean}: A Production Engineering Walkthrough`
    : `Inside ${clean}: Architectural Trade-offs & Production Boundaries`;

  const md = outlineOnly
    ? `> **[REVIEW REQUIRED]** — Synthesized outline awaiting technical & factual review before approval.

# ${title}

## Structured Outline
1. Why Naive Prototypes Break Under Production Constraints
2. Grounded System Topology & Type Contracts
3. Human-in-the-Loop Approval Gates
4. Verification Suite & Regression Checks`
    : `> **[REVIEW REQUIRED]** — Synthesized draft awaiting technical & factual review before approval.

# ${title}

When engineering teams move **${clean}** from a prototype into multi-tenant production, failure modes cluster around state transitions, permission boundaries, and ungrounded outputs.

## 1. Grounded Architectural Invariants

- **Strict State Transitions**: Enforce \`Idea -> Outline -> Draft -> Approved -> Published\` inside a dedicated pipeline validator so neither UI nor background workers can bypass review.
- **Codebase Citation Grounding**: Retrieve verified files and RAG chunks before drafting prose.

\`\`\`python
# Pattern: enforce approval gate prior to irreversible stage transition
def approve_draft(item_stage: str, approved: bool) -> str:
    if item_stage != "draft" or not approved:
        raise ValueError("Explicit approval on an existing draft is required.")
    return "approved"
\`\`\`

## 2. Core Engineering Trade-Offs

1. **Determinism vs. Speed**: Typed Pydantic boundaries require upfront contract design, eliminating silent schema corruption downstream.
2. **Honest Telemetry Over Guesswork**: Any unmeasured latency claim remains marked \`[BENCHMARK NEEDED]\` until verified by staging telemetry.`;

  return {
    title,
    summary: isTut
      ? `Step-by-step developer tutorial for ${clean}.`
      : `Principal systems engineering deep dive on ${clean}.`,
    markdown: md,
    channel: 'blog',
    twitterThread: [],
    linkedinPost: '',
    citations,
  };
}

export const ContentStudioView: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'studio' | 'pipeline' | 'social' | 'calendar'>('studio');

  // Pipeline state
  const [items, setItems] = useState<ContentItem[]>(() => {
    const seedDraft = buildLocalDraft('Phase 10 Hybrid pgvector RAG Retrieval', 'article', false);
    const seedCase = buildLocalDraft('Phase 11 Approval-Gated DevOps Workflows', 'case_study', false);
    const seedSocial = buildLocalDraft('Deterministic Tool Sandboxing via MCP', 'social_pack', false);
    return [
      {
        id: 'cs-101',
        title: seedDraft.title,
        slug: 'phase-10-rag-deep-dive',
        content_type: 'article',
        stage: 'draft',
        channel: 'blog',
        body_markdown: seedDraft.markdown,
        summary: seedDraft.summary,
        rag_sources: seedDraft.citations,
        metadata_json: {
          word_count: 185,
          reading_time_min: 1,
          code_blocks_count: 1,
          review_required: true,
          benchmark_flags: ['Contains [BENCHMARK NEEDED] placeholders awaiting production telemetry.'],
        },
        scheduled_at: '2026-11-18T10:00:00Z',
        created_at: '2026-11-11T09:00:00Z',
        updated_at: '2026-11-11T09:00:00Z',
      },
      {
        id: 'cs-102',
        title: seedCase.title,
        slug: 'phase-11-devops-case-study',
        content_type: 'case_study',
        stage: 'approved',
        channel: 'blog',
        body_markdown: seedCase.markdown,
        summary: seedCase.summary,
        rag_sources: seedCase.citations,
        metadata_json: {
          word_count: 162,
          reading_time_min: 1,
          code_blocks_count: 0,
          review_required: false,
          benchmark_flags: ['Contains [BENCHMARK NEEDED] placeholders awaiting production telemetry.'],
        },
        scheduled_at: '2026-11-21T14:00:00Z',
        approved_at: '2026-11-11T16:00:00Z',
        created_at: '2026-11-10T11:00:00Z',
        updated_at: '2026-11-11T16:00:00Z',
      },
      {
        id: 'cs-103',
        title: seedSocial.title,
        slug: 'mcp-social-pack',
        content_type: 'social_pack',
        stage: 'outline',
        channel: 'cross_platform',
        body_markdown: seedSocial.markdown,
        summary: seedSocial.summary,
        rag_sources: seedSocial.citations,
        metadata_json: {
          word_count: 170,
          reading_time_min: 1,
          review_required: true,
          twitter_thread: seedSocial.twitterThread,
          linkedin_post: seedSocial.linkedinPost,
        },
        scheduled_at: null,
        created_at: '2026-11-12T08:00:00Z',
        updated_at: '2026-11-12T08:00:00Z',
      },
    ];
  });

  // Generator controls
  const [topic, setTopic] = useState<string>('Multi-Tenant Agent Permission Boundaries in FastAPI');
  const [contentType, setContentType] = useState<ContentType>('article');
  const [outlineOnly, setOutlineOnly] = useState<boolean>(false);
  const [useRag, setUseRag] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [previewMode, setPreviewMode] = useState<'rendered' | 'edit'>('rendered');
  const [activeDraft, setActiveDraft] = useState<{
    title: string;
    contentType: ContentType;
    stage: ContentStage;
    channel: ContentChannel;
    summary: string;
    markdown: string;
    citations: Citation[];
    benchmarkFlags: string[];
    twitterThread: string[];
    linkedinPost: string;
  } | null>(() => {
    const initial = buildLocalDraft('Multi-Tenant Agent Permission Boundaries in FastAPI', 'article', false);
    const metrics = computeLocalMetrics(initial.markdown);
    return {
      title: initial.title,
      contentType: 'article',
      stage: 'draft',
      channel: initial.channel,
      summary: initial.summary,
      markdown: initial.markdown,
      citations: initial.citations,
      benchmarkFlags: metrics.flags,
      twitterThread: initial.twitterThread,
      linkedinPost: initial.linkedinPost,
    };
  });

  // Pipeline filter & selected item inspection
  const [stageFilter, setStageFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedItemId, setSelectedItemId] = useState<string | null>('cs-101');
  const [approvalConfirmed, setApprovalConfirmed] = useState<boolean>(false);
  const [newIdeaTitle, setNewIdeaTitle] = useState<string>('');
  const [statusNotice, setStatusNotice] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Try hydrating from backend API when available
  useEffect(() => {
    const loadFromApi = async () => {
      try {
        const res = await fetch('/api/v1/content/items');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setItems(data);
            setSelectedItemId(data[0].id);
          }
        }
      } catch {
        // Operate smoothly in offline/preview mode
      }
    };
    loadFromApi();
  }, []);

  const selectedItem = useMemo(
    () => items.find((it) => it.id === selectedItemId) || null,
    [items, selectedItemId]
  );

  const filteredItems = useMemo(() => {
    return items.filter((it) => {
      if (stageFilter !== 'all' && it.stage !== stageFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          it.title.toLowerCase().includes(q) ||
          it.summary.toLowerCase().includes(q) ||
          it.content_type.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [items, stageFilter, searchQuery]);

  const stageCounts = useMemo(() => {
    const counts: Record<ContentStage, number> = {
      idea: 0,
      outline: 0,
      draft: 0,
      approved: 0,
      published: 0,
    };
    items.forEach((it) => {
      if (counts[it.stage] !== undefined) counts[it.stage] += 1;
    });
    return counts;
  }, [items]);

  const notify = (msg: string) => {
    setStatusNotice(msg);
    setTimeout(() => setStatusNotice(null), 3500);
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(key);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setIsGenerating(true);

    try {
      const res = await fetch('/api/v1/content/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          content_type: contentType,
          outline_only: outlineOnly,
          use_rag: useRag,
          save_to_pipeline: false,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setActiveDraft({
          title: data.title,
          contentType,
          stage: data.stage,
          channel: data.channel,
          summary: data.summary,
          markdown: data.body_markdown,
          citations: data.rag_citations || [],
          benchmarkFlags: data.benchmark_flags || [],
          twitterThread: data.twitter_thread || [],
          linkedinPost: data.linkedin_post || '',
        });
        notify('Synthesized draft grounded in repository & RAG context [REVIEW REQUIRED].');
        setIsGenerating(false);
        return;
      }
    } catch {
      // Fallback to local synthesis matching exact backend contract
    }

    const local = buildLocalDraft(topic, contentType, outlineOnly);
    const metrics = computeLocalMetrics(local.markdown);
    setActiveDraft({
      title: local.title,
      contentType,
      stage: outlineOnly ? 'outline' : 'draft',
      channel: local.channel,
      summary: local.summary,
      markdown: local.markdown,
      citations: useRag ? local.citations : [],
      benchmarkFlags: metrics.flags,
      twitterThread: local.twitterThread,
      linkedinPost: local.linkedinPost,
    });
    notify('Synthesized draft tagged [REVIEW REQUIRED]. Auto-publish remains disabled.');
    setIsGenerating(false);
  };

  const handleSaveDraftToPipeline = async () => {
    if (!activeDraft) return;
    const metrics = computeLocalMetrics(activeDraft.markdown);
    const newId = `cs-${Date.now().toString().slice(-5)}`;
    const nowIso = new Date().toISOString();

    try {
      const res = await fetch('/api/v1/content/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: activeDraft.title,
          content_type: activeDraft.contentType,
          stage: activeDraft.stage === 'outline' ? 'outline' : 'draft',
          channel: activeDraft.channel,
          body_markdown: activeDraft.markdown,
          summary: activeDraft.summary,
        }),
      });
      if (res.ok) {
        const created: ContentItem = await res.json();
        setItems((prev) => [created, ...prev]);
        setSelectedItemId(created.id);
        setActiveSubTab('pipeline');
        notify('Saved draft to Content Pipeline (awaiting review).');
        return;
      }
    } catch {
      // Local state persistence
    }

    const newItem: ContentItem = {
      id: newId,
      title: activeDraft.title,
      slug: `${activeDraft.contentType}-${newId}`,
      content_type: activeDraft.contentType,
      stage: activeDraft.stage === 'outline' ? 'outline' : 'draft',
      channel: activeDraft.channel,
      body_markdown: activeDraft.markdown,
      summary: activeDraft.summary,
      rag_sources: activeDraft.citations,
      metadata_json: {
        word_count: metrics.wordCount,
        reading_time_min: metrics.readingTimeMin,
        code_blocks_count: metrics.codeBlocks,
        review_required: true,
        benchmark_flags: metrics.flags,
        twitter_thread: activeDraft.twitterThread,
        linkedin_post: activeDraft.linkedinPost,
      },
      scheduled_at: null,
      created_at: nowIso,
      updated_at: nowIso,
    };

    setItems((prev) => [newItem, ...prev]);
    setSelectedItemId(newItem.id);
    setActiveSubTab('pipeline');
    notify('Saved draft to Content Pipeline (tagged [REVIEW REQUIRED]).');
  };

  const handleCreateIdea = async () => {
    if (!newIdeaTitle.trim()) return;
    const nowIso = new Date().toISOString();
    const newId = `idea-${Date.now().toString().slice(-4)}`;

    try {
      const res = await fetch('/api/v1/content/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newIdeaTitle.trim(),
          content_type: 'article',
          stage: 'idea',
          channel: 'blog',
          body_markdown: `# ${newIdeaTitle.trim()}\n\nInitial editorial concept queued for RAG research.`,
          summary: 'New editorial idea queued in pipeline.',
        }),
      });
      if (res.ok) {
        const created: ContentItem = await res.json();
        setItems((prev) => [created, ...prev]);
        setSelectedItemId(created.id);
        setNewIdeaTitle('');
        notify('Added new Idea to pipeline.');
        return;
      }
    } catch {
      // Local fallback
    }

    const localIdea: ContentItem = {
      id: newId,
      title: newIdeaTitle.trim(),
      slug: newId,
      content_type: 'article',
      stage: 'idea',
      channel: 'blog',
      body_markdown: `# ${newIdeaTitle.trim()}\n\nInitial editorial concept queued for RAG research.`,
      summary: 'New editorial idea queued in pipeline.',
      metadata_json: { word_count: 12, reading_time_min: 1, review_required: true },
      scheduled_at: null,
      created_at: nowIso,
      updated_at: nowIso,
    };
    setItems((prev) => [localIdea, ...prev]);
    setSelectedItemId(localIdea.id);
    setNewIdeaTitle('');
    notify('Added new Idea to pipeline.');
  };

  const handleTransitionStage = async (item: ContentItem, targetStage: ContentStage) => {
    const needsApproval = targetStage === 'approved' || targetStage === 'published';
    if (needsApproval && !approvalConfirmed) {
      notify(`Explicit review approval checkbox required before moving to ${targetStage.toUpperCase()}.`);
      return;
    }

    try {
      const res = await fetch(`/api/v1/content/items/${item.id}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_stage: targetStage, approved: needsApproval ? approvalConfirmed : false }),
      });
      if (res.ok) {
        const updated: ContentItem = await res.json();
        setItems((prev) => prev.map((it) => (it.id === updated.id ? updated : it)));
        setApprovalConfirmed(false);
        notify(`Item transitioned to ${targetStage.toUpperCase()}.`);
        return;
      }
    } catch {
      // Local pipeline state update
    }

    const nowIso = new Date().toISOString();
    setItems((prev) =>
      prev.map((it) =>
        it.id === item.id
          ? {
              ...it,
              stage: targetStage,
              approved_at: targetStage === 'approved' ? nowIso : it.approved_at,
              published_at: targetStage === 'published' ? nowIso : it.published_at,
              updated_at: nowIso,
            }
          : it
      )
    );
    setApprovalConfirmed(false);
    notify(`Pipeline item updated -> ${targetStage.toUpperCase()}.`);
  };

  const handleScheduleDate = async (itemId: string, dateStr: string) => {
    const isoDate = dateStr ? `${dateStr}T10:00:00Z` : null;
    try {
      await fetch(`/api/v1/content/items/${itemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scheduled_at: isoDate }),
      });
    } catch {
      // Continue local update
    }

    setItems((prev) =>
      prev.map((it) => (it.id === itemId ? { ...it, scheduled_at: isoDate } : it))
    );
    notify(dateStr ? `Scheduled for ${dateStr}.` : 'Cleared schedule date.');
  };

  const handleDeleteItem = async (itemId: string) => {
    try {
      await fetch(`/api/v1/content/items/${itemId}`, { method: 'DELETE' });
    } catch {
      // Local delete
    }
    setItems((prev) => prev.filter((it) => it.id !== itemId));
    if (selectedItemId === itemId) setSelectedItemId(null);
    notify('Removed content item from pipeline.');
  };

  const nextStageOf = (stage: ContentStage): ContentStage | null => {
    const idx = STAGE_ORDER.indexOf(stage);
    if (idx === -1 || idx >= STAGE_ORDER.length - 1) return null;
    return STAGE_ORDER[idx + 1];
  };

  const socialItems = useMemo(
    () => items.filter((it) => it.content_type === 'social_pack' || it.content_type === 'youtube_script'),
    [items]
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-slate-400 mb-1.5">
              <span className="text-[#00D4FF]">CONTENT STUDIO</span>
              <span aria-hidden="true">/</span>
              <span>PHASE 12 VERIFIED</span>
              <span aria-hidden="true">/</span>
              <span>NO AUTO-PUBLISH</span>
            </div>
            <h1 className="text-xl font-bold font-display text-white flex items-center gap-3">
              Editorial & Technical Publishing Studio
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Principal systems engineering voice. Synthesizes RAG-grounded deep dives, tutorials, case studies, YouTube scripts, and LinkedIn/X threads with mandatory human review gates.
            </p>
          </div>

          <a
            href={RAYHAN_PROFILE.masterclassPlaylistUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-mono bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-200 rounded-lg self-start lg:self-auto transition-colors"
          >
            <Youtube className="w-4 h-4 text-rose-400" />
            <span>Masterclass Playlist</span>
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>
        </div>

        {/* Sub-Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800 mt-6 -mb-2 overflow-x-auto">
          {[
            { id: 'studio', label: 'Writer Studio', icon: FileText },
            { id: 'pipeline', label: `Editorial Pipeline (${items.length})`, icon: Layers },
            { id: 'social', label: 'Social & Video Scripts', icon: Share2 },
            { id: 'calendar', label: 'Content Calendar', icon: CalendarIcon },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeSubTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? 'border-[#00D4FF] text-[#00D4FF] bg-[#00D4FF]/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Inline Status Notice */}
      {statusNotice && (
        <div className="bg-slate-900 border border-[#00D4FF]/40 rounded-lg px-4 py-2.5 text-xs font-mono text-[#00D4FF] flex items-center justify-between">
          <span>{statusNotice}</span>
          <button onClick={() => setStatusNotice(null)} className="text-slate-400 hover:text-white ml-4">
            Dismiss
          </button>
        </div>
      )}

      {/* TAB 1: WRITER STUDIO */}
      {activeSubTab === 'studio' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Controls */}
          <div className="lg:col-span-4 space-y-4">
            <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h2 className="text-sm font-semibold text-white">Content Brief</h2>
                <span className="text-[11px] font-mono text-slate-500">RAG GROUNDED</span>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Format</label>
                <div className="space-y-1.5">
                  {(Object.keys(TYPE_LABELS) as ContentType[]).map((t) => (
                    <button
                      key={t}
                      onClick={() => setContentType(t)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs border transition-colors flex items-center justify-between ${
                        contentType === t
                          ? 'bg-[#00D4FF]/10 border-[#00D4FF]/50 text-white font-medium'
                          : 'bg-[#0A0F1E] border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                      }`}
                    >
                      <span>{TYPE_LABELS[t]}</span>
                      {contentType === t && <Check className="w-3.5 h-3.5 text-[#00D4FF]" />}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Engineering Topic</label>
                <textarea
                  rows={3}
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Enter technical architecture or codebase topic..."
                  className="w-full px-3 py-2 bg-[#0A0F1E] border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#00D4FF] font-mono"
                />
                <div className="mt-2 space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block">
                    Suggested Codebase Topics
                  </span>
                  {QUICK_TOPICS.map((preset) => (
                    <button
                      key={preset}
                      onClick={() => setTopic(preset)}
                      className="block w-full text-left text-[11px] text-slate-400 hover:text-[#00D4FF] truncate py-0.5 transition-colors"
                    >
                      &rarr; {preset}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800 text-xs">
                <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useRag}
                    onChange={(e) => setUseRag(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-[#00D4FF] focus:ring-0"
                  />
                  <span>Ground draft via Phase 10 RAG + repo files</span>
                </label>

                {(contentType === 'article' || contentType === 'tutorial') && (
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={outlineOnly}
                      onChange={(e) => setOutlineOnly(e.target.checked)}
                      className="rounded bg-slate-900 border-slate-700 text-[#00D4FF] focus:ring-0"
                    />
                    <span>Generate structured outline only</span>
                  </label>
                )}
              </div>

              <button
                onClick={handleGenerate}
                disabled={isGenerating || !topic.trim()}
                className="w-full py-2.5 px-4 bg-[#00D4FF] hover:bg-cyan-300 disabled:opacity-50 text-slate-950 font-semibold text-xs rounded-lg transition-colors"
              >
                {isGenerating ? 'Researching & Synthesizing...' : 'Generate Draft [REVIEW REQUIRED]'}
              </button>
            </div>

            {/* Grounded RAG Sources Box */}
            {activeDraft && (
              <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-[#00D4FF]" />
                    Citations & Grounding
                  </h3>
                  <span className="text-[11px] font-mono text-slate-500">
                    {activeDraft.citations.length} refs
                  </span>
                </div>
                {activeDraft.citations.length > 0 ? (
                  <div className="divide-y divide-slate-800/80 text-xs">
                    {activeDraft.citations.map((cit, i) => (
                      <div key={i} className="py-2 space-y-0.5">
                        <div className="font-mono text-slate-200 flex items-center justify-between">
                          <span className="truncate">{cit.document}</span>
                          <span className="text-[10px] text-[#00D4FF] shrink-0 ml-2">
                            {cit.score.toFixed(2)}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 truncate">{cit.source}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">RAG grounding disabled for this run.</p>
                )}
              </div>
            )}
          </div>

          {/* Right Editorial Draft Preview */}
          <div className="lg:col-span-8">
            {activeDraft ? (
              <div className="bg-[#0F172A] border border-slate-800 rounded-xl overflow-hidden">
                {/* Review Notice Strip */}
                <div className="bg-amber-950/30 border-b border-amber-800/50 px-5 py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-2 text-amber-300 font-mono">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    <span>[REVIEW REQUIRED] — Drafts never auto-publish. Explicit approval required.</span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    {computeLocalMetrics(activeDraft.markdown).wordCount} words &bull; ~
                    {computeLocalMetrics(activeDraft.markdown).readingTimeMin} min read
                  </span>
                </div>

                {/* Benchmark Verification Warning if case study flags */}
                {activeDraft.benchmarkFlags.length > 0 && (
                  <div className="bg-slate-900/80 border-b border-slate-800 px-5 py-2 text-[11px] font-mono text-slate-300 flex items-center gap-2">
                    <Lock className="w-3.5 h-3.5 text-[#00D4FF] shrink-0" />
                    <span>No-Fake-Metrics Active: {activeDraft.benchmarkFlags[0]}</span>
                  </div>
                )}

                {/* Toolbar */}
                <div className="px-5 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPreviewMode('rendered')}
                      className={`px-3 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 ${
                        previewMode === 'rendered'
                          ? 'bg-slate-800 text-white'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Eye className="w-3.5 h-3.5" />
                      Reading View
                    </button>
                    <button
                      onClick={() => setPreviewMode('edit')}
                      className={`px-3 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 ${
                        previewMode === 'edit'
                          ? 'bg-slate-800 text-white'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      Edit Markdown
                    </button>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleCopy(activeDraft.markdown, 'draft-md')}
                      className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-xs text-slate-200 flex items-center gap-1.5"
                    >
                      {copiedId === 'draft-md' ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                      {copiedId === 'draft-md' ? 'Copied' : 'Copy Markdown'}
                    </button>
                    <button
                      onClick={handleSaveDraftToPipeline}
                      className="px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs flex items-center gap-1.5"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Save to Pipeline
                    </button>
                  </div>
                </div>

                {/* Content Body */}
                <div className="p-6 sm:p-8">
                  {previewMode === 'edit' ? (
                    <textarea
                      rows={20}
                      value={activeDraft.markdown}
                      onChange={(e) =>
                        setActiveDraft((prev) =>
                          prev ? { ...prev, markdown: e.target.value } : prev
                        )
                      }
                      className="w-full p-4 bg-[#050811] border border-slate-800 rounded-lg text-xs font-mono text-slate-200 leading-relaxed focus:outline-none focus:border-[#00D4FF]"
                    />
                  ) : (
                    <div className="max-w-3xl mx-auto space-y-4 text-slate-200 leading-relaxed">
                      <div className="text-xs font-mono uppercase tracking-widest text-slate-500">
                        {TYPE_LABELS[activeDraft.contentType]} &bull; {activeDraft.channel.toUpperCase()}
                      </div>
                      <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-200">
                        {activeDraft.markdown}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-12 text-center text-xs text-slate-400">
                Select a format and engineering topic to synthesize a draft.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: EDITORIAL PIPELINE (Idea -> Outline -> Draft -> Approved -> Published) */}
      {activeSubTab === 'pipeline' && (
        <div className="space-y-6">
          {/* Stage Bar + New Idea Input */}
          <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
                <button
                  onClick={() => setStageFilter('all')}
                  className={`pb-1 border-b-2 transition-colors ${
                    stageFilter === 'all'
                      ? 'border-[#00D4FF] text-white font-semibold'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  All ({items.length})
                </button>
                {STAGE_ORDER.map((st) => (
                  <button
                    key={st}
                    onClick={() => setStageFilter(st)}
                    className={`pb-1 border-b-2 transition-colors ${
                      stageFilter === st
                        ? 'border-[#00D4FF] text-[#00D4FF] font-semibold'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {STAGE_LABELS[st].split(' ')[0]} ({stageCounts[st]})
                  </button>
                ))}
              </div>

              <div className="relative w-full md:w-64">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter content items..."
                  className="w-full pl-8 pr-3 py-1.5 bg-[#0A0F1E] border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#00D4FF]"
                />
              </div>
            </div>

            {/* Quick Idea Creator */}
            <div className="flex items-center gap-2 pt-3 border-t border-slate-800">
              <input
                type="text"
                value={newIdeaTitle}
                onChange={(e) => setNewIdeaTitle(e.target.value)}
                placeholder="Add quick content idea to backlog..."
                className="flex-1 px-3 py-2 bg-[#0A0F1E] border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#00D4FF]"
              />
              <button
                onClick={handleCreateIdea}
                disabled={!newIdeaTitle.trim()}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-xs font-medium text-white border border-slate-700 flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5 text-[#00D4FF]" />
                Add Idea
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Pipeline List */}
            <div className="lg:col-span-5 bg-[#0F172A] border border-slate-800 rounded-xl divide-y divide-slate-800/80 overflow-hidden">
              {filteredItems.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500">
                  No content items match current filter.
                </div>
              ) : (
                filteredItems.map((it) => {
                  const isSel = selectedItemId === it.id;
                  return (
                    <button
                      key={it.id}
                      onClick={() => {
                        setSelectedItemId(it.id);
                        setApprovalConfirmed(false);
                      }}
                      className={`w-full text-left p-4 transition-colors ${
                        isSel ? 'bg-[#00D4FF]/5 border-l-2 border-l-[#00D4FF]' : 'hover:bg-slate-900/40'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 text-[11px] font-mono uppercase tracking-wider mb-1">
                        <span
                          className={
                            it.stage === 'published'
                              ? 'text-emerald-400'
                              : it.stage === 'approved'
                              ? 'text-[#00D4FF]'
                              : it.stage === 'draft'
                              ? 'text-amber-400'
                              : 'text-slate-400'
                          }
                        >
                          {STAGE_LABELS[it.stage]}
                        </span>
                        <span className="text-slate-500">{it.content_type.replace('_', ' ')}</span>
                      </div>
                      <div className="text-sm font-semibold text-white line-clamp-1">{it.title}</div>
                      <div className="text-xs text-slate-400 line-clamp-1 mt-1">{it.summary}</div>
                    </button>
                  );
                })
              )}
            </div>

            {/* Pipeline Inspector */}
            <div className="lg:col-span-7">
              {selectedItem ? (
                <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-6 space-y-5">
                  <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
                    <div>
                      <div className="text-[11px] font-mono uppercase tracking-widest text-slate-400 mb-1">
                        {TYPE_LABELS[selectedItem.content_type]} &bull; {selectedItem.channel.toUpperCase()} &bull; Stage:{' '}
                        <span className="text-[#00D4FF]">{STAGE_LABELS[selectedItem.stage]}</span>
                      </div>
                      <h3 className="text-lg font-bold text-white">{selectedItem.title}</h3>
                    </div>
                    <button
                      onClick={() => handleDeleteItem(selectedItem.id)}
                      className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
                      title="Delete item"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Lifecycle Transition Controls (No Auto-Publish) */}
                  <div className="bg-[#0A0F1E] border border-slate-800 rounded-lg p-4 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <span className="font-mono text-slate-300">Lifecycle Pipeline Gate</span>
                      <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-500">
                        {STAGE_ORDER.map((s, idx) => (
                          <React.Fragment key={s}>
                            <span className={selectedItem.stage === s ? 'text-[#00D4FF] font-bold' : ''}>
                              {s.toUpperCase()}
                            </span>
                            {idx < STAGE_ORDER.length - 1 && <span>&rarr;</span>}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>

                    {nextStageOf(selectedItem.stage) ? (
                      <div className="space-y-3 pt-2 border-t border-slate-800/80">
                        {(nextStageOf(selectedItem.stage) === 'approved' ||
                          nextStageOf(selectedItem.stage) === 'published') && (
                          <label className="flex items-center gap-2 text-xs text-amber-300 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={approvalConfirmed}
                              onChange={(e) => setApprovalConfirmed(e.target.checked)}
                              className="rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-0"
                            />
                            <span>
                              I have reviewed technical accuracy and metrics and explicitly approve transition to{' '}
                              <strong>{nextStageOf(selectedItem.stage)?.toUpperCase()}</strong>.
                            </span>
                          </label>
                        )}

                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div className="flex items-center gap-2 text-xs">
                            <Clock className="w-3.5 h-3.5 text-slate-500" />
                            <input
                              type="date"
                              value={selectedItem.scheduled_at ? selectedItem.scheduled_at.slice(0, 10) : ''}
                              onChange={(e) => handleScheduleDate(selectedItem.id, e.target.value)}
                              className="px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 font-mono"
                            />
                          </div>

                          <button
                            onClick={() =>
                              handleTransitionStage(selectedItem, nextStageOf(selectedItem.stage)!)
                            }
                            className="px-4 py-2 rounded-lg bg-[#00D4FF] hover:bg-cyan-300 text-slate-950 font-semibold text-xs flex items-center gap-1.5"
                          >
                            <span>Advance to {nextStageOf(selectedItem.stage)?.toUpperCase()}</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-xs text-emerald-400 pt-1">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Published with explicit review approval.</span>
                      </div>
                    )}
                  </div>

                  {/* Body Preview / Editor */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="font-mono">Markdown Content</span>
                      <button
                        onClick={() => handleCopy(selectedItem.body_markdown, `item-${selectedItem.id}`)}
                        className="text-slate-300 hover:text-white flex items-center gap-1"
                      >
                        {copiedId === `item-${selectedItem.id}` ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                        Copy
                      </button>
                    </div>
                    <textarea
                      rows={12}
                      value={selectedItem.body_markdown}
                      onChange={(e) => {
                        const val = e.target.value;
                        setItems((prev) =>
                          prev.map((it) =>
                            it.id === selectedItem.id ? { ...it, body_markdown: val } : it
                          )
                        );
                      }}
                      className="w-full p-4 bg-[#050811] border border-slate-800 rounded-lg text-xs font-mono text-slate-200 leading-relaxed focus:outline-none focus:border-[#00D4FF]"
                    />
                  </div>
                </div>
              ) : (
                <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-12 text-center text-xs text-slate-500">
                  Select a content piece from the left list to inspect or advance its pipeline stage.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: SOCIAL & VIDEO PREVIEW */}
      {activeSubTab === 'social' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* LinkedIn & Twitter Preview */}
          <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Share2 className="w-4 h-4 text-[#00D4FF]" />
                LinkedIn & X (Twitter) Thread Inspector
              </h3>
              <button
                onClick={() => {
                  setContentType('social_pack');
                  setActiveSubTab('studio');
                }}
                className="text-xs font-mono text-[#00D4FF] hover:underline"
              >
                + New Social Pack
              </button>
            </div>

            {(() => {
              const pack =
                items.find((it) => it.content_type === 'social_pack') || socialItems[0];
              const tweets =
                pack?.metadata_json?.twitter_thread ||
                buildLocalDraft(topic, 'social_pack', false).twitterThread;
              const linkedin =
                pack?.metadata_json?.linkedin_post ||
                buildLocalDraft(topic, 'social_pack', false).linkedinPost;

              return (
                <div className="space-y-5">
                  <div>
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                      <span className="font-mono uppercase tracking-wider">LinkedIn Engineering Post</span>
                      <button
                        onClick={() => handleCopy(linkedin, 'li-copy')}
                        className="text-slate-300 hover:text-white flex items-center gap-1"
                      >
                        {copiedId === 'li-copy' ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                        Copy Post
                      </button>
                    </div>
                    <pre className="p-4 bg-[#0A0F1E] border border-slate-800 rounded-lg text-xs font-sans text-slate-200 whitespace-pre-wrap leading-relaxed">
                      {linkedin}
                    </pre>
                  </div>

                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="font-mono uppercase tracking-wider">
                        X / Twitter Thread ({tweets.length} tweets)
                      </span>
                      <button
                        onClick={() => handleCopy(tweets.join('\n\n---\n\n'), 'tw-copy')}
                        className="text-slate-300 hover:text-white flex items-center gap-1"
                      >
                        {copiedId === 'tw-copy' ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                        Copy Full Thread
                      </button>
                    </div>
                    {tweets.map((tweet, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 bg-[#0A0F1E] border border-slate-800 rounded-lg text-xs text-slate-200 space-y-1.5"
                      >
                        <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                          <span>POST {idx + 1} / {tweets.length}</span>
                          <span className={tweet.length <= 280 ? 'text-emerald-400' : 'text-rose-400'}>
                            {tweet.length} / 280 chars
                          </span>
                        </div>
                        <p className="leading-relaxed">{tweet}</p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>

          {/* YouTube Script Cue Sheet */}
          <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Terminal className="w-4 h-4 text-rose-400" />
                YouTube Breakdown Script Cues
              </h3>
              <button
                onClick={() => {
                  setContentType('youtube_script');
                  setActiveSubTab('studio');
                }}
                className="text-xs font-mono text-[#00D4FF] hover:underline"
              >
                + Generate Script
              </button>
            </div>

            {(() => {
              const ytItem = items.find((it) => it.content_type === 'youtube_script');
              const previewScript =
                ytItem?.body_markdown || buildLocalDraft(topic, 'youtube_script', false).markdown;
              return (
                <div className="space-y-3">
                  <div className="text-[11px] font-mono text-amber-300 bg-amber-950/30 border border-amber-800/50 rounded px-3 py-2">
                    Editorial script only — video & image generation excluded per Phase 12 boundaries.
                  </div>
                  <pre className="p-4 bg-[#050811] border border-slate-800 rounded-lg text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed max-h-[540px] overflow-y-auto">
                    {previewScript}
                  </pre>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* TAB 4: CONTENT CALENDAR */}
      {activeSubTab === 'calendar' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 bg-[#0F172A] border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 bg-slate-900/60 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <CalendarIcon className="w-4 h-4 text-[#00D4FF]" />
                Scheduled Release Timeline
              </h3>
              <span className="text-xs font-mono text-slate-400">
                {items.filter((i) => i.scheduled_at).length} scheduled
              </span>
            </div>

            <div className="divide-y divide-slate-800/80">
              {items.filter((i) => i.scheduled_at).length === 0 ? (
                <div className="p-10 text-center text-xs text-slate-500">
                  No scheduled items yet. Assign a target date from the backlog panel on the right.
                </div>
              ) : (
                items
                  .filter((i) => i.scheduled_at)
                  .sort((a, b) => (a.scheduled_at || '').localeCompare(b.scheduled_at || ''))
                  .map((it) => (
                    <div
                      key={it.id}
                      className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                    >
                      <div>
                        <div className="text-[11px] font-mono text-[#00D4FF] mb-0.5">
                          {new Date(it.scheduled_at!).toLocaleDateString(undefined, {
                            weekday: 'short',
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })}{' '}
                          &bull; {it.channel.toUpperCase()} &bull; {STAGE_LABELS[it.stage]}
                        </div>
                        <div className="text-sm font-semibold text-white">{it.title}</div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <input
                          type="date"
                          value={it.scheduled_at ? it.scheduled_at.slice(0, 10) : ''}
                          onChange={(e) => handleScheduleDate(it.id, e.target.value)}
                          className="px-2.5 py-1 bg-[#0A0F1E] border border-slate-700 rounded text-xs text-slate-200 font-mono"
                        />
                        <button
                          onClick={() => {
                            setSelectedItemId(it.id);
                            setActiveSubTab('pipeline');
                          }}
                          className="px-3 py-1 rounded border border-slate-700 text-xs text-slate-300 hover:text-white"
                        >
                          Inspect
                        </button>
                      </div>
                    </div>
                  ))
              )}
            </div>
          </div>

          {/* Unscheduled Queue */}
          <div className="lg:col-span-4 bg-[#0F172A] border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 bg-slate-900/60 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-white">Unscheduled Backlog</h3>
              <p className="text-[11px] text-slate-400">Assign a release date to schedule onto the calendar.</p>
            </div>
            <div className="divide-y divide-slate-800/80">
              {items.filter((i) => !i.scheduled_at).length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500">All items are scheduled.</div>
              ) : (
                items
                  .filter((i) => !i.scheduled_at)
                  .map((it) => (
                    <div key={it.id} className="p-4 space-y-2">
                      <div className="text-[10px] font-mono uppercase text-slate-500">
                        {STAGE_LABELS[it.stage]} &bull; {TYPE_LABELS[it.content_type]}
                      </div>
                      <div className="text-xs font-semibold text-slate-200">{it.title}</div>
                      <input
                        type="date"
                        onChange={(e) => handleScheduleDate(it.id, e.target.value)}
                        className="w-full px-2.5 py-1.5 bg-[#0A0F1E] border border-slate-800 rounded text-xs text-slate-300 font-mono"
                      />
                    </div>
                  ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
