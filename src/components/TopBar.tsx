import React from 'react';
import { PortfolioSection, ViewMode, WorkbenchTab } from '../types';
import { Terminal, Globe, Github } from 'lucide-react';
import { RAYHAN_PROFILE } from '../data/workbenchData';

interface TopBarProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  portfolioSection: PortfolioSection;
  onNavigatePortfolioHash: (hash: string) => void;
  activeWorkbenchTab: WorkbenchTab;
  onWorkbenchTabChange: (tab: WorkbenchTab) => void;
}

const PORTFOLIO_LINKS: { label: string; hash: string; matches: PortfolioSection[] }[] = [
  { label: 'Projects', hash: '#portfolio/projects', matches: ['projects', 'project-detail'] },
  { label: 'Case Studies', hash: '#portfolio/case-studies', matches: ['case-studies', 'case-study-detail'] },
  { label: 'Articles', hash: '#portfolio/articles', matches: ['articles', 'article-detail'] },
  { label: 'Safe Demos', hash: '#portfolio/demos', matches: ['demos', 'demo-detail'] },
  { label: 'Contact', hash: '#portfolio/contact', matches: ['contact'] },
];

export const TopBar: React.FC<TopBarProps> = ({
  viewMode,
  onViewModeChange,
  portfolioSection,
  onNavigatePortfolioHash,
  activeWorkbenchTab,
  onWorkbenchTabChange,
}) => {
  return (
    <header className="sticky top-0 z-50 w-full bg-[#0A0F1E]/95 backdrop-blur-md border-b border-slate-800/80 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4 sm:gap-8">
        {/* Zone 1: Brand Wordmark */}
        <div className="flex items-center shrink-0">
          <button
            onClick={() => onNavigatePortfolioHash('#portfolio')}
            className="flex items-center gap-2.5 text-left group focus-visible:outline-none whitespace-nowrap shrink-0"
          >
            <div className="w-8 h-8 rounded bg-[#162036] border border-[#00D4FF]/30 flex items-center justify-center text-[#00D4FF] group-hover:border-[#00D4FF] transition-colors">
              <Terminal className="w-4 h-4" />
            </div>
            <span className="text-base font-bold tracking-tight text-slate-100 group-hover:text-white font-display whitespace-nowrap">
              {RAYHAN_PROFILE.brand}
            </span>
          </button>
        </div>

        {/* Zone 2: Clean Single-Line Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
          {viewMode === 'portfolio' ? (
            <>
              {PORTFOLIO_LINKS.map((link) => {
                const isActive = link.matches.includes(portfolioSection);
                return (
                  <button
                    key={link.hash}
                    onClick={() => onNavigatePortfolioHash(link.hash)}
                    className={`transition-colors whitespace-nowrap shrink-0 pb-0.5 border-b ${
                      isActive
                        ? 'text-[#00D4FF] border-[#00D4FF]'
                        : 'border-transparent hover:text-slate-100'
                    }`}
                  >
                    {link.label}
                  </button>
                );
              })}
            </>
          ) : (
            <div className="flex items-center gap-1 bg-[#0F172A] p-1 rounded-md border border-slate-800">
              <button
                onClick={() => onWorkbenchTabChange('dashboard')}
                className={`px-3 py-1 text-xs font-mono transition-colors rounded whitespace-nowrap ${
                  activeWorkbenchTab === 'dashboard'
                    ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => onWorkbenchTabChange('agents')}
                className={`px-3 py-1 text-xs font-mono transition-colors rounded whitespace-nowrap ${
                  activeWorkbenchTab === 'agents'
                    ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Agent Registry
              </button>
              <button
                onClick={() => onWorkbenchTabChange('executions')}
                className={`px-3 py-1 text-xs font-mono transition-colors rounded whitespace-nowrap ${
                  activeWorkbenchTab === 'executions'
                    ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Executions
              </button>
              <button
                onClick={() => onWorkbenchTabChange('gateway')}
                className={`px-3 py-1 text-xs font-mono transition-colors rounded whitespace-nowrap ${
                  activeWorkbenchTab === 'gateway'
                    ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                AI Gateway
              </button>
              <button
                onClick={() => onWorkbenchTabChange('security')}
                className={`px-3 py-1 text-xs font-mono transition-colors rounded whitespace-nowrap ${
                  activeWorkbenchTab === 'security'
                    ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Security
              </button>
              <button
                onClick={() => onWorkbenchTabChange('testing')}
                className={`px-3 py-1 text-xs font-mono transition-colors rounded whitespace-nowrap ${
                  activeWorkbenchTab === 'testing'
                    ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Testing
              </button>
              <button
                onClick={() => onWorkbenchTabChange('projects')}
                className={`px-3 py-1 text-xs font-mono transition-colors rounded whitespace-nowrap ${
                  activeWorkbenchTab === 'projects'
                    ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Projects
              </button>
            </div>
          )}
        </nav>

        {/* Zone 3: Surface Switcher & GitHub */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center bg-[#0F172A] border border-slate-800 p-0.5 rounded">
            <button
              onClick={() => onViewModeChange('portfolio')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors whitespace-nowrap shrink-0 ${
                viewMode === 'portfolio'
                  ? 'bg-[#162036] text-[#00D4FF] shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Public Portfolio View"
            >
              <Globe className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Portfolio</span>
            </button>
            <button
              onClick={() => onViewModeChange('workbench')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded transition-colors whitespace-nowrap shrink-0 ${
                viewMode === 'workbench'
                  ? 'bg-[#162036] text-[#00D4FF] shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="AI Engineering Workbench View"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Workbench</span>
            </button>
          </div>

          <a
            href={RAYHAN_PROFILE.githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 text-slate-400 hover:text-white bg-[#0F172A] hover:bg-[#162036] border border-slate-800 rounded transition-colors shrink-0"
            title="Rayhan GitHub"
          >
            <Github className="w-4 h-4" />
          </a>
        </div>
      </div>
    </header>
  );
};
