import React, { useState, useMemo, useEffect } from 'react';
import { INITIAL_AGENTS } from '../../data/workbenchData';
import { StatusBadge } from '../StatusBadge';
import { AgentCategory, Agent } from '../../types';
import { getAgents, BackendAgent } from '../../lib/api/agents';
import { AgentTaskModal } from './AgentTaskModal';
import { 
  Bot, 
  Search, 
  Cpu, 
  Wrench, 
  Layers, 
  Github, 
  ShieldAlert, 
  ExternalLink,
  Server,
  Play,
  Lock,
  Sparkles,
  CheckCircle2
} from 'lucide-react';

export const AgentRegistryView: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);
  const [dataSource, setDataSource] = useState<'Phase 01 Spec' | 'Live REST API (/api/v1/agents)'>('Phase 01 Spec');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedAgentForTask, setSelectedAgentForTask] = useState<Agent | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadBackendAgents() {
      try {
        const res = await getAgents();
        if (isMounted && res.data && res.data.length > 0) {
          const mapped: Agent[] = res.data.map((b: BackendAgent) => {
            const match = INITIAL_AGENTS.find((a) => a.codename === b.slug || a.id === b.slug);
            return {
              id: b.id,
              name: b.name,
              codename: b.slug,
              category: match ? match.category : 'Autonomous Agents',
              role: match ? match.role : b.purpose,
              architecture: match ? match.architecture : 'FastAPI Registered Specification',
              targetModel: match ? match.targetModel : 'Production LLM Gateway',
              tools: b.allowed_tools || [],
              status: b.status as any,
              description: b.purpose,
              repoUrl: match?.repoUrl,
            };
          });
          setAgents(mapped);
          setDataSource('Live REST API (/api/v1/agents)');
        }
      } catch {
        // Keep initial spec peacefully
      }
    }
    loadBackendAgents();
    return () => {
      isMounted = false;
    };
  }, []);

  const categories: string[] = [
    'All',
    'Autonomous Agents',
    'RAG & Retrieval',
    'Tooling & MCP',
    'Workflow Automation',
    'Engineering & Evaluation',
  ];

  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      const matchesCategory =
        selectedCategory === 'All' || agent.category === selectedCategory;
      const matchesSearch =
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.codename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.targetModel.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [agents, searchQuery, selectedCategory]);

  const toggleAgentAvailability = (slug: string) => {
    // Local dev helper to test lifecycle transitions Planned -> Configured -> Available
    setAgents((prev) =>
      prev.map((a) => {
        if (a.codename === slug || a.id === slug) {
          const nextStatus = a.status === 'Available' ? 'Planned' : 'Available';
          return { ...a, status: nextStatus };
        }
        return a;
      })
    );
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span className="text-[#00D4FF]">AGENT DIRECTORY</span>
            <span aria-hidden="true">·</span>
            <span>SPECIFICATION ARCHITECTURE</span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Agent Registry
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            8 autonomous systems and orchestration agents designed for practical production deployment.
          </p>
        </div>

        {/* Status reminder and Data Source note */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0F172A] border border-slate-800 rounded text-xs font-mono text-slate-400">
            <Server className="w-3.5 h-3.5 text-[#00D4FF]" />
            <span>{dataSource}</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0F172A] border border-slate-800 rounded text-xs font-mono text-slate-400">
            <ShieldAlert className="w-3.5 h-3.5 text-[#00D4FF]" />
            <span>Phase 03 Runtime Contract</span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        {/* Category Tabs */}
        <div className="flex flex-wrap items-center gap-1 p-1 bg-[#0F172A] border border-slate-800 rounded-md">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 text-xs font-mono rounded transition-colors whitespace-nowrap ${
                selectedCategory === cat
                  ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search input */}
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter agents by name or tool..."
            className="w-full bg-[#0F172A] border border-slate-800 text-xs text-slate-200 pl-9 pr-3 py-2 rounded focus:outline-none focus:border-[#00D4FF] focus:ring-1 focus:ring-[#00D4FF] font-mono placeholder:text-slate-600"
          />
        </div>
      </div>

      {/* 8 Agent Cards Grid */}
      {filteredAgents.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {filteredAgents.map((agent) => {
            const isAvailable = agent.status === 'Available';
            return (
              <div
                key={agent.id}
                className="bg-[#0F172A] border border-slate-800 hover:border-slate-700/80 rounded-lg p-5 flex flex-col justify-between transition-colors relative"
              >
                <div>
                  {/* Card Header: Category & Real Status */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                      <span className="text-[#00D4FF] font-semibold">{agent.category}</span>
                      <span aria-hidden="true">·</span>
                      <span className="text-slate-500">[{agent.codename}]</span>
                    </div>
                    {/* Real status badge */}
                    <StatusBadge status={agent.status} />
                  </div>

                  {/* Agent Title & Role */}
                  <h3 className="text-lg font-bold text-white font-display mb-1 flex items-center justify-between">
                    <span>{agent.name}</span>
                    {agent.repoUrl && (
                      <a
                        href={agent.repoUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs font-mono text-slate-400 hover:text-[#00D4FF] flex items-center gap-1"
                        title="Inspect GitHub Repository"
                      >
                        <Github className="w-3.5 h-3.5" />
                        <span>Code</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </h3>

                  <p className="text-xs font-mono text-slate-400 mb-3">
                    {agent.role}
                  </p>

                  <p className="text-xs sm:text-sm text-slate-300 mb-4 leading-relaxed">
                    {agent.description}
                  </p>

                  {/* Architecture & Target Model */}
                  <div className="space-y-2 mb-4 p-3 bg-[#0A0F1E] border border-slate-800/80 rounded text-xs font-mono">
                    <div className="flex items-start gap-2">
                      <Layers className="w-3.5 h-3.5 text-[#00D4FF] shrink-0 mt-0.5" />
                      <div>
                        <span className="text-slate-400 block text-[11px] uppercase">
                          Architecture:
                        </span>
                        <span className="text-slate-200">{agent.architecture}</span>
                      </div>
                    </div>

                    <div className="flex items-start gap-2 pt-2 border-t border-slate-800/60">
                      <Cpu className="w-3.5 h-3.5 text-[#00D4FF] shrink-0 mt-0.5" />
                      <div>
                        <span className="text-slate-400 block text-[11px] uppercase">
                          Target Model:
                        </span>
                        <span className="text-slate-200">{agent.targetModel}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Action & Tools Footer */}
                <div className="pt-3 border-t border-slate-800/60 space-y-3">
                  <div>
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 mb-2">
                      <Wrench className="w-3 h-3 text-[#00D4FF]" />
                      <span>Configured Tools:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {agent.tools.map((tool) => (
                        <span
                          key={tool}
                          className="text-[11px] font-mono px-2 py-0.5 bg-[#162036] text-slate-300 border border-slate-700/60 rounded"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Run Task Controls */}
                  <div className="flex items-center justify-between pt-2">
                    <button
                      onClick={() => toggleAgentAvailability(agent.codename)}
                      className="text-[11px] font-mono text-slate-500 hover:text-slate-300 transition-colors"
                      title="Simulate superuser lifecycle transition"
                    >
                      {isAvailable ? 'Demote to Planned' : 'Set Available (Test)'}
                    </button>

                    <button
                      onClick={() => setSelectedAgentForTask(agent)}
                      disabled={!isAvailable}
                      className={`px-3 py-1.5 text-xs font-mono rounded flex items-center gap-1.5 transition-colors ${
                        isAvailable
                          ? 'bg-[#00D4FF] text-[#0A0F1E] font-semibold hover:bg-[#38bdf8] shadow-xs'
                          : 'bg-slate-800/60 text-slate-500 cursor-not-allowed border border-slate-800'
                      }`}
                      title={isAvailable ? 'Execute task' : 'Requires Available status to run tasks'}
                    >
                      {isAvailable ? (
                        <>
                          <Play className="w-3 h-3 fill-current" />
                          <span>Run Task</span>
                        </>
                      ) : (
                        <>
                          <Lock className="w-3 h-3 text-slate-500" />
                          <span>Locked (Planned)</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-12 text-center bg-[#0F172A] border border-dashed border-slate-800 rounded-lg">
          <Bot className="w-8 h-8 text-slate-500 mx-auto mb-3" />
          <p className="text-sm text-slate-300 font-mono">
            No agents match the filter: "{searchQuery}"
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedCategory('All');
            }}
            className="mt-3 text-xs font-mono text-[#00D4FF] hover:underline"
          >
            Reset Filters
          </button>
        </div>
      )}

      {/* Agent Task Execution Modal */}
      {selectedAgentForTask && (
        <AgentTaskModal
          agent={selectedAgentForTask}
          isOpen={!!selectedAgentForTask}
          onClose={() => setSelectedAgentForTask(null)}
        />
      )}
    </div>
  );
};
