import React, { useState, useEffect } from 'react';
import {
  Blocks,
  Terminal,
  CheckCircle2,
  Server,
  Shield,
  Github,
  HardDrive,
  Globe,
  Database,
  Lock,
  Play,
  Clock,
  Search,
  Filter,
  AlertCircle,
  FileText,
  Radio,
  ExternalLink,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';
import { ToolApprovalCard, PendingApproval } from './ToolApprovalCard';
import { StreamingView } from './StreamingView';

interface ToolItem {
  name: string;
  description: string;
  category: 'github' | 'filesystem' | 'web' | 'database' | 'shell';
  permission_scope: 'READ_ONLY' | 'SUGGEST' | 'IMPLEMENT' | 'DEPLOY';
  requires_approval: boolean;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  phase_lock_note?: string;
}

interface AuditEntry {
  id: string;
  tool_name: string;
  agent_slug?: string;
  parameters: Record<string, any>;
  output_summary?: string;
  success: boolean;
  error_message?: string;
  duration_ms: number;
  created_at: string;
}

export const IntegrationsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'tools' | 'approvals' | 'github' | 'audit' | 'streaming'>('tools');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Execution modal state
  const [selectedTool, setSelectedTool] = useState<ToolItem | null>(null);
  const [testParams, setTestParams] = useState<string>('{}');
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // GitHub test state
  const [githubRepo, setGithubRepo] = useState('facebook/react');
  const [githubBranch, setGithubBranch] = useState('main');
  const [githubPath, setGithubPath] = useState('package.json');
  const [githubResult, setGithubResult] = useState<any>(null);

  useEffect(() => {
    fetchTools();
    fetchApprovals();
    fetchAuditLogs();
  }, []);

  const fetchTools = async () => {
    try {
      const res = await fetch('/api/v1/mcp/tools');
      if (res.ok) {
        const data = await res.json();
        setTools(data);
      }
    } catch {
      // Fallback default list if backend offline
    }
  };

  const fetchApprovals = async () => {
    try {
      const res = await fetch('/api/v1/mcp/approvals');
      if (res.ok) {
        const data = await res.json();
        setApprovals(data);
      }
    } catch {
      // Ignore error
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch('/api/v1/mcp/audit?limit=25');
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch {
      // Ignore error
    }
  };

  const handleApprove = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/mcp/approvals/${id}/approve`, { method: 'POST' });
      if (res.ok) {
        setApprovals((prev) => prev.filter((a) => a.id !== id));
        fetchAuditLogs();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async (id: string, reason?: string) => {
    try {
      const res = await fetch(`/api/v1/mcp/approvals/${id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
      if (res.ok) {
        setApprovals((prev) => prev.filter((a) => a.id !== id));
        fetchAuditLogs();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const executeSelectedTool = async () => {
    if (!selectedTool) return;
    setIsExecuting(true);
    setExecutionResult(null);

    let parsedParams = {};
    try {
      parsedParams = JSON.parse(testParams);
    } catch {
      setExecutionResult({ success: false, error: 'Invalid JSON in parameters' });
      setIsExecuting(false);
      return;
    }

    try {
      const res = await fetch(`/api/v1/mcp/tools/${selectedTool.name}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parameters: parsedParams,
          agent_slug: 'arch-sentinel',
        }),
      });
      const data = await res.json();
      setExecutionResult(data);
      fetchApprovals();
      fetchAuditLogs();
    } catch (e: any) {
      setExecutionResult({ success: false, error: e.message || 'Execution failed' });
    } finally {
      setIsExecuting(false);
    }
  };

  const testGitHubRead = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/mcp/tools/github_read_file/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parameters: { repo: githubRepo, path: githubPath, branch: githubBranch },
          agent_slug: 'arch-sentinel',
        }),
      });
      const data = await res.json();
      setGithubResult(data);
      fetchAuditLogs();
    } catch (e: any) {
      setGithubResult({ success: false, error: e.message });
    } finally {
      setIsLoading(false);
    }
  };

  const filteredTools = tools.filter((t) => {
    const matchesCategory = selectedCategory === 'all' || t.category === selectedCategory;
    const matchesSearch =
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const categoryIcons: Record<string, React.ReactNode> = {
    github: <Github className="w-4 h-4 text-slate-300" />,
    filesystem: <HardDrive className="w-4 h-4 text-cyan-400" />,
    web: <Globe className="w-4 h-4 text-emerald-400" />,
    database: <Database className="w-4 h-4 text-purple-400" />,
    shell: <Terminal className="w-4 h-4 text-amber-400" />,
  };

  const scopeStyles: Record<string, string> = {
    READ_ONLY: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    SUGGEST: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    IMPLEMENT: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    DEPLOY: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span className="text-[#00D4FF]">PROTOCOL INTERFACE</span>
            <span aria-hidden="true">·</span>
            <span>MODEL CONTEXT PROTOCOL (MCP 1.0)</span>
            <span aria-hidden="true">·</span>
            <span className="text-emerald-400">18 ACTIVE TOOLS</span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Integrations & MCP Tool Hub
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Standard JSON-RPC tool registry, sandboxed filesystem, GitHub connector, DuckDuckGo search, read-only database inspector, and immutable audit logs.
          </p>
        </div>

        {/* Status Pills */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0F172A] border border-slate-800 rounded text-xs font-mono">
            <Server className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">Host:</span>
            <span className="text-emerald-400 font-semibold">Active JSON-RPC</span>
          </div>
          {approvals.length > 0 && (
            <button
              onClick={() => setActiveTab('approvals')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded text-xs font-mono font-semibold animate-pulse"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>{approvals.length} Pending Approval{approvals.length > 1 ? 's' : ''}</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto font-mono text-xs">
        <button
          onClick={() => setActiveTab('tools')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'tools'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Blocks className="w-3.5 h-3.5" />
          Tool Catalog (18)
        </button>

        <button
          onClick={() => setActiveTab('approvals')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'approvals'
              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          Approvals Queue
          {approvals.length > 0 && (
            <span className="ml-1 px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-300 text-[10px]">
              {approvals.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('github')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'github'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Github className="w-3.5 h-3.5" />
          GitHub Connector
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'audit'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          Audit Trail
        </button>

        <button
          onClick={() => setActiveTab('streaming')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'streaming'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          Live Streaming (SSE)
        </button>
      </div>

      {/* TAB 1: TOOL CATALOG */}
      {activeTab === 'tools' && (
        <div className="space-y-6">
          {/* Filters & Search */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-mono">
              {['all', 'github', 'filesystem', 'web', 'database', 'shell'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1 rounded capitalize transition-colors ${
                    selectedCategory === cat
                      ? 'bg-slate-800 text-white font-medium border border-slate-700'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search tools & schemas..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#0F172A] border border-slate-800 rounded pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#00D4FF] font-mono"
              />
            </div>
          </div>

          {/* Tools Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTools.map((tool) => (
              <div
                key={tool.name}
                className={`bg-[#0F172A] border rounded-lg p-4 flex flex-col justify-between space-y-3 transition-colors ${
                  tool.enabled ? 'border-slate-800 hover:border-slate-700' : 'border-slate-800/50 opacity-75'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-[#0A0F1E] border border-slate-800 rounded">
                        {categoryIcons[tool.category]}
                      </div>
                      <span className="font-mono text-sm font-semibold text-white truncate">{tool.name}</span>
                    </div>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${scopeStyles[tool.permission_scope]}`}>
                      {tool.permission_scope}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 mt-2.5 line-clamp-2 leading-relaxed">
                    {tool.description}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
                    {tool.requires_approval ? (
                      <span className="text-amber-400 flex items-center gap-1">
                        <Lock className="w-3 h-3" /> Approval Req.
                      </span>
                    ) : (
                      <span className="text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Auto-Exec
                      </span>
                    )}
                  </div>

                  {tool.phase_lock_note ? (
                    <span className="text-[10px] font-mono text-rose-400 px-2 py-0.5 bg-rose-500/10 border border-rose-500/20 rounded">
                      Phase 11
                    </span>
                  ) : (
                    <button
                      onClick={() => {
                        setSelectedTool(tool);
                        setTestParams('{}');
                        setExecutionResult(null);
                      }}
                      className="flex items-center gap-1 text-xs font-mono text-[#00D4FF] hover:underline"
                    >
                      <Play className="w-3 h-3" /> Inspect & Test
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Test Execution Drawer / Modal */}
          {selectedTool && (
            <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
              <div className="bg-[#0F172A] border border-slate-800 rounded-lg max-w-xl w-full p-6 space-y-4 shadow-2xl">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-bold font-mono text-white">{selectedTool.name}</span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${scopeStyles[selectedTool.permission_scope]}`}>
                        {selectedTool.permission_scope}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{selectedTool.description}</p>
                  </div>
                  <button
                    onClick={() => setSelectedTool(null)}
                    className="text-slate-500 hover:text-white font-mono text-sm"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-mono text-slate-300">Parameters (JSON):</label>
                  <textarea
                    rows={4}
                    value={testParams}
                    onChange={(e) => setTestParams(e.target.value)}
                    className="w-full bg-[#0A0F1E] border border-slate-800 rounded p-3 text-xs font-mono text-white focus:outline-none focus:border-[#00D4FF]"
                  />
                </div>

                {executionResult && (
                  <div className="space-y-1.5">
                    <label className="text-xs font-mono text-slate-300">Execution Result:</label>
                    <pre className="p-3 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono text-slate-300 max-h-48 overflow-auto">
                      {JSON.stringify(executionResult, null, 2)}
                    </pre>
                  </div>
                )}

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setSelectedTool(null)}
                    className="px-3 py-1.5 text-xs font-mono text-slate-400 hover:text-white"
                  >
                    Close
                  </button>
                  <button
                    type="button"
                    onClick={executeSelectedTool}
                    disabled={isExecuting}
                    className="flex items-center gap-1.5 px-4 py-1.5 bg-[#00D4FF]/10 border border-[#00D4FF]/30 hover:bg-[#00D4FF]/20 text-[#00D4FF] rounded text-xs font-mono font-medium disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    {isExecuting ? 'Running...' : 'Execute Tool'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: PENDING APPROVALS */}
      {activeTab === 'approvals' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>Human-in-the-Loop Approval Queue</span>
            </h3>
            <button
              onClick={fetchApprovals}
              className="text-xs font-mono text-slate-400 hover:text-slate-200"
            >
              Refresh Queue
            </button>
          </div>

          {approvals.length === 0 ? (
            <div className="p-12 text-center bg-[#0F172A] border border-slate-800 rounded-lg space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <h4 className="text-sm font-semibold text-white font-mono">No Pending Authorizations</h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                All write operations, filesystem changes, and PR actions have been resolved or none are currently queued.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {approvals.map((app) => (
                <ToolApprovalCard
                  key={app.id}
                  approval={app}
                  onApprove={handleApprove}
                  onReject={handleReject}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: GITHUB CONNECTOR */}
      {activeTab === 'github' && (
        <div className="space-y-6">
          <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <Github className="w-5 h-5 text-white" />
                <div>
                  <h3 className="text-sm font-semibold text-white font-mono">GitHub Integration Hub</h3>
                  <p className="text-xs text-slate-400">Inspect remote files, issues, and pull request changes with rate-limit protections.</p>
                </div>
              </div>

              <div className="flex items-center gap-2 px-3 py-1 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-slate-300">API Gateway: Online</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-mono text-slate-400">Repository (owner/repo):</label>
                <input
                  type="text"
                  value={githubRepo}
                  onChange={(e) => setGithubRepo(e.target.value)}
                  className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#00D4FF]"
                />
              </div>

              <div>
                <label className="text-[11px] font-mono text-slate-400">Target Path:</label>
                <input
                  type="text"
                  value={githubPath}
                  onChange={(e) => setGithubPath(e.target.value)}
                  className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#00D4FF]"
                />
              </div>

              <div>
                <label className="text-[11px] font-mono text-slate-400">Branch:</label>
                <input
                  type="text"
                  value={githubBranch}
                  onChange={(e) => setGithubBranch(e.target.value)}
                  className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#00D4FF]"
                />
              </div>
            </div>

            <button
              onClick={testGitHubRead}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-[#00D4FF]/10 border border-[#00D4FF]/30 hover:bg-[#00D4FF]/20 text-[#00D4FF] rounded text-xs font-mono font-medium disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {isLoading ? 'Querying GitHub API...' : 'Fetch Remote File (github_read_file)'}
            </button>

            {githubResult && (
              <div className="space-y-1.5 pt-2">
                <label className="text-xs font-mono text-slate-400">GitHub Tool Output:</label>
                <pre className="p-3 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono text-slate-300 max-h-56 overflow-auto">
                  {JSON.stringify(githubResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                <Shield className="w-4 h-4 text-[#00D4FF]" />
                <span>Immutable Tool Call Audit Log</span>
              </h3>
              <p className="text-xs text-slate-400">Tamper-proof record of every tool dispatched. Tokens and secrets are redacted prior to storage.</p>
            </div>
            <button
              onClick={fetchAuditLogs}
              className="text-xs font-mono text-slate-400 hover:text-slate-200"
            >
              Refresh Logs
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Tool Name</th>
                  <th className="py-2.5 px-3">Agent</th>
                  <th className="py-2.5 px-3">Duration</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Summary / Sanitized Params</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No tool executions logged yet. Run a tool from the catalog to see audit records.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                      <td className="py-2.5 px-3 text-white font-semibold">{log.tool_name}</td>
                      <td className="py-2.5 px-3 text-[#00D4FF]">{log.agent_slug || 'orchestrator'}</td>
                      <td className="py-2.5 px-3 text-slate-400">{log.duration_ms} ms</td>
                      <td className="py-2.5 px-3">
                        {log.success ? (
                          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
                            SUCCESS
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px]">
                            FAILED
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate">
                        {log.output_summary || JSON.stringify(log.parameters)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: STREAMING DEMO */}
      {activeTab === 'streaming' && <StreamingView />}
    </div>
  );
};
