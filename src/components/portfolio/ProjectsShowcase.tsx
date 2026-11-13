import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ArrowUpRight,
  BookOpen,
  ExternalLink,
  Github,
  Layers,
  Terminal,
} from 'lucide-react';
import { PortfolioCategory, PublicPortfolioProjectDTO } from '../../types';
import { fetchPublicProjectBySlug, fetchPublicProjects } from '../../lib/api/portfolio';
import { PortfolioMarkdown } from './PortfolioMarkdown';

interface ProjectsShowcaseProps {
  selectedSlug?: string;
  onNavigateHash: (hash: string) => void;
}

const CATEGORIES: { id: 'all' | PortfolioCategory; label: string }[] = [
  { id: 'all', label: 'All Work' },
  { id: 'ai_agent', label: 'AI Agents' },
  { id: 'rag', label: 'RAG Systems' },
  { id: 'llm_app', label: 'LLM Apps' },
  { id: 'mcp', label: 'MCP & Tools' },
  { id: 'automation', label: 'Automation' },
  { id: 'backend', label: 'Backend APIs' },
  { id: 'saas', label: 'AI SaaS' },
];

const STATUS_TEXT: Record<string, string> = {
  in_progress: 'In Progress',
  completed: 'Completed',
  archived: 'Archived',
};

