import { Agent, BengaliReport, ExecutionItem } from '../types';

export const BENGALI_LOADING_MESSAGES = [
  '⏳ কাজ চলছে...',
  '🔍 বিশ্লেষণ করা হচ্ছে...',
  '💭 উত্তর তৈরি হচ্ছে...',
  '✅ সম্পন্ন!',
] as const;

export const BENGALI_AGENTS_CATALOG: Agent[] = [
  {
    id: 'arch-sentinel',
    name: 'Coding Agent',
    codename: 'arch-sentinel',
    category: 'Engineering & Evaluation',
    role: 'AST Code Inspector & Refactoring Assistant',
    architecture: 'Static AST Verification + Sandboxed Diff & Subprocess Runner',
    targetModel: 'Gemini 2.5 Flash / Claude 3.5 Sonnet',
    tools: ['file_reader', 'ast_parser', 'diff_generator', 'test_runner'],
    status: 'Available',
    description: 'Reads codebase files safely, highlights structural issues, proposes unified diffs, and runs scoped pytest checks.',
    bengaliName: 'কোডিং সহকারী',
    bengaliTask: 'আপনার code পড়বে, সমস্যা খুঁজবে, উন্নতির পরামর্শ দেবে',
    whenToUseBn: [
      'Code review দরকার',
      'Bug খুঁজতে হবে',
      'Code quality বাড়াতে চান',
    ],
    quickPromptsBn: [
      'backend/app/main.py-এর code review ও সমস্যা খুঁজে বের করো',
      'backend/app/schemas/agent.py উন্নত করার diff পরামর্শ দাও',
    ],
    targetPathDefault: 'backend/app/main.py',
    supportsImplement: true,
  },
  {
    id: 'security-agent',
    name: 'Security Agent',
    codename: 'security-agent',
    category: 'Engineering & Evaluation',
    role: 'Vulnerability, Secret & Auth Scanner',
    architecture: 'Static OWASP Rules + Secret Scanner + Auth & CVE Auditor',
    targetModel: 'Gemini 2.5 Flash / Rule Engine',
    tools: ['secret_detector', 'auth_auditor', 'dependency_auditor', 'security_rules_catalog'],
    status: 'Available',
    description: 'Scans for hardcoded credentials, JWT/auth weaknesses, SQL injection patterns, and dependency risks.',
    bengaliName: 'নিরাপত্তা পরীক্ষক',
    bengaliTask: 'আপনার code-এর নিরাপত্তা যাচাই করবে',
    whenToUseBn: [
      'Security check দরকার',
      'Vulnerability খুঁজতে হবে',
    ],
    quickPromptsBn: [
      'আমার code-এর security check করো',
      'Authentication এবং hardcoded secret ঝুঁকি যাচাই করো',
    ],
    targetPathDefault: 'backend/app/routers/auth.py',
    supportsImplement: false,
  },
  {
    id: 'testing-agent',
    name: 'Testing Agent',
    codename: 'testing-agent',
    category: 'Engineering & Evaluation',
    role: 'Test Coverage & Gap Analyzer',
    architecture: 'Coverage Estimator + Missing Test Detector + Template Generator',
    targetModel: 'Gemini 2.5 Flash / Pytest Runner',
    tools: ['coverage_analyzer', 'test_gap_detector', 'test_generator', 'test_runner'],
    status: 'Available',
    description: 'Audits module test coverage, spots untested endpoints, generates pytest templates, and runs test suites.',
    bengaliName: 'টেস্টিং সহকারী',
    bengaliTask: 'Test coverage দেখবে, missing tests খুঁজবে',
    whenToUseBn: [
      'Test coverage কম মনে হচ্ছে',
      'New tests দরকার',
    ],
    quickPromptsBn: [
      'সম্পূর্ণ প্রজেক্টের test coverage বিশ্লেষণ করো',
      'backend/app/routers/auth.py-এর জন্য missing tests ও template তৈরি করো',
    ],
    targetPathDefault: 'backend/tests',
    supportsImplement: true,
  },
  {
    id: 'architecture-agent',
    name: 'Architecture Agent',
    codename: 'architecture-agent',
    category: 'Autonomous Agents',
    role: 'System Architect & Diagram Generator',
    architecture: 'Module Dependency Mapper + Mermaid Diagram & ADR Synthesizer',
    targetModel: 'Claude 3.5 Sonnet / Gemini 2.5 Flash',
    tools: ['architecture_analyzer', 'diagram_generator', 'adr_generator'],
    status: 'Available',
    description: 'Reviews service boundaries, draws system Mermaid diagrams, and drafts Architecture Decision Records (ADRs).',
    bengaliName: 'আর্কিটেকচার পরামর্শদাতা',
    bengaliTask: 'System diagram বানাবে, architecture review করবে',
    whenToUseBn: [
      'Diagram দরকার',
      'Architecture review চাই',
    ],
    quickPromptsBn: [
      'পুরো সিস্টেমের একটি Mermaid architecture diagram বানাও',
      'API ও Database স্তরের architecture review করো',
    ],
    supportsImplement: true,
  },
  {
    id: 'documentation-agent',
    name: 'Documentation Agent',
    codename: 'documentation-agent',
    category: 'Workflow Automation',
    role: 'API Docs & README Author',
    architecture: 'Route Docstring Auditor + Markdown Synthesizer',
    targetModel: 'Gemini 2.5 Flash / Markdown Writer',
    tools: ['doc_auditor', 'doc_generator'],
    status: 'Available',
    description: 'Audits FastAPI endpoint documentation coverage and drafts structured README, setup, or API reference docs.',
    bengaliName: 'ডকুমেন্টেশন সহকারী',
    bengaliTask: 'README, API docs লিখবে',
    whenToUseBn: [
      'Documentation দরকার',
      'README update করতে হবে',
    ],
    quickPromptsBn: [
      'API documentation-এর coverage ও মান পরীক্ষা করো',
      'প্রজেক্টের জন্য নতুন README update খসড়া লেখো',
    ],
    supportsImplement: true,
  },
  {
    id: 'rag-engine-v1',
    name: 'RAG Agent',
    codename: 'rag-engine-v1',
    category: 'RAG & Retrieval',
    role: 'Hybrid Vector & Keyword Search Engine',
    architecture: 'pgvector Cosine + BM25 Lexical Reranking with Grounded Citations',
    targetModel: 'text-embedding-004 / Gemini 2.5 Flash',
    tools: ['vector_search', 'bm25_retriever', 'gap_analyzer', 'ingestion_pipeline'],
    status: 'Available',
    description: 'Retrieves grounded answers with citations from indexed knowledge documents and identifies missing topics.',
    bengaliName: 'জ্ঞান অনুসন্ধানকারী',
    bengaliTask: 'আপনার documents থেকে উত্তর খুঁজে দেবে',
    whenToUseBn: [
      'Document থেকে তথ্য চাই',
      'Knowledge base search করতে',
    ],
    quickPromptsBn: [
      'Knowledge base-এ কী কী document আছে দেখাও',
      'JWT authentication ও rate limiting সম্পর্কে documents থেকে উত্তর খুঁজে দাও',
    ],
    supportsImplement: true,
  },
  {
    id: 'devops-agent',
    name: 'DevOps Agent',
    codename: 'devops-agent',
    category: 'Tooling & MCP',
    role: 'CI/CD, Docker & Release Readiness Guard',
    architecture: 'GitHub Actions Synthesizer + Container Audit + Health Checker',
    targetModel: 'Gemini 2.5 Flash / Infrastructure Rules',
    tools: ['cicd_generator', 'docker_validator', 'deployment_checker', 'health_monitor'],
    status: 'Available',
    description: 'Validates Dockerfile security, checks production deployment gates, and generates GitHub Actions workflows.',
    bengaliName: 'ডেভঅপস সহকারী',
    bengaliTask: 'CI/CD pipeline বানাবে, deployment চেক করবে',
    whenToUseBn: [
      'Deploy করতে চান',
      'CI/CD setup দরকার',
    ],
    quickPromptsBn: [
      'Production deployment readiness checklist যাচাই করো',
      'প্রজেক্টের জন্য GitHub Actions CI/CD workflow তৈরি করো',
    ],
    supportsImplement: true,
  },
  {
    id: 'masterclass-synth',
    name: 'Content Agent',
    codename: 'masterclass-synth',
    category: 'Workflow Automation',
    role: 'Technical Writer & Social Content Studio',
    architecture: 'RAG Topic Researcher + Review-Gated Draft Writers',
    targetModel: 'Claude 3.5 Sonnet / Gemini 2.5 Flash',
    tools: ['topic_researcher', 'article_writer', 'social_post_writer', 'youtube_script_writer'],
    status: 'Available',
    description: 'Synthesizes LinkedIn posts, technical deep-dive articles, and YouTube breakdown scripts with [REVIEW REQUIRED].',
    bengaliName: 'কন্টেন্ট লেখক',
    bengaliTask: 'LinkedIn post, article, YouTube script লিখবে',
    whenToUseBn: [
      'Post লিখতে হবে',
      'Article দরকার',
    ],
    quickPromptsBn: [
      'RAG এবং MCP architecture নিয়ে একটি LinkedIn post লেখো',
      'AI Agent safety নিয়ে একটি technical article খসড়া তৈরি করো',
    ],
    supportsImplement: true,
  },
  {
    id: 'eval-matrix',
    name: 'Eval Matrix Agent',
    codename: 'eval-matrix',
    category: 'Engineering & Evaluation',
    role: 'Deterministic Benchmark & RAG Quality Evaluator',
    architecture: 'Code AST + Security + RAG Precision@5 + LLM Quality Suite',
    targetModel: 'Deterministic Evaluator / Judge Suite',
    tools: ['code_analysis_benchmark', 'security_scan_benchmark', 'rag_retrieval_benchmark', 'llm_quality_benchmark'],
    status: 'Available',
    description: 'Runs deterministic regression benchmark suites across code rules, security detection, RAG retrieval, and quality.',
    bengaliName: 'ইভ্যালুয়েশন পরীক্ষক',
    bengaliTask: 'AI prompt ও RAG response-এর মান ও নির্ভুলতা যাচাই করবে',
    whenToUseBn: [
      'Benchmark run করতে চান',
      'RAG বা prompt accuracy দেখতে',
    ],
    quickPromptsBn: [
      'সম্পূর্ণ full benchmark suite চালিয়ে accuracy রিপোর্ট দাও',
      'RAG retrieval benchmark পরীক্ষা করো',
    ],
    supportsImplement: false,
  },
];

