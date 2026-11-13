import React from 'react';
import { WorkbenchTab } from '../../types';
import { StatusBadge } from '../StatusBadge';
import { EmptyState } from '../EmptyState';
import { 
  INITIAL_AGENTS, 
  FEATURED_PROJECTS, 
  RAYHAN_PROFILE 
} from '../../data/workbenchData';
import { 
  Bot, 
  Layers, 
  FolderKanban, 
  Activity, 
  ArrowRight, 
  Github, 
  Terminal, 
  Clock, 
  ShieldCheck 
} from 'lucide-react';

interface DashboardViewProps {
  onTabChange: (tab: WorkbenchTab) => void;
  onSwitchToPortfolio: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onTabChange,
  onSwitchToPortfolio,
}) => {
  const featured = FEATURED_PROJECTS[0];

  return (
    <div className="space-y-8">
      {/* Workbench Welcome Banner */}
      <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-2">
            <span className="text-[#00D4FF]">RAYHAN AI WORKBENCH</span>
            <span aria-hidden="true">·</span>
            <span>PHASE 01 FOUNDATION</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold font-display text-white mb-2">
            AI Engineering Workspace
          </h2>
          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            Welcome to the internal engineering console for {RAYHAN_PROFILE.name}. 
            All agent registry cards, project shells, and design tokens are initialized for Phase 01.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <button
            onClick={() => onTabChange('agents')}
            className="px-4 py-2 text-xs font-mono font-medium text-[#0A0F1E] bg-[#00D4FF] hover:bg-[#38bdf8] rounded transition-colors flex items-center gap-2"
          >
            <Bot className="w-4 h-4" />
            <span>Open Agent Registry</span>
          </button>
          <button
            onClick={onSwitchToPortfolio}
            className="px-4 py-2 text-xs font-mono font-medium text-slate-300 hover:text-white bg-[#162036] hover:bg-slate-800 border border-slate-700 rounded transition-colors"
          >
            View Public Portfolio
          </button>
        </div>
      </div>

      {/* Honest Workspace Inventory Grid (No fake metrics) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-[#0F172A] border border-slate-800 rounded-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase">Agent Registry</span>
            <Bot className="w-4 h-4 text-[#00D4FF]" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">8</div>
          <div className="text-xs text-slate-500 font-mono mt-1">Status: All Planned</div>
        </div>

        <div className="p-4 bg-[#0F172A] border border-slate-800 rounded-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase">Flagship Prototype</span>
            <FolderKanban className="w-4 h-4 text-[#00D4FF]" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">1</div>
          <div className="text-xs text-slate-500 font-mono mt-1">Curizx AI Employee</div>
        </div>

        <div className="p-4 bg-[#0F172A] border border-slate-800 rounded-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase">Service Blueprints</span>
            <Layers className="w-4 h-4 text-[#00D4FF]" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">7</div>
          <div className="text-xs text-slate-500 font-mono mt-1">Ready for Delivery</div>
        </div>

        <div className="p-4 bg-[#0F172A] border border-slate-800 rounded-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase">Agent Runtime</span>
            <ShieldCheck className="w-4 h-4 text-[#00D4FF]" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">Phase 03</div>
          <div className="text-xs text-[#00D4FF] font-mono mt-1">Lifecycle + DB Active</div>
        </div>
      </div>

      {/* Featured Project Quick Access */}
      <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#00D4FF] font-semibold uppercase">
              Featured Flagship
            </span>
            <StatusBadge status={featured.status} />
          </div>
          {featured.githubUrl && (
            <a
              href={featured.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-white"
            >
              <Github className="w-3.5 h-3.5" />
              <span>GitHub Repository</span>
            </a>
          )}
        </div>

        <h3 className="text-xl font-bold text-white font-display mb-2">
          {featured.title}
        </h3>
        <p className="text-sm text-slate-300 mb-4 max-w-2xl">
          {featured.description}
        </p>

        <div className="flex flex-wrap items-center gap-2">
          {featured.techStack.map((tech) => (
            <span
              key={tech}
              className="text-xs font-mono px-2 py-0.5 bg-[#162036] text-slate-300 border border-slate-700/60 rounded"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>

      {/* Real Task Execution Quick Access */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white font-display flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#00D4FF]" />
            <span>Agent Execution Log</span>
          </h3>
          <button
            onClick={() => onTabChange('executions')}
            className="text-xs font-mono text-[#00D4FF] hover:underline flex items-center gap-1"
          >
            <span>View Full Execution History</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="p-6 bg-[#0F172A] border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-slate-300 font-semibold">Phase 03 Agent Runtime Active</span>
              <span>·</span>
              <span className="text-[#F59E0B]">Simulated = True</span>
            </div>
            <p className="text-xs text-slate-400 max-w-xl">
              All 8 agents support lifecycle state transitions, permission verification (READ_ONLY & SUGGEST scopes), background execution tasks, and persistent database tracking.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => onTabChange('agents')}
              className="px-3.5 py-1.5 text-xs font-mono bg-[#162036] hover:bg-slate-800 text-slate-200 border border-slate-700 rounded transition-colors"
            >
              Configure Agents
            </button>
            <button
              onClick={() => onTabChange('executions')}
              className="px-3.5 py-1.5 text-xs font-mono bg-[#00D4FF] hover:bg-[#38bdf8] text-[#0A0F1E] font-medium rounded transition-colors flex items-center gap-1.5"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Launch Execution</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
