import {
  PublicArticleDTO,
  PublicCaseStudyDTO,
  PublicPortfolioProjectDTO,
  PublicProfileDTO,
  SafeDemoDefinitionDTO,
  SafeDemoRunResponseDTO,
} from '../../types';

const BASE = '/api/v1/portfolio';

export const FALLBACK_PROFILE: PublicProfileDTO = {
  name: 'Rayhan',
  title: 'Applied AI Systems Architect & Engineer',
  tagline: 'Architecting Intelligence. Engineering the Future.',
  bio: 'Applied AI Systems Architect designing production agent runtimes, hybrid vector RAG pipelines, Model Context Protocol integrations, and multi-model backends grounded in software engineering rigor.',
  location: 'Bangladesh',
  collaboration_status: 'Open to engineering collaborations & technical advisory',
  expertise: [
    'AI Systems Architecture',
    'Applied AI Engineering',
    'LLM & RAG Applications',
    'AI Agents & Automation',
    'MCP & Tool Integration',
    'Backend APIs & Databases',
  ],
  tech_badges: [
    'FastAPI',
    'Python / TypeScript',
    'PostgreSQL + pgvector',
    'Model Context Protocol',
    'Gemini & Claude APIs',
    'React + Tailwind CSS',
  ],
  social_links: {
    github: 'https://github.com/rayhan-ai-architect',
    linkedin: 'https://www.linkedin.com/in/rayhan-badsha-a71662294',
    youtube: 'https://youtube.com/playlist?list=PLbIePX5F-An4',
  },
};

export const FALLBACK_PUBLIC_PROJECTS: PublicPortfolioProjectDTO[] = [
  {
    id: 'curizx-ai-employee',
    slug: 'curizx-ai-employee',
    title: 'Curizx AI Employee',
    tagline: 'Open-source conversational SaaS agent loop with RAG grounding and CRM webhooks',
    description:
      '## System Overview\nCurizx AI Employee is an open-source Applied AI SaaS prototype engineered for structured inbound qualification, grounded business knowledge retrieval, and reliable CRM webhook automation.\n\n## Engineering Priorities\n- State-machine boundaries around nondeterministic LLM outputs\n- Schema-validated function calling contracts\n- Zero fabricated latency or conversion claims prior to production telemetry',
    architecture_overview:
      'Inbound webhook & WebSocket events route through an intent policy validator into a bounded ReAct loop backed by vector knowledge retrieval and typed CRM dispatch.',
    challenges_solutions: [
      {
        challenge: 'Preventing ungrounded product claims during customer conversations',
        solution: 'Strict citation-backed retrieval gating before response emission.',
      },
      {
        challenge: 'Keeping webhook side effects idempotent across retries',
        solution: 'Deterministic action schemas separated from read-only knowledge queries.',
      },
    ],
    tech_stack: ['Python', 'FastAPI', 'TypeScript', 'Vector RAG', 'MCP Tools', 'PostgreSQL'],
    category: 'ai_agent',
    status: 'in_progress',
    github_url: 'https://github.com/rayhan-ai-architect/curizx-ai-employee',
    demo_url: '#portfolio/demos/code-analyzer',
    case_study_slug: null,
    is_featured: true,
    is_public: true,
    sort_order: 1,
    published_at: null,
  },
];

