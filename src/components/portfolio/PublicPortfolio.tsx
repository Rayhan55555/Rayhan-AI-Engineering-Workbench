import React, { useEffect, useState } from 'react';
import {
  ArrowRight,
  ArrowUpRight,
  Blocks,
  Bot,
  Cpu,
  Database,
  FileText,
  Github,
  Layers,
  Linkedin,
  Mail,
  Server,
  Terminal,
  Youtube,
} from 'lucide-react';
import {
  PortfolioSection,
  PublicArticleDTO,
  PublicPortfolioProjectDTO,
  PublicProfileDTO,
} from '../../types';
import {
  FALLBACK_PROFILE,
  fetchPublicArticles,
  fetchPublicProfile,
  fetchPublicProjects,
} from '../../lib/api/portfolio';
import { ProjectsShowcase } from './ProjectsShowcase';
import { ArticlesView, CaseStudiesView } from './CaseStudiesAndArticles';
import { SafeDemosView } from './SafeDemosView';
import { ContactView } from './ContactView';

interface PublicPortfolioProps {
  section: PortfolioSection;
  slug?: string;
  onNavigateHash: (hash: string) => void;
  onSwitchToWorkbench: () => void;
}

const EXPERTISE_AREAS = [
  {
    icon: Layers,
    title: 'AI Systems Architecture',
    description:
      'State-machine boundaries, multi-service data isolation, and failure recovery around nondeterministic models.',
  },
  {
    icon: Cpu,
    title: 'Applied AI Engineering',
    description:
      'Structured schema validation, deterministic evaluation harnesses, and multi-provider gateway routing.',
  },
  {
    icon: Database,
    title: 'LLM & RAG Applications',
    description:
      'Hybrid pgvector cosine retrieval, cross-scoring reranking, and strict citation verification pipelines.',
  },
  {
    icon: Bot,
    title: 'AI Agents & Automation',
    description:
      'Scope-gated ReAct agent runtimes with read-only inspection, suggestion diffs, and human approval checkpoints.',
  },
  {
    icon: Blocks,
    title: 'MCP & Tool Integration',
    description:
      'Sandboxed Model Context Protocol tools with path-traversal guards, timeouts, and immutable audit logs.',
  },
  {
    icon: Server,
    title: 'Backend APIs & Databases',
    description:
      'Async FastAPI services, PostgreSQL schema engineering, sliding-window rate limits, and clean REST contracts.',
  },
];

