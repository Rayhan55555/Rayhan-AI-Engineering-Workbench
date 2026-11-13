import React, { useState, useEffect } from 'react';
import {
  FileText,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Download,
  Play,
  RefreshCw,
  Search,
  ExternalLink,
  ShieldAlert,
  FileCheck,
} from 'lucide-react';

interface DocAuditReport {
  total_endpoints: number;
  documented_endpoints: number;
  undocumented_endpoints: number;
  coverage_percentage: number;
  missing_docs: Array<{ path: string; method: string; router: string }>;
  quality_score: number;
  recommendations: string[];
}

interface GeneratedDoc {
  doc_type: string;
  title: string;
  content: string;
  file_target: string;
  word_count: number;
  generated_at: string;
  review_required: boolean;
}

export const DocumentationView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'coverage' | 'generator' | 'audit'>('coverage');
  const [audit, setAudit] = useState<DocAuditReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Doc Generator state
  const [selectedType, setSelectedType] = useState<string>('api');
  const [generatedDoc, setGeneratedDoc] = useState<GeneratedDoc | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchAuditReport();
    generateDoc('api');
  }, []);

  const fetchAuditReport = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/docs/audit', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setAudit(data);
      }
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  };

  const generateDoc = async (docType: string) => {
    setIsGenerating(true);
    setSelectedType(docType);
    try {
      const res = await fetch('/api/v1/docs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_type: docType }),
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedDoc(data);
      }
    } catch {
      // Ignore
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    if (!generatedDoc) return;
    navigator.clipboard.writeText(generatedDoc.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span className="text-[#00D4FF]">DOCUMENTATION INTELLIGENCE</span>
            <span aria-hidden="true">·</span>
            <span>PHASE 09 VERIFIED AGENT</span>
            <span aria-hidden="true">·</span>
            <span className="text-emerald-400">LIVING SPECS</span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Documentation Agent & Spec Studio
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Living OpenAPI reference generation, automated README synthesis, system setup guides, and documentation coverage audits.
          </p>
        </div>

        {audit && (
          <div className="flex items-center gap-3">
            <div className="px-4 py-2 bg-[#0F172A] border border-slate-800 rounded-lg font-mono flex items-center gap-3">
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Coverage</div>
                <div className="text-xl font-bold text-emerald-400">{audit.coverage_percentage}%</div>
              </div>
              <div className="border-l border-slate-800 pl-3">
                <div className="text-[10px] text-slate-400 uppercase">Quality</div>
                <div className="text-xl font-bold text-[#00D4FF]">{audit.quality_score}/100</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto font-mono text-xs">
        <button
          onClick={() => setActiveTab('coverage')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'coverage'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          Doc Coverage Dashboard
        </button>

        <button
          onClick={() => setActiveTab('generator')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'generator'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          Doc Generator & Preview
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-colors ${
            activeTab === 'audit'
              ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCheck className="w-3.5 h-3.5" />
          Quality Audit & Gaps
        </button>
      </div>

      {/* TAB 1: COVERAGE DASHBOARD */}
      {activeTab === 'coverage' && audit && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5">
              <div className="text-xs font-mono text-slate-400">Total API Endpoints</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {audit.total_endpoints}
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-0.5">Across all router modules</div>
            </div>

            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5">
              <div className="text-xs font-mono text-slate-400">Documented Endpoints</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {audit.documented_endpoints}
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-0.5">With full OpenAPI docstrings</div>
            </div>

            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5">
              <div className="text-xs font-mono text-slate-400">Undocumented Gaps</div>
              <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                {audit.undocumented_endpoints}
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-0.5">Endpoints flagged for review</div>
            </div>
          </div>

          {/* Missing Documentation Table */}
          <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-sm font-semibold text-white font-mono">Documentation Coverage Gaps</h3>
                <p className="text-xs text-slate-400">Endpoints currently lacking comprehensive docstrings or descriptions.</p>
              </div>
              <button
                onClick={fetchAuditReport}
                className="text-xs font-mono text-slate-400 hover:text-white flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" /> Re-audit
              </button>
            </div>

            {audit.missing_docs.length === 0 ? (
              <div className="p-8 text-center text-slate-400 font-mono text-xs">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
                <span>All endpoints are fully documented with complete OpenAPI specifications!</span>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                      <th className="py-2.5 px-3">Method</th>
                      <th className="py-2.5 px-3">Route Path</th>
                      <th className="py-2.5 px-3">Router Module</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {audit.missing_docs.map((doc, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2 px-3 text-[#00D4FF] font-semibold">{doc.method}</td>
                        <td className="py-2 px-3 text-white">{doc.path}</td>
                        <td className="py-2 px-3 text-slate-400">{doc.router}</td>
                        <td className="py-2 px-3">
                          <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px]">
                            DOCSTRING MISSING
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: DOC GENERATOR */}
      {activeTab === 'generator' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-mono">
              {[
                { id: 'api', label: 'API Reference Manual' },
                { id: 'readme', label: 'Project README' },
                { id: 'setup', label: 'Setup Guide (SETUP.md)' },
                { id: 'changelog', label: 'Changelog' },
              ].map((d) => (
                <button
                  key={d.id}
                  onClick={() => generateDoc(d.id)}
                  className={`px-3 py-1.5 rounded transition-colors whitespace-nowrap ${
                    selectedType === d.id
                      ? 'bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
                      : 'text-slate-400 hover:text-white bg-[#0F172A] border border-slate-800'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                disabled={!generatedDoc}
                className="flex items-center gap-1 px-3 py-1.5 bg-[#0F172A] border border-slate-800 hover:border-slate-700 text-slate-300 rounded text-xs font-mono"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
              </button>

              <button
                onClick={() => generateDoc(selectedType)}
                disabled={isGenerating}
                className="flex items-center gap-1 px-3 py-1.5 bg-[#00D4FF]/10 border border-[#00D4FF]/30 hover:bg-[#00D4FF]/20 text-[#00D4FF] rounded text-xs font-mono disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                <span>Regenerate</span>
              </button>
            </div>
          </div>

          {generatedDoc && (
            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold font-mono text-white">{generatedDoc.title}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    GENERATED — REVIEW REQUIRED
                  </span>
                </div>
                <div className="text-xs font-mono text-slate-400">
                  Target: <span className="text-[#00D4FF]">{generatedDoc.file_target}</span> ({generatedDoc.word_count} words)
                </div>
              </div>

              <pre className="p-4 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono text-slate-300 max-h-[500px] overflow-auto whitespace-pre-wrap leading-relaxed scrollbar-thin">
                {generatedDoc.content}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: AUDIT & RECOMMENDATIONS */}
      {activeTab === 'audit' && audit && (
        <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white font-mono">Documentation Recommendations</h3>
              <p className="text-xs text-slate-400">Automated advice from the Documentation Agent to maintain 90%+ coverage.</p>
            </div>
            <span className="text-xs font-mono px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">
              Quality Score: {audit.quality_score}/100
            </span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {audit.recommendations.map((rec, i) => (
              <div key={i} className="p-3 bg-[#0A0F1E] border border-slate-800 rounded flex items-start gap-2.5 text-slate-300">
                <span className="text-[#00D4FF] font-bold">0{i + 1}.</span>
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
