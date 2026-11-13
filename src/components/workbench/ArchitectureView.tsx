import React, { useState, useEffect } from 'react';
import {
  Layers,
  Network,
  FileCheck2,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  RefreshCw,
  Plus,
  GitBranch,
  Search,
  Sliders,
  ShieldCheck,
  ExternalLink,
} from 'lucide-react';
import { MermaidViewer } from './MermaidViewer';

interface ArchitectureFinding {
  category: string;
  severity: 'info' | 'warning' | 'error';
  title: string;
  description: string;
  affected_components: string[];
  recommendation: string;
}

interface ArchitectureReport {
  analysis_type: string;
  health_score: number;
  grade: string;
  summary: string;
  findings: ArchitectureFinding[];
  violations: string[];
  recommendations: string[];
  metrics: Record<string, any>;
  diagrams: Record<string, string>;
}

interface ADRSummary {
  number: number;
  title: string;
  status: string;
  date: string;
  filename: string;
  path: string;
}

export const ArchitectureView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'health' | 'diagrams' | 'adrs' | 'contracts'>('health');
  const [report, setReport] = useState<ArchitectureReport | null>(null);
  const [adrs, setAdrs] = useState<ADRSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Diagram Studio state
  const [selectedDiagramType, setSelectedDiagramType] = useState<string>('system');
  const [diagramCode, setDiagramCode] = useState<string>('');
  const [diagramTitle, setDiagramTitle] = useState<string>('System Architecture');
  const [isGeneratingDiagram, setIsGeneratingDiagram] = useState(false);

  // ADR creation state
  const [newAdrTitle, setNewAdrTitle] = useState('');
  const [newAdrDecision, setNewAdrDecision] = useState('');
  const [newAdrContext, setNewAdrContext] = useState('');
  const [generatedAdrPreview, setGeneratedAdrPreview] = useState<string | null>(null);
  const [isCreatingAdr, setIsCreatingAdr] = useState(false);

  useEffect(() => {
    fetchHealthReport();
    fetchExistingAdrs();
    generateDiagram('system');
  }, []);

  const fetchHealthReport = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/architecture/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis_type: 'full' }),
      });
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch {
      // Fallback handled gracefully
    } finally {
      setIsLoading(false);
    }
  };

  const fetchExistingAdrs = async () => {
    try {
      const res = await fetch('/api/v1/architecture/adrs');
      if (res.ok) {
        const data = await res.json();
        setAdrs(data);
      }
    } catch {
      // Ignore error
    }
  };

  const generateDiagram = async (type: string) => {
    setIsGeneratingDiagram(true);
    setSelectedDiagramType(type);
    try {
      const res = await fetch('/api/v1/architecture/diagram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diagram_type: type }),
      });
      if (res.ok) {
        const data = await res.json();
        setDiagramCode(data.mermaid_code);
        setDiagramTitle(data.title);
      }
    } catch {
      // Ignore error
    } finally {
      setIsGeneratingDiagram(false);
    }
  };

  const handleCreateAdr = async () => {
    if (!newAdrTitle || !newAdrDecision) return;
    setIsCreatingAdr(true);
    try {
      const res = await fetch('/api/v1/architecture/adr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newAdrTitle,
          decision: newAdrDecision,
          context: newAdrContext || 'Standardizing workbench architecture.',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedAdrPreview(data.content);
        fetchExistingAdrs();
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsCreatingAdr(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (score >= 80) return 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10';
    if (score >= 70) return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span className="text-[#00D4FF]">SYSTEM ARCHITECTURE LAB</span>
            <span aria-hidden="true">·</span>
            <span>PHASE 09 VERIFIED AGENT</span>
            <span aria-hidden="true">·</span>
            <span className="text-emerald-400">MERMAID.JS ENGINE</span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Architecture Sentinel & Studio
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Static AST layer inspection, import cycle detector, authentic Mermaid.js diagrams, and Architecture Decision Records (ADR).
          </p>
        </div>

        {report && (
          <div className="flex items-center gap-3">
            <div className={`px-4 py-2 rounded-lg border font-mono flex items-center gap-3 ${getScoreColor(report.health_score)}`}>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Health Score</div>
                <div className="text-xl font-bold">{report.health_score} / 100</div>
              </div>
              <div className="text-2xl font-extrabold border-l border-slate-700/60 pl-3">
                {report.grade}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto font-mono text-xs">
        <button
          onClick={() => setActiveTab('health')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'health'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Architecture Health
        </button>

        <button
          onClick={() => setActiveTab('diagrams')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'diagrams'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Network className="w-3.5 h-3.5" />
          Diagram Studio
        </button>

        <button
          onClick={() => setActiveTab('adrs')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'adrs'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCheck2 className="w-3.5 h-3.5" />
          ADR Manager
        </button>

        <button
          onClick={() => setActiveTab('contracts')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'contracts'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          API Contract Review
        </button>
      </div>

      {/* TAB 1: ARCHITECTURE HEALTH */}
      {activeTab === 'health' && report && (
        <div className="space-y-6">
          {/* Summary Box */}
          <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5">
            <h3 className="text-sm font-semibold text-white font-mono mb-2 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#00D4FF]" />
              <span>Architectural Integrity Assessment</span>
            </h3>
            <p className="text-xs text-slate-300 font-mono leading-relaxed">{report.summary}</p>
          </div>

          {/* Metric Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-4">
              <div className="text-xs font-mono text-slate-400">Circular Dependencies</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {report.metrics.circular_dependency_count || 0}
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-0.5">Acyclic module imports</div>
            </div>

            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-4">
              <div className="text-xs font-mono text-slate-400">Layer Violations</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {report.violations.length}
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-0.5">Strict Clean Arch</div>
            </div>

            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-4">
              <div className="text-xs font-mono text-slate-400">Total API Endpoints</div>
              <div className="text-2xl font-bold font-mono text-[#00D4FF] mt-1">
                {report.metrics.total_routes || 0}
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-0.5">Across FastAPI routers</div>
            </div>

            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-4">
              <div className="text-xs font-mono text-slate-400">Modules Analyzed</div>
              <div className="text-2xl font-bold font-mono text-purple-400 mt-1">
                {report.metrics.modules_count || 0}
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-0.5">In backend/app tree</div>
            </div>
          </div>

          {/* Findings List */}
          <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white font-mono flex items-center justify-between">
              <span>Auditor Findings ({report.findings.length})</span>
              <button
                onClick={fetchHealthReport}
                className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-mono"
              >
                <RefreshCw className="w-3 h-3" /> Re-scan
              </button>
            </h3>

            <div className="space-y-3">
              {report.findings.map((f, i) => (
                <div
                  key={i}
                  className={`p-3.5 rounded border text-xs font-mono space-y-1.5 ${
                    f.severity === 'error'
                      ? 'bg-rose-950/20 border-rose-800/40 text-rose-300'
                      : f.severity === 'warning'
                      ? 'bg-amber-950/20 border-amber-800/40 text-amber-300'
                      : 'bg-emerald-950/20 border-emerald-800/40 text-emerald-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{f.title}</span>
                    <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-black/40 border border-slate-700">
                      {f.category}
                    </span>
                  </div>
                  <p className="text-slate-300">{f.description}</p>
                  <p className="text-slate-400 text-[11px]">💡 Recommendation: {f.recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DIAGRAM STUDIO */}
      {activeTab === 'diagrams' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-mono">
              {[
                { id: 'system', label: 'System Architecture' },
                { id: 'er', label: 'Database ER' },
                { id: 'api_flow', label: 'API Sequence Flow' },
                { id: 'agent', label: 'Agent State Machine' },
                { id: 'component', label: 'Component Graph' },
              ].map((d) => (
                <button
                  key={d.id}
                  onClick={() => generateDiagram(d.id)}
                  className={`px-3 py-1.5 rounded transition-colors whitespace-nowrap ${
                    selectedDiagramType === d.id
                      ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
                      : 'text-slate-400 hover:text-white bg-[#0F172A] border border-slate-800'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => generateDiagram(selectedDiagramType)}
              disabled={isGeneratingDiagram}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-mono font-medium disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingDiagram ? 'animate-spin' : ''}`} />
              <span>Regenerate Diagram</span>
            </button>
          </div>

          {/* Mermaid diagram viewer */}
          <MermaidViewer code={diagramCode} title={diagramTitle} />
        </div>
      )}

      {/* TAB 3: ADR MANAGER */}
      {activeTab === 'adrs' && (
        <div className="space-y-6">
          {/* Create ADR Section */}
          <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
              <Plus className="w-4 h-4 text-[#00D4FF]" />
              <span>Create Architecture Decision Record (ADR)</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-mono text-slate-300">Decision Title:</label>
                <input
                  type="text"
                  placeholder="e.g., Adopt Redis for sliding rate limit cache"
                  value={newAdrTitle}
                  onChange={(e) => setNewAdrTitle(e.target.value)}
                  className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#00D4FF] mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-mono text-slate-300">Context & Rationale:</label>
                <input
                  type="text"
                  placeholder="Problem or architectural challenge being solved"
                  value={newAdrContext}
                  onChange={(e) => setNewAdrContext(e.target.value)}
                  className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#00D4FF] mt-1"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-mono text-slate-300">Decision Statement:</label>
              <textarea
                rows={3}
                placeholder="What architectural decision is being committed..."
                value={newAdrDecision}
                onChange={(e) => setNewAdrDecision(e.target.value)}
                className="w-full bg-[#0A0F1E] border border-slate-800 rounded p-3 text-xs text-white font-mono focus:outline-none focus:border-[#00D4FF] mt-1"
              />
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={handleCreateAdr}
                disabled={isCreatingAdr || !newAdrTitle || !newAdrDecision}
                className="flex items-center gap-1.5 px-4 py-1.5 bg-[#00D4FF]/10 border border-[#00D4FF]/30 hover:bg-[#00D4FF]/20 text-[#00D4FF] rounded text-xs font-mono font-medium disabled:opacity-50"
              >
                {isCreatingAdr ? 'Synthesizing ADR...' : 'Generate ADR Template (SUGGEST)'}
              </button>
            </div>

            {generatedAdrPreview && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                  <span>Generated ADR Preview (In-Memory SUGGEST Scope):</span>
                  <span className="text-amber-400 text-[11px]">Writing to disk requires IMPLEMENT approval</span>
                </div>
                <pre className="p-4 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono text-slate-300 max-h-64 overflow-auto whitespace-pre leading-relaxed">
                  {generatedAdrPreview}
                </pre>
              </div>
            )}
          </div>

          {/* Existing ADRs List */}
          <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white font-mono flex items-center justify-between">
              <span>Standard Architecture Decisions ({adrs.length})</span>
              <button
                onClick={fetchExistingAdrs}
                className="text-xs text-slate-400 hover:text-white font-mono flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" /> Refresh
              </button>
            </h3>

            {adrs.length === 0 ? (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">
                No ADRs saved to docs/adr/ yet. Use the generator above or dispatch the Architecture Agent.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
                {adrs.map((a) => (
                  <div key={a.number} className="p-3 bg-[#0A0F1E] border border-slate-800 rounded flex flex-col justify-between space-y-2">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-[#00D4FF] font-semibold">ADR-{a.number.toString().padStart(3, '0')}</span>
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px]">
                          {a.status}
                        </span>
                      </div>
                      <h4 className="text-white font-medium mt-1">{a.title}</h4>
                    </div>
                    <div className="text-[11px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-800/80">
                      <span>Date: {a.date}</span>
                      <span className="text-slate-400">{a.filename}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: API CONTRACTS */}
      {activeTab === 'contracts' && report && (
        <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white font-mono">FastAPI API Contract Inventory</h3>
              <p className="text-xs text-slate-400">Endpoint contracts inspected via AST parsing across all router modules.</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono">
              <span className="text-slate-400">Total:</span>
              <span className="text-white font-semibold">{report.metrics.total_routes || 0}</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <th className="py-2.5 px-3">Method</th>
                  <th className="py-2.5 px-3">Route Path</th>
                  <th className="py-2.5 px-3">Router Module</th>
                  <th className="py-2.5 px-3">Documentation Status</th>
                  <th className="py-2.5 px-3">Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {(report.metrics.endpoints || []).map((ep: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 font-semibold text-[#00D4FF]">{ep.method}</td>
                    <td className="py-2 px-3 text-white">{ep.path || '/'}</td>
                    <td className="py-2 px-3 text-slate-400">{ep.router}</td>
                    <td className="py-2 px-3">
                      {ep.is_documented ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
                          DOCUMENTED
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px]">
                          MISSING DOC
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-slate-400 max-w-xs truncate">{ep.docstring}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