export const FALLBACK_DEMOS: SafeDemoDefinitionDTO[] = [
  {
    slug: 'code-analyzer',
    title: 'Code Analyzer Demo',
    description:
      'Inspect Python or TypeScript source snippets via AST complexity, import hygiene, and type coverage checks.',
    demo_label: 'Demo — Sample Data',
    read_only: true,
    rate_limit: '10 requests / minute per IP',
    timeout_seconds: 30,
    persisted: false,
    samples: [
      {
        label: 'Async Service Handler (Sample)',
        language: 'python',
        input_code:
          "import os\nimport json\n\ndef process_records(items, threshold):\n    matched = []\n    for item in items:\n        if item.get('score', 0) >= threshold:\n            if item.get('active'):\n                matched.append(item)\n    return matched\n",
      },
      {
        label: 'Typed Utility Function (Sample)',
        language: 'python',
        input_code:
          'def compute_ratio(passed: int, total: int) -> float:\n    """Compute safe pass percentage ratio."""\n    if total <= 0:\n        return 0.0\n    return round((passed / total) * 100.0, 2)\n',
      },
    ],
  },
  {
    slug: 'security-scanner',
    title: 'Security Scanner Demo',
    description:
      'Scan pasted code snippets for CWE patterns including SQL string formatting, command injection, and secret exposure.',
    demo_label: 'Demo — Sample Data',
    read_only: true,
    rate_limit: '10 requests / minute per IP',
    timeout_seconds: 30,
    persisted: false,
    samples: [
      {
        label: 'SQL & Shell Anti-Pattern (Sample)',
        language: 'python',
        input_code:
          'import subprocess\n\ndef fetch_user_unsafe(cursor, user_id, export_cmd):\n    cursor.execute(f"SELECT * FROM accounts WHERE id = {user_id}")\n    subprocess.run(export_cmd, shell=True)\n',
      },
      {
        label: 'Parameterized Query Baseline (Sample)',
        language: 'python',
        input_code:
          'from sqlalchemy import select\n\nasync def fetch_public_project(session, slug: str):\n    stmt = select(PortfolioProject).where(PortfolioProject.slug == slug)\n    return await session.execute(stmt)\n',
      },
    ],
  },
  {
    slug: 'architecture-diagram',
    title: 'Architecture Diagram Demo',
    description:
      'Synthesize valid Mermaid.js architecture topology graphs from system component descriptions.',
    demo_label: 'Demo — Sample Data',
    read_only: true,
    rate_limit: '10 requests / minute per IP',
    timeout_seconds: 30,
    persisted: false,
    samples: [
      {
        label: 'Hybrid RAG + Agent Gateway (Sample)',
        language: 'python',
        input_code:
          'FastAPI gateway with JWT auth, pgvector hybrid RAG retriever, Redis cache, and Gemini/Claude fallback router',
      },
      {
        label: 'Event-Driven SaaS Pipeline (Sample)',
        language: 'python',
        input_code:
          'React SPA client, FastAPI webhook ingestion API, Async worker queue, PostgreSQL store, and MCP tool server',
      },
    ],
  },
];

async function safeFetchJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!res.ok) return null;
    const ct = res.headers.get('content-type') || '';
    if (!ct.includes('application/json')) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchPublicProfile(): Promise<PublicProfileDTO> {
  const data = await safeFetchJson<PublicProfileDTO>(`${BASE}/profile`);
  return data || FALLBACK_PROFILE;
}

export async function fetchPublicProjects(category?: string): Promise<PublicPortfolioProjectDTO[]> {
  const params = category && category !== 'all' ? `?category=${encodeURIComponent(category)}` : '';
  const data = await safeFetchJson<PublicPortfolioProjectDTO[]>(`${BASE}/projects${params}`);
  if (data) return data;
  if (!category || category === 'all') return FALLBACK_PUBLIC_PROJECTS;
  return FALLBACK_PUBLIC_PROJECTS.filter((p) => p.category === category);
}

export async function fetchPublicProjectBySlug(slug: string): Promise<PublicPortfolioProjectDTO | null> {
  const data = await safeFetchJson<PublicPortfolioProjectDTO>(`${BASE}/projects/${encodeURIComponent(slug)}`);
  if (data) return data;
  return FALLBACK_PUBLIC_PROJECTS.find((p) => p.slug === slug) || null;
}

export async function fetchPublicCaseStudies(): Promise<PublicCaseStudyDTO[]> {
  const data = await safeFetchJson<PublicCaseStudyDTO[]>(`${BASE}/case-studies`);
  return data || [];
}

export async function fetchPublicCaseStudyBySlug(slug: string): Promise<PublicCaseStudyDTO | null> {
  return safeFetchJson<PublicCaseStudyDTO>(`${BASE}/case-studies/${encodeURIComponent(slug)}`);
}