export const toBnDigits = (val: string | number): string => {
  const bn = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'];
  return String(val).replace(/\d/g, (d) => bn[Number(d)]);
};

export function findAgentBengaliProfile(slug?: string): Agent {
  const normalized = (slug || '').toLowerCase().trim();
  return (
    BENGALI_AGENTS_CATALOG.find((a) => a.codename === normalized || a.id === normalized) ||
    BENGALI_AGENTS_CATALOG[0]
  );
}

/**
 * Resolves an ExecutionItem into the 4-part structured Bengali Report.
 * Prefers server-provided `execution.bn_report`, with truthful client-side
 * fallback if an older/cached record lacks `bn_report`.
 */
export function resolveBengaliReport(execution: ExecutionItem): BengaliReport {
  if (execution.bn_report) {
    return execution.bn_report;
  }

  const profile = findAgentBengaliProfile(execution.agent_slug);
  const agentNameBn = profile.bengaliName || profile.name;

  if (execution.status === 'Pending') {
    if (execution.scope === 'implement') {
      return {
        language: 'bn',
        agent_slug: execution.agent_slug,
        agent_name_bn: agentNameBn,
        summary_bn: 'কাজটি চালানোর জন্য আপনার চূড়ান্ত অনুমোদন (Approval) প্রয়োজন।',
        what_agent_did: 'কাজটি গ্রহণ করা হয়েছে এবং নিরাপত্তার স্বার্থে আপনার অনুমোদনের অপেক্ষায় রাখা হয়েছে।',
        findings: ['মোড: কাজ করো (Implement)', 'কোনো ফাইল বা কমান্ড এখনো পরিবর্তন করা হয়নি।'],
        recommendations: ["অনুমোদন দিলে তবেই Agent নির্ধারিত কাজ শুরু করবে।"],
        limitations: ['Implement মোডের কাজ ব্যবহারকারীর সরাসরি সম্মতি ছাড়া চলে না।'],
      };
    }
    return {
      language: 'bn',
      agent_slug: execution.agent_slug,
      agent_name_bn: agentNameBn,
      summary_bn: '⏳ কাজটি কিউতে আছে...',
      what_agent_did: 'টাস্কটি ব্যাকগ্রাউন্ড ওয়ার্কারে পাঠানো হয়েছে।',
      findings: [`নির্দেশনা: ${execution.instruction}`],
      recommendations: ['কয়েক মুহূর্ত অপেক্ষা করুন; ফলাফল শীঘ্রই দেখা যাবে।'],
      limitations: ['চলমান কাজের চূড়ান্ত ফলাফল এখনো তৈরি হয়নি।'],
    };
  }

  if (execution.status === 'Failed' || execution.status === 'Cancelled') {
    return {
      language: 'bn',
      agent_slug: execution.agent_slug,
      agent_name_bn: agentNameBn,
      summary_bn: execution.status === 'Cancelled' ? 'কাজটি বাতিল করা হয়েছে।' : 'কাজটি সম্পন্ন করা যায়নি।',
      what_agent_did: 'নির্দেশনা ও permission পরীক্ষা করেছে, তবে ত্রুটির কারণে থেমে গেছে।',
      findings: [execution.error_message || execution.output || 'অজানা ত্রুটি ঘটেছে।'],
      recommendations: ["ইনপুট ও scope ('শুধু দেখো' / 'পরামর্শ দাও') ঠিক করে আবার চেষ্টা করুন।"],
      limitations: ['নিরাপত্তা বা যাচাইয়ে আটকে গেলে স্বয়ংক্রিয়ভাবে কাজ বন্ধ থাকে।'],
    };
  }

  const raw = (execution.output || '').trim();
  return {
    language: 'bn',
    agent_slug: execution.agent_slug,
    agent_name_bn: agentNameBn,
    summary_bn: 'বিশ্লেষণ সম্পন্ন।',
    what_agent_did: `${agentNameBn} আপনার নির্দেশনা (${execution.scope}) অনুযায়ী কাজটি সম্পন্ন করেছে।`,
    findings: raw
      ? raw
          .split('\n')
          .map((l) => l.trim())
          .filter(Boolean)
          .slice(0, 5)
      : ['কাজ সম্পন্ন হয়েছে।'],
    recommendations: ['বিস্তারিত ফলাফল যাচাই করে পরবর্তী পদক্ষেপ গ্রহণ করুন।'],
    limitations: execution.simulated
      ? ['এটি simulated মোডে সম্পন্ন হয়েছে।']
      : ['কাজটি sandbox নিয়মের মধ্যে সম্পন্ন হয়েছে।'],
  };
}
