export type AgentStatus = 
  | 'Planned' 
  | 'Configured' 
  | 'Available' 
  | 'Running' 
  | 'Completed' 
  | 'Failed' 
  | 'Maintenance' 
  | 'Prototype' 
  | 'In Development' 
  | 'Active';

export type AgentCategory = 
  | 'Autonomous Agents'
  | 'RAG & Retrieval'
  | 'Tooling & MCP'
  | 'Workflow Automation'
  | 'Engineering & Evaluation';

export interface Agent {
  id: string;
  name: string;
  codename: string;
  category: AgentCategory;
  role: string;
  architecture: string;
  targetModel: string;
  tools: string[];
  status: AgentStatus;
  description: string;
  repoUrl?: string;
  bengaliName?: string;
  bengaliTask?: string;
  whenToUseBn?: string[];
  quickPromptsBn?: string[];
  targetPathDefault?: string;
  supportsImplement?: boolean;
}

export interface Project {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  status: AgentStatus;
  githubUrl?: string;
  architectureHighlights: string[];
  techStack: string[];
  featured?: boolean;
}

export interface NavItem {
  id: string;
  label: string;
  iconName: string;
  badge?: string;
}

export interface ServiceItem {
  id: string;
  number: string;
  title: string;
  problem: string;
  deliverables: string[];
  approach: string;
  ctaText: string;
}

export type ViewMode = 'portfolio' | 'workbench';

export type WorkbenchTab = 
  | 'dashboard'
  | 'agents'
  | 'executions'
  | 'security'
  | 'testing'
  | 'gateway'
  | 'architecture'
  | 'documentation'
  | 'projects'
  | 'knowledge'
  | 'integrations'
  | 'devops'
  | 'content-studio'
  | 'settings';


export type ExecutionStatusType = 'Pending' | 'Running' | 'Completed' | 'Failed' | 'Cancelled';

export interface ExecutionItem {
  id: string;
  agent_slug: string;
  task_id: string;
  user_id: string;
  status: ExecutionStatusType;
  scope: 'read_only' | 'suggest' | 'implement';
  instruction: string;
  output?: string | null;
  error_message?: string | null;
  simulated: boolean;
  tokens_used?: number | null;
  duration_ms?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  bn_report?: BengaliReport | null;
}

export interface BengaliReport {
  language: 'bn';
  agent_slug: string;
  agent_name_bn: string;
  summary_bn: string;
  what_agent_did: string;
  findings: string[];
  recommendations: string[];
  limitations: string[];
}

export type PortfolioSection =
  | 'home'
  | 'projects'
  | 'project-detail'
  | 'case-studies'
  | 'case-study-detail'
  | 'articles'
  | 'article-detail'
  | 'demos'
  | 'demo-detail'
  | 'contact';

export interface PublicProfileDTO {
  name: string;
  title: string;
  tagline: string;
  bio: string;
  location: string;
  collaboration_status: string;
  expertise: string[];
  tech_badges: string[];
  social_links: {
    github: string;
    linkedin: string;
    youtube: string;
  };
}

export type PortfolioCategory =
  | 'ai_agent'
  | 'rag'
  | 'llm_app'
  | 'automation'
  | 'backend'
  | 'mcp'
  | 'saas';

export interface PublicPortfolioProjectDTO {
  id: string;
  slug: string;
  title: string;
  tagline: string;
  description: string;
  architecture_overview: string;
  challenges_solutions: { challenge: string; solution: string }[];
  tech_stack: string[];
  category: PortfolioCategory;
  status: 'in_progress' | 'completed' | 'archived';
  github_url?: string | null;
  demo_url?: string | null;
  case_study_slug?: string | null;
  is_featured: boolean;
  is_public: boolean;
  sort_order: number;
  published_at?: string | null;
}

export interface PublicCaseStudyDTO {
  slug: string;
  title: string;
  summary: string;
  body_markdown: string;
  benchmark_flags: string[];
  reading_time_min: number;
  published_at?: string | null;
}

export interface PublicArticleDTO {
  slug: string;
  title: string;
  content_type: 'article' | 'tutorial';
  summary: string;
  body_markdown: string;
  reading_time_min: number;
  word_count: number;
  published_at?: string | null;
}

export interface SafeDemoDefinitionDTO {
  slug: 'code-analyzer' | 'security-scanner' | 'architecture-diagram';
  title: string;
  description: string;
  demo_label: string;
  read_only: boolean;
  rate_limit: string;
  timeout_seconds: number;
  persisted: boolean;
  samples: {
    label: string;
    language: 'python' | 'typescript';
    input_code: string;
  }[];
}

export interface SafeDemoRunResponseDTO {
  slug: string;
  demo_label: string;
  sample_data_only: boolean;
  persisted: boolean;
  execution_ms: number;
  output: Record<string, any>;
}