export const ProjectsShowcase: React.FC<ProjectsShowcaseProps> = ({
  selectedSlug,
  onNavigateHash,
}) => {
  const [projects, setProjects] = useState<PublicPortfolioProjectDTO[]>([]);
  const [detailProject, setDetailProject] = useState<PublicPortfolioProjectDTO | null>(null);
  const [activeCategory, setActiveCategory] = useState<'all' | PortfolioCategory>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    if (selectedSlug) {
      fetchPublicProjectBySlug(selectedSlug)
        .then((proj) => {
          if (active) setDetailProject(proj);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    } else {
      fetchPublicProjects(activeCategory)
        .then((list) => {
          if (active) setProjects(list);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }
    return () => {
      active = false;
    };
  }, [selectedSlug, activeCategory]);

  if (selectedSlug) {
    if (loading) {
      return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-16">
          <div className="h-8 w-48 bg-[#0F172A] rounded animate-pulse mb-6" />
          <div className="h-64 bg-[#0F172A] border border-slate-800 rounded-lg animate-pulse" />
        </div>
      );
    }

    if (!detailProject) {
      return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-20">
          <button
            onClick={() => onNavigateHash('#portfolio/projects')}
            className="inline-flex items-center gap-2 text-xs font-mono text-[#00D4FF] hover:underline mb-8"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Projects</span>
          </button>
          <div className="p-8 bg-[#0F172A] border border-slate-800 rounded-lg">
            <h1 className="text-2xl font-bold font-display text-white mb-2">
              Project Not Found or Private
            </h1>
            <p className="text-sm text-slate-400">
              Only manually approved public projects are accessible on the portfolio surface.
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-14 space-y-10">
        <button
          onClick={() => onNavigateHash('#portfolio/projects')}
          className="inline-flex items-center gap-2 text-xs font-mono text-[#00D4FF] hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>All Public Projects</span>
        </button>

        {/* Project Header */}
        <header className="space-y-4 border-b border-slate-800/80 pb-8">
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-400">
            <span className="text-[#00D4FF] uppercase">{detailProject.category.replace('_', ' ')}</span>
            <span aria-hidden="true">·</span>
            <span>{STATUS_TEXT[detailProject.status] || detailProject.status}</span>
            {detailProject.is_featured && (
              <>
                <span aria-hidden="true">·</span>
                <span className="text-slate-200">Featured Build</span>
              </>
            )}
          </div>

          <h1 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
            {detailProject.title}
          </h1>
          <p className="text-base sm:text-lg text-slate-300 max-w-3xl">
            {detailProject.tagline}
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            {detailProject.github_url && (
              <a
                href={detailProject.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-mono font-medium bg-[#00D4FF] text-[#0A0F1E] rounded hover:bg-[#38BDF8] transition-colors whitespace-nowrap shrink-0"
              >
                <Github className="w-4 h-4" />
                <span>Inspect Repository</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </a>
            )}
            {detailProject.demo_url && (
              <button
                onClick={() => onNavigateHash(detailProject.demo_url || '#portfolio/demos')}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-mono font-medium text-slate-200 bg-[#0F172A] border border-slate-700 hover:border-[#00D4FF]/50 rounded transition-colors whitespace-nowrap shrink-0"
              >
                <Terminal className="w-3.5 h-3.5 text-[#00D4FF]" />
                <span>Try Safe Demo</span>
              </button>
            )}
            {detailProject.case_study_slug && (
              <button
                onClick={() => onNavigateHash(`#portfolio/case-studies/${detailProject.case_study_slug}`)}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-mono font-medium text-[#00D4FF] bg-[#0F172A] border border-[#00D4FF]/30 hover:bg-[#162036] rounded transition-colors whitespace-nowrap shrink-0"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Read Case Study</span>
              </button>
            )}
          </div>
        </header>

        {/* Tech Stack Breakdown (Zero-pill clean monospace list) */}
        <section className="space-y-3">
          <h2 className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Technology Stack Breakdown
          </h2>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm font-mono text-slate-200">
            {detailProject.tech_stack.map((tech, idx) => (
              <React.Fragment key={tech}>
                <span>{tech}</span>
                {idx < detailProject.tech_stack.length - 1 && (
                  <span className="text-slate-600" aria-hidden="true">
                    /
                  </span>
                )}
              </React.Fragment>
            ))}
          </div>
        </section>

        {/* Architecture Overview */}
        {detailProject.architecture_overview && (
          <section className="p-6 bg-[#0F172A] border border-slate-800 rounded-lg space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono text-[#00D4FF]">
              <Layers className="w-4 h-4" />
              <span>Architecture Overview</span>
            </div>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              {detailProject.architecture_overview}
            </p>
          </section>
        )}

        {/* Full Markdown Description */}
        <section className="pt-2">
          <PortfolioMarkdown markdown={detailProject.description} />
        </section>

        {/* Challenges & Engineering Solutions */}
        {detailProject.challenges_solutions && detailProject.challenges_solutions.length > 0 && (
          <section className="space-y-4 pt-6 border-t border-slate-800/80">
            <h2 className="text-xl font-bold font-display text-white">
              Engineering Challenges &amp; Solutions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {detailProject.challenges_solutions.map((pair, idx) => (
                <div key={idx} className="p-5 bg-[#0F172A] border border-slate-800 rounded-lg space-y-2">
                  <div className="text-xs font-mono text-slate-400">Challenge 0{idx + 1}</div>
                  <h3 className="text-sm font-semibold text-white">{pair.challenge}</h3>
                  <p className="text-sm text-slate-300 leading-relaxed pt-1">{pair.solution}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-10">
      <header className="space-y-3 max-w-2xl">
        <div className="text-xs font-mono text-[#00D4FF]">Public Portfolio Showcase</div>
        <h1 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
          Curated AI Systems &amp; Engineering Builds
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Manually approved public builds highlighting production agent architecture, hybrid retrieval, and backend reliability. Internal drafts remain private.
        </p>
      </header>

      {/* Interactive Category Filter Segmented Bar */}
      <div className="flex flex-wrap items-center gap-1.5 p-1.5 bg-[#0F172A] border border-slate-800 rounded-lg w-fit">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-3 py-1.5 text-xs font-mono rounded transition-colors whitespace-nowrap shrink-0 ${
              activeCategory === cat.id
                ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map((n) => (
            <div key={n} className="h-56 bg-[#0F172A] border border-slate-800 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="p-10 bg-[#0F172A] border border-slate-800 rounded-lg text-center space-y-2">
          <h2 className="text-lg font-semibold text-white font-display">
            No public projects in this category yet
          </h2>
          <p className="text-sm text-slate-400 max-w-lg mx-auto">
            Only manually reviewed and published projects appear here. Select another category or inspect interactive safe demos.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {projects.map((proj) => (
            <article
              key={proj.id}
              className="p-6 sm:p-7 bg-[#0F172A] border border-slate-800 hover:border-slate-700 rounded-lg flex flex-col justify-between gap-6 transition-colors"
            >
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                  <span className="text-[#00D4FF] uppercase">{proj.category.replace('_', ' ')}</span>
                  <span aria-hidden="true">·</span>
                  <span>{STATUS_TEXT[proj.status] || proj.status}</span>
                  {proj.is_featured && (
                    <>
                      <span aria-hidden="true">·</span>
                      <span className="text-slate-200">Featured</span>
                    </>
                  )}
                </div>

                <h2 className="text-xl font-bold font-display text-white">
                  <button
                    onClick={() => onNavigateHash(`#portfolio/projects/${proj.slug}`)}
                    className="text-left hover:text-[#00D4FF] transition-colors"
                  >
                    {proj.title}
                  </button>
                </h2>

                <p className="text-sm text-slate-300 leading-relaxed">{proj.tagline}</p>

                <div className="text-xs font-mono text-slate-400 pt-1">
                  {proj.tech_stack.join(' · ')}
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800/80 text-xs font-mono">
                <button
                  onClick={() => onNavigateHash(`#portfolio/projects/${proj.slug}`)}
                  className="text-[#00D4FF] hover:underline inline-flex items-center gap-1 whitespace-nowrap"
                >
                  <span>Architecture Details</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>

                <div className="flex items-center gap-4 text-slate-400">
                  {proj.github_url && (
                    <a
                      href={proj.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-white inline-flex items-center gap-1 whitespace-nowrap"
                    >
                      <Github className="w-3.5 h-3.5" />
                      <span>GitHub</span>
                    </a>
                  )}
                  {proj.demo_url && (
                    <button
                      onClick={() => onNavigateHash(proj.demo_url || '#portfolio/demos')}
                      className="hover:text-white inline-flex items-center gap-1 whitespace-nowrap"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Demo</span>
                    </button>
                  )}
                  {proj.case_study_slug && (
                    <button
                      onClick={() => onNavigateHash(`#portfolio/case-studies/${proj.case_study_slug}`)}
                      className="hover:text-[#00D4FF] inline-flex items-center gap-1 whitespace-nowrap"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>Case Study</span>
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};