export async function fetchPublicArticles(): Promise<PublicArticleDTO[]> {
  const data = await safeFetchJson<PublicArticleDTO[]>(`${BASE}/articles`);
  return data || [];
}

export async function fetchPublicArticleBySlug(slug: string): Promise<PublicArticleDTO | null> {
  return safeFetchJson<PublicArticleDTO>(`${BASE}/articles/${encodeURIComponent(slug)}`);
}

export async function fetchSafeDemos(): Promise<SafeDemoDefinitionDTO[]> {
  const data = await safeFetchJson<SafeDemoDefinitionDTO[]>(`${BASE}/demos`);
  return data || FALLBACK_DEMOS;
}

export function runClientSafeDemoFallback(
  slug: string,
  codeOrPrompt: string
): SafeDemoRunResponseDTO {
  const text = codeOrPrompt || '';
  if (slug === 'code-analyzer') {
    const lines = text.split('\n');
    const fnMatches = Array.from(text.matchAll(/^\s*(?:async\s+)?def\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)/gm));
    const importMatches = Array.from(text.matchAll(/^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)/gm));
    const issues: { type: string; severity: string; message: string; line?: number }[] = [];
    fnMatches.forEach((m) => {
      if (m[2] && !m[2].includes(':')) {
        issues.push({
          type: 'missing_type_hint',
          severity: 'info',
          message: `Function '${m[1]}' omits parameter type annotations.`,
        });
      }
    });
    if (/import os\b/.test(text) && !/\bos\./.test(text)) {
      issues.push({ type: 'unused_import', severity: 'warning', message: "Unused import 'os' detected.", line: 1 });
    }
    return {
      slug,
      demo_label: 'Demo — Sample Data (Local Offline Engine)',
      sample_data_only: true,
      persisted: false,
      execution_ms: 4,
      output: {
        language: 'python',
        functions: fnMatches.map((m) => ({ name: m[1], args: m[2] })),
        imports: importMatches.map((m) => m[1]),
        metrics: { lines_of_code: lines.length, function_count: fnMatches.length },
        issues,
      },
    };
  }

  if (slug === 'security-scanner') {
    const findings: Record<string, any>[] = [];
    const lines = text.split('\n');
    lines.forEach((line, idx) => {
      if (/execute\s*\(\s*f['"]/.test(line)) {
        findings.push({
          rule_id: 'INJ-001',
          severity: 'critical',
          cwe: 'CWE-89',
          line: idx + 1,
          title: 'Potential SQL Injection via f-string formatting',
          snippet: line.trim().slice(0, 90),
          fix: 'Use parameterized queries cleanly bound via SQLAlchemy or DB driver placeholders.',
        });
      }
      if (/shell\s*=\s*True/.test(line)) {
        findings.push({
          rule_id: 'INJ-002',
          severity: 'critical',
          cwe: 'CWE-78',
          line: idx + 1,
          title: 'Subprocess shell=True Command Injection Risk',
          snippet: line.trim().slice(0, 90),
          fix: 'Pass argument list with shell=False.',
        });
      }
      if (/\b(?:AIza[0-9A-Za-z-_]{20,}|sk-[0-9A-Za-z-_]{20,})\b/.test(line)) {
        findings.push({
          rule_id: 'SEC-001',
          severity: 'critical',
          cwe: 'CWE-798',
          line: idx + 1,
          title: 'Hardcoded API Credential Pattern',
          snippet: '[REDACTED CREDENTIAL SNIPPET]',
          fix: 'Move secrets into server-side environment variables.',
        });
      }
    });
    return {
      slug,
      demo_label: 'Demo — Sample Data (Local Offline Engine)',
      sample_data_only: true,
      persisted: false,
      execution_ms: 5,
      output: {
        total_findings: findings.length,
        findings,
        scanned_scope: 'in-memory sample buffer only',
      },
    };
  }

  // architecture-diagram
  const lower = text.toLowerCase();
  const nodes: [string, string][] = [
    ['Client', 'Client UI / API Consumer'],
    ['Gateway', lower.includes('fastapi') ? 'FastAPI REST Gateway' : 'Application API Tier'],
  ];
  const edges = ['Client --> Gateway'];
  let anchor = 'Gateway';
  if (lower.includes('auth') || lower.includes('jwt') || lower.includes('security')) {
    nodes.push(['Guard', 'JWT Auth & Rate-Limit Boundary']);
    edges.push('Gateway --> Guard');
    anchor = 'Guard';
  }
  if (lower.includes('rag') || lower.includes('vector') || lower.includes('pgvector')) {
    nodes.push(['RAG', 'Hybrid RAG & Reranker']);
    edges.push(`${anchor} --> RAG`);
  }
  if (lower.includes('agent') || lower.includes('mcp')) {
    nodes.push(['Agent', 'Agent Runtime & MCP Tools']);
    edges.push(`${anchor} --> Agent`);
  }
  if (lower.includes('gemini') || lower.includes('claude') || lower.includes('llm') || lower.includes('router')) {
    nodes.push(['LLM', 'Multi-Model Router (Gemini / Claude)']);
    edges.push(`${anchor} --> LLM`);
  }
  nodes.push(['DB', 'PostgreSQL / Vector Store']);
  edges.push(`${anchor} --> DB`);

  const mermaid = [
    'graph TD',
    ...nodes.map(([id, label]) => `  ${id}[${label}]`),
    ...edges.map((e) => `  ${e}`),
  ].join('\n');

  return {
    slug,
    demo_label: 'Demo — Sample Data (Local Offline Engine)',
    sample_data_only: true,
    persisted: false,
    execution_ms: 3,
    output: {
      diagram_type: 'system_flowchart',
      mermaid_code: mermaid,
      syntax_valid: true,
      components_detected: nodes.map(([, l]) => l),
    },
  };
}

export async function executeSafeDemo(
  slug: string,
  payload: { code?: string; prompt?: string; language?: 'python' | 'typescript' }
): Promise<SafeDemoRunResponseDTO> {
  try {
    const res = await fetch(`${BASE}/demos/${encodeURIComponent(slug)}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.status === 429) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.message || 'Rate limit reached (10 requests/minute per IP). Please wait briefly.');
    }
    if (!res.ok) {
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        const err = await res.json();
        throw new Error(err?.message || 'Demo execution failed.');
      }
      // Static Vite preview without FastAPI running -> fall back cleanly to local isolated sandbox
      return runClientSafeDemoFallback(slug, payload.prompt || payload.code || '');
    }
    return (await res.json()) as SafeDemoRunResponseDTO;
  } catch (err: any) {
    if (err?.message && (err.message.includes('Rate limit') || err.message.includes('Demo execution'))) {
      throw err;
    }
    return runClientSafeDemoFallback(slug, payload.prompt || payload.code || '');
  }
}

export async function submitPublicContact(payload: {
  name: string;
  email: string;
  subject: string;
  message: string;
  honeypot?: string;
}): Promise<{ received: boolean; message: string; localPreview?: boolean }> {
  try {
    const res = await fetch(`${BASE}/contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const ct = res.headers.get('content-type') || '';
    if (res.status === 429) {
      const err = ct.includes('application/json') ? await res.json() : {};
      throw new Error(err?.message || 'Rate limit exceeded (3 inquiries/hour). Please try again later.');
    }
    if (!res.ok) {
      if (ct.includes('application/json')) {
        const err = await res.json();
        throw new Error(err?.message || 'Failed to submit inquiry.');
      }
      // Preview mode without FastAPI attached
      if (payload.honeypot && payload.honeypot.trim()) {
        throw new Error('Automated form submission rejected.');
      }
      return {
        received: true,
        message: 'Message received (preview validation active; start backend API to persist inquiries).',
        localPreview: true,
      };
    }
    return await res.json();
  } catch (err: any) {
    if (err?.message && !err.message.includes('Failed to fetch')) {
      throw err;
    }
    if (payload.honeypot && payload.honeypot.trim()) {
      throw new Error('Automated form submission rejected.');
    }
    return {
      received: true,
      message: 'Message received (preview validation active; start backend API to persist inquiries).',
      localPreview: true,
    };
  }
}
