import React from 'react';
import { FEATURED_PROJECTS } from '../../data/workbenchData';
import { StatusBadge } from '../StatusBadge';
import { EmptyState } from '../EmptyState';
import { 
  FolderKanban, 
  Github, 
  ExternalLink, 
  CheckCircle2, 
  PlusCircle, 
  Code2 
} from 'lucide-react';

export const ProjectsView: React.FC = () => {
  const featured = FEATURED_PROJECTS[0];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span className="text-[#00D4FF]">CODEBASE REPOSITORIES</span>
            <span aria-hidden="true">·</span>
            <span>AI SAAS & TOOLS</span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Projects & Repositories
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real source repositories and experimental prototypes engineered by Rayhan Badsha.
          </p>
        </div>
      </div>

      {/* Featured Prototype: Curizx AI Employee */}
      <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-6 sm:p-7">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2.5 mb-3">
              <span className="text-xs font-mono text-[#00D4FF] uppercase tracking-wider font-semibold">
                Featured Flagship
              </span>
              <span aria-hidden="true" className="text-slate-600">·</span>
              <StatusBadge status={featured.status} />
            </div>

            <h3 className="text-2xl font-bold font-display text-white mb-2">
              {featured.title}
            </h3>

            <p className="text-sm font-mono text-slate-400 mb-4">
              {featured.subtitle}
            </p>

            <p className="text-sm text-slate-300 mb-6 leading-relaxed">
              {featured.description}
            </p>

            {/* Architecture Highlights */}
            <div className="mb-6 space-y-2">
              <div className="text-xs font-mono uppercase text-slate-400">
                Key Architecture Attributes:
              </div>
              {featured.architectureHighlights.map((hl, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#00D4FF] shrink-0" />
                  <span>{hl}</span>
                </div>
              ))}
            </div>

            {/* Tech Stack */}
            <div className="flex flex-wrap items-center gap-1.5 mb-6">
              {featured.techStack.map((tech) => (
                <span
                  key={tech}
                  className="text-xs font-mono px-2.5 py-1 bg-[#162036] text-slate-300 border border-slate-700/60 rounded"
                >
                  {tech}
                </span>
              ))}
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3">
              {featured.githubUrl && (
                <a
                  href={featured.githubUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs font-mono font-medium text-[#0A0F1E] bg-[#00D4FF] hover:bg-[#38bdf8] rounded transition-colors"
                >
                  <Github className="w-4 h-4" />
                  <span>Inspect GitHub Repository</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>

          <div className="w-full md:w-80 bg-[#0A0F1E] border border-slate-800 rounded p-4 font-mono text-xs text-slate-400">
            <div className="text-slate-300 font-semibold mb-2 border-b border-slate-800 pb-2">
              Verification Metadata
            </div>
            <div className="space-y-2 text-[11px]">
              <div>
                <span className="text-slate-500 block">Repository:</span>
                <span className="text-slate-300 break-all">
                  github.com/rayhan-ai-architect/curizx-ai-employee
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">Role:</span>
                <span className="text-slate-300">Author & Systems Architect</span>
              </div>
              <div>
                <span className="text-slate-500 block">Status:</span>
                <span className="text-[#00D4FF]">Active Prototype</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Honest Empty State for Additional Projects */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-white font-display">
            Secondary Repositories
          </h3>
          <span className="text-xs font-mono text-slate-500">
            Honest State: Zero Inventions
          </span>
        </div>

        <EmptyState
          icon={FolderKanban}
          title="No Unverified Projects Listed"
          description="In alignment with Rayhan's engineering credibility standards, we do not invent fake client case studies, mock production statistics, or unverified repositories. Additional open-source projects will appear here as their codebases are released."
          phaseNote="Verified Evidence Only"
        />
      </div>
    </div>
  );
};