export const PublicPortfolio: React.FC<PublicPortfolioProps> = ({
  section,
  slug,
  onNavigateHash,
  onSwitchToWorkbench,
}) => {
  const [profile, setProfile] = useState<PublicProfileDTO>(FALLBACK_PROFILE);
  const [featuredProjects, setFeaturedProjects] = useState<PublicPortfolioProjectDTO[]>([]);
  const [recentArticles, setRecentArticles] = useState<PublicArticleDTO[]>([]);

  useEffect(() => {
    let active = true;
    fetchPublicProfile().then((p) => {
      if (active) setProfile(p);
    });
    fetchPublicProjects().then((list) => {
      if (active) {
        const featured = list.filter((p) => p.is_featured);
        setFeaturedProjects((featured.length > 0 ? featured : list).slice(0, 3));
      }
    });
    fetchPublicArticles().then((arts) => {
      if (active) setRecentArticles(arts.slice(0, 3));
    });
    return () => {
      active = false;
    };
  }, []);

  const renderSection = () => {
    if (section === 'projects' || section === 'project-detail') {
      return <ProjectsShowcase selectedSlug={slug} onNavigateHash={onNavigateHash} />;
    }
    if (section === 'case-studies' || section === 'case-study-detail') {
      return <CaseStudiesView selectedSlug={slug} onNavigateHash={onNavigateHash} />;
    }
    if (section === 'articles' || section === 'article-detail') {
      return <ArticlesView selectedSlug={slug} onNavigateHash={onNavigateHash} />;
    }
    if (section === 'demos' || section === 'demo-detail') {
      return <SafeDemosView selectedSlug={slug} onNavigateHash={onNavigateHash} />;
    }
    if (section === 'contact') {
      return <ContactView profile={profile} />;
    }

    // Default: Public Home Page (Step 13.3)
    return (
      <>
        {/* 1. HERO SECTION */}
        <section className="relative pt-16 pb-20 sm:pt-24 sm:pb-24 border-b border-slate-800/60 overflow-hidden">
          <div
            className="absolute inset-0 opacity-[0.03] pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(#00D4FF 1px, transparent 1px)',
              backgroundSize: '32px 32px',
            }}
            aria-hidden="true"
          />

          <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10 space-y-8">
            <div className="max-w-3xl space-y-6">
              <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-400">
                <span className="text-[#00D4FF]">{profile.name}</span>
                <span aria-hidden="true">·</span>
                <span>{profile.title}</span>
                <span aria-hidden="true">·</span>
                <span>Open to collaborations</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold font-display tracking-tight text-white leading-[1.08] [text-wrap:balance]">
                {profile.tagline}
              </h1>

              <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl">
                {profile.bio}
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button
                  onClick={() => onNavigateHash('#portfolio/projects')}
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-mono font-semibold bg-[#00D4FF] text-[#0A0F1E] hover:bg-[#38BDF8] rounded transition-colors whitespace-nowrap shrink-0"
                >
                  <span>View Work</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
                <button
                  onClick={onSwitchToWorkbench}
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-mono font-medium text-slate-200 hover:text-white bg-[#0F172A] hover:bg-[#162036] border border-slate-700 hover:border-[#00D4FF]/40 rounded transition-colors whitespace-nowrap shrink-0"
                >
                  <Terminal className="w-4 h-4 text-[#00D4FF]" />
                  <span>Open Workbench</span>
                </button>
              </div>
            </div>

            {/* Honest Stack & Verified Links Strip (No Fake Metrics) */}
            <div className="pt-8 border-t border-slate-800/80 flex flex-col lg:flex-row lg:items-center justify-between gap-4 text-xs font-mono text-slate-400">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="text-slate-500">Core Stack:</span>
                {profile.tech_badges.map((tech, idx) => (
                  <React.Fragment key={tech}>
                    <span className="text-slate-300">{tech}</span>
                    {idx < profile.tech_badges.length - 1 && (
                      <span className="text-slate-700" aria-hidden="true">
                        /
                      </span>
                    )}
                  </React.Fragment>
                ))}
              </div>

              <div className="flex flex-wrap items-center gap-5 shrink-0">
                <a
                  href={profile.social_links.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 hover:text-[#00D4FF] transition-colors whitespace-nowrap"
                >
                  <Github className="w-4 h-4" />
                  <span>GitHub</span>
                </a>
                <a
                  href={profile.social_links.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 hover:text-[#00D4FF] transition-colors whitespace-nowrap"
                >
                  <Linkedin className="w-4 h-4" />
                  <span>LinkedIn</span>
                </a>
                <a
                  href={profile.social_links.youtube}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 hover:text-[#00D4FF] transition-colors whitespace-nowrap"
                >
                  <Youtube className="w-4 h-4 text-rose-400" />
                  <span>YouTube</span>
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* 2. EXPERTISE SECTION (6 Areas) */}
        <section className="py-20 border-b border-slate-800/60 bg-[#0A0F1E]">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 space-y-10">
            <div className="max-w-2xl space-y-2">
              <div className="text-xs font-mono text-[#00D4FF]">Core Capabilities</div>
              <h2 className="text-3xl font-bold font-display text-white">
                Engineering Expertise
              </h2>
              <p className="text-sm sm:text-base text-slate-400">
                Focused technical disciplines across deterministic AI architectures, retrieval engineering, and production backend infrastructure.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {EXPERTISE_AREAS.map((area) => {
                const Icon = area.icon;
                return (
                  <div
                    key={area.title}
                    className="p-6 bg-[#0F172A] border border-slate-800 rounded-lg space-y-3"
                  >
                    <div className="w-9 h-9 rounded bg-[#162036] border border-slate-700/60 flex items-center justify-center text-[#00D4FF]">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h3 className="text-lg font-semibold font-display text-white">
                      {area.title}
                    </h3>
                    <p className="text-sm text-slate-400 leading-relaxed">{area.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* 3. FEATURED PROJECTS (Max 3) */}
        <section className="py-20 border-b border-slate-800/60 bg-[#0A0F1E]">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 space-y-10">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div className="space-y-2">
                <div className="text-xs font-mono text-[#00D4FF]">Selected Systems</div>
                <h2 className="text-3xl font-bold font-display text-white">
                  Featured Engineering Projects
                </h2>
              </div>
              <button
                onClick={() => onNavigateHash('#portfolio/projects')}
                className="text-xs font-mono text-[#00D4FF] hover:underline inline-flex items-center gap-1 whitespace-nowrap"
              >
                <span>Browse All Public Projects</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {featuredProjects.map((proj) => (
                <article
                  key={proj.id}
                  className="p-6 bg-[#0F172A] border border-slate-800 hover:border-slate-700 rounded-lg flex flex-col justify-between gap-5"
                >
                  <div className="space-y-2.5">
                    <div className="text-xs font-mono text-slate-400">
                      <span className="text-[#00D4FF] uppercase">
                        {proj.category.replace('_', ' ')}
                      </span>{' '}
                      · {proj.status === 'in_progress' ? 'In Progress' : proj.status}
                    </div>
                    <h3 className="text-xl font-bold font-display text-white">{proj.title}</h3>
                    <p className="text-sm text-slate-300 leading-relaxed">{proj.tagline}</p>
                    <div className="text-xs font-mono text-slate-500 pt-1">
                      {proj.tech_stack.slice(0, 5).join(' · ')}
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-3 pt-4 border-t border-slate-800/80 text-xs font-mono">
                    <button
                      onClick={() => onNavigateHash(`#portfolio/projects/${proj.slug}`)}
                      className="text-[#00D4FF] hover:underline inline-flex items-center gap-1"
                    >
                      <span>View Project</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                    {proj.github_url && (
                      <a
                        href={proj.github_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-400 hover:text-white inline-flex items-center gap-1"
                      >
                        <Github className="w-3.5 h-3.5" />
                        <span>Code</span>
                      </a>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* 4. SAFE INTERACTIVE DEMOS + RECENT PUBLISHED CONTENT */}
        <section className="py-20 border-b border-slate-800/60 bg-[#0A0F1E]">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 space-y-12">
            {/* Safe Demos Highlight */}
            <div className="p-6 sm:p-8 bg-[#0F172A] border border-slate-800 rounded-lg flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div className="space-y-2 max-w-2xl">
                <div className="text-xs font-mono text-[#00D4FF]">Demo — Sample Data Sandbox</div>
                <h2 className="text-2xl font-bold font-display text-white">
                  Try Safe Isolated Engineering Demos
                </h2>
                <p className="text-sm text-slate-300">
                  Test read-only Code AST Analysis, Security Vulnerability Scanning, and Mermaid Architecture Diagram generation with sample inputs — zero login or persistent storage.
                </p>
              </div>
              <button
                onClick={() => onNavigateHash('#portfolio/demos')}
                className="px-5 py-2.5 text-xs font-mono font-semibold text-[#0A0F1E] bg-[#00D4FF] hover:bg-[#38BDF8] rounded transition-colors inline-flex items-center gap-2 whitespace-nowrap shrink-0"
              >
                <Terminal className="w-4 h-4" />
                <span>Launch Safe Demos</span>
              </button>
            </div>

            {/* Recent Published Content (Strict Phase 12 Published Only) */}
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="text-xs font-mono text-[#00D4FF]">From Content Studio</div>
                  <h2 className="text-2xl sm:text-3xl font-bold font-display text-white">
                    Recent Published Writing
                  </h2>
                </div>
                <div className="flex items-center gap-5 text-xs font-mono">
                  <button
                    onClick={() => onNavigateHash('#portfolio/case-studies')}
                    className="text-slate-300 hover:text-[#00D4FF]"
                  >
                    Case Studies →
                  </button>
                  <button
                    onClick={() => onNavigateHash('#portfolio/articles')}
                    className="text-[#00D4FF] hover:underline"
                  >
                    All Articles →
                  </button>
                </div>
              </div>

              {recentArticles.length === 0 ? (
                <div className="p-6 bg-[#0F172A] border border-slate-800 rounded-lg flex items-center gap-3 text-sm text-slate-400">
                  <FileText className="w-5 h-5 text-slate-500 shrink-0" />
                  <span>
                    No published articles yet — items appear publicly only after explicit approval and publication in Content Studio.
                  </span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {recentArticles.map((art) => (
                    <article
                      key={art.slug}
                      className="p-6 bg-[#0F172A] border border-slate-800 rounded-lg flex flex-col justify-between gap-4"
                    >
                      <div className="space-y-2">
                        <div className="text-xs font-mono text-slate-400 tabular-nums">
                          <span className="text-[#00D4FF] capitalize">{art.content_type}</span> ·{' '}
                          {art.reading_time_min} min read
                        </div>
                        <h3 className="text-lg font-bold font-display text-white">{art.title}</h3>
                        <p className="text-sm text-slate-400 leading-relaxed">{art.summary}</p>
                      </div>
                      <button
                        onClick={() => onNavigateHash(`#portfolio/articles/${art.slug}`)}
                        className="text-xs font-mono text-[#00D4FF] hover:underline inline-flex items-center gap-1 w-fit"
                      >
                        <span>Read Article</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* 5. HONEST CONTACT CTA */}
        <section className="py-20 bg-[#0A0F1E]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6">
            <h2 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
              Let&apos;s work together
            </h2>
            <p className="text-slate-300 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              {profile.collaboration_status}. Reach out to discuss AI systems engineering roles, retrieval architecture, or technical advisory.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
              <button
                onClick={() => onNavigateHash('#portfolio/contact')}
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-mono font-semibold bg-[#00D4FF] text-[#0A0F1E] hover:bg-[#38BDF8] rounded transition-colors whitespace-nowrap shrink-0"
              >
                <Mail className="w-4 h-4" />
                <span>Open Contact Page</span>
              </button>
              <button
                onClick={() => onNavigateHash('#portfolio/demos')}
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-mono font-medium text-slate-200 bg-[#0F172A] border border-slate-700 hover:border-[#00D4FF]/40 rounded transition-colors whitespace-nowrap shrink-0"
              >
                <span>Explore Safe Demos</span>
              </button>
            </div>
          </div>
        </section>
      </>
    );
  };

  return (
    <div className="min-h-screen bg-[#0A0F1E] text-slate-100 flex flex-col">
      <div className="flex-1">{renderSection()}</div>

      {/* Quiet Footer */}
      <footer className="border-t border-slate-800/80 py-8 bg-[#0A0F1E]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between text-xs font-mono text-slate-500 gap-4">
          <div>
            © 2026 {profile.name} · Applied AI Systems Architecture
          </div>
          <div className="flex flex-wrap items-center gap-5">
            <button onClick={() => onNavigateHash('#portfolio/projects')} className="hover:text-slate-300">
              Projects
            </button>
            <button onClick={() => onNavigateHash('#portfolio/case-studies')} className="hover:text-slate-300">
              Case Studies
            </button>
            <button onClick={() => onNavigateHash('#portfolio/articles')} className="hover:text-slate-300">
              Articles
            </button>
            <button onClick={() => onNavigateHash('#portfolio/demos')} className="hover:text-slate-300">
              Safe Demos
            </button>
            <button onClick={() => onNavigateHash('#portfolio/contact')} className="hover:text-slate-300">
              Contact
            </button>
            <button onClick={onSwitchToWorkbench} className="text-[#00D4FF] hover:underline">
              Workbench
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
