import React from 'react';
import { WorkbenchTab } from '../../types';
import { 
  LayoutDashboard, 
  Bot, 
  PlayCircle,
  ShieldCheck,
  FolderKanban, 
  Database, 
  Blocks, 
  Tv, 
  Settings, 
  ChevronRight,
  ShieldAlert,
  TestTube,
  Cpu,
  Network,
  BookOpen,
  GitBranch,
} from 'lucide-react';

interface SidebarProps {
  activeTab: WorkbenchTab;
  onTabChange: (tab: WorkbenchTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const navItems: { id: WorkbenchTab; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'agents', label: 'Agent Registry', icon: Bot, badge: '9 Agents' },
    { id: 'executions', label: 'Task Executions', icon: PlayCircle },
    { id: 'gateway', label: 'AI Gateway', icon: Cpu },
    { id: 'architecture', label: 'Architecture Agent', icon: Network, badge: 'Phase 09' },
    { id: 'documentation', label: 'Documentation Agent', icon: BookOpen, badge: 'Phase 09' },
    { id: 'security', label: 'Security Agent', icon: ShieldCheck, badge: 'Phase 05' },
    { id: 'testing', label: 'Testing & QA', icon: TestTube, badge: 'Phase 06' },
    { id: 'projects', label: 'Projects & Repos', icon: FolderKanban, badge: '1 Proto' },
    { id: 'knowledge', label: 'Knowledge & RAG', icon: Database, badge: 'Phase 10' },
    { id: 'integrations', label: 'Integrations & MCP', icon: Blocks, badge: '18 Tools' },
    { id: 'devops', label: 'DevOps & Releases', icon: GitBranch, badge: 'Phase 11' },
    { id: 'content-studio', label: 'Content Studio', icon: Tv, badge: 'Phase 12' },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];


  return (
    <aside className="w-64 bg-[#0A0F1E] border-r border-slate-800/80 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      {/* Workbench Header Banner */}
      <div className="p-4 border-b border-slate-800/60">
        <div className="text-xs font-mono uppercase tracking-wider text-slate-500 mb-1">
          Internal Workspace
        </div>
        <div className="text-sm font-semibold text-slate-100 font-display flex items-center justify-between">
          <span>AI Architecture Lab</span>
          <span className="text-[11px] font-mono text-[#00D4FF] bg-[#00D4FF]/10 px-1.5 py-0.5 rounded border border-[#00D4FF]/20">
            Phase 01
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="p-3 space-y-1 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded transition-colors group ${
                isActive
                  ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-[#0F172A]'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#00D4FF]' : 'text-slate-500 group-hover:text-slate-300'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge ? (
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                    isActive
                      ? 'bg-[#00D4FF]/20 text-[#00D4FF]'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {item.badge}
                </span>
              ) : (
                isActive && <ChevronRight className="w-3 h-3 text-[#00D4FF]" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Honest Phase Status Info Box */}
      <div className="p-4 m-3 bg-[#0F172A] border border-slate-800/80 rounded text-xs font-mono text-slate-400">
        <div className="flex items-center gap-1.5 text-slate-300 font-semibold mb-1">
          <ShieldAlert className="w-3.5 h-3.5 text-[#00D4FF]" />
          <span>Integrity Constraint</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-normal">
          Phase 03 Agent Runtime: Base contracts, permission validation, and execution logging active. Simulated = True (no LLM calls until Phase 07).
        </p>
      </div>
    </aside>
  );
};
