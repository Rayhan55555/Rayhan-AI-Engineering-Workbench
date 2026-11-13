import React, { Suspense, lazy, useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowLeft,
  ArrowUpRight,
  Code2,
  Network,
  Play,
  ShieldCheck,
  Terminal,
} from 'lucide-react';
import { SafeDemoDefinitionDTO, SafeDemoRunResponseDTO } from '../../types';
import { executeSafeDemo, fetchSafeDemos } from '../../lib/api/portfolio';

const LazyMermaidViewer = lazy(() =>
  import('../workbench/MermaidViewer').then((m) => ({ default: m.MermaidViewer }))
);

interface SafeDemosViewProps {
  selectedSlug?: string;
  onNavigateHash: (hash: string) => void;
}

const DEMO_ICONS: Record<string, React.ElementType> = {
  'code-analyzer': Code2,
  'security-scanner': ShieldCheck,
  'architecture-diagram': Network,
};

export const SafeDemosView: React.FC<SafeDemosViewProps> = ({
  selectedSlug,
  onNavigateHash,
}) => {
  const [demos, setDemos] = useState<SafeDemoDefinitionDTO[]>([]);
  const [inputCode, setInputCode] = useState('');
  const [language, setLanguage] = useState<'python' | 'typescript'>('python');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SafeDemoRunResponseDTO | null>(null);

  useEffect(() => {
    fetchSafeDemos().then((list) => {
      setDemos(list);
      if (selectedSlug) {
        const match = list.find((d) => d.slug === selectedSlug);
        if (match && match.samples.length > 0) {
          setInputCode(match.samples[0].input_code);
          setLanguage(match.samples[0].language);
          setResult(null);
          setError(null);
        }
      }
    });
  }, [selectedSlug]);

  const activeDemo = selectedSlug ? demos.find((d) => d.slug === selectedSlug) : undefined;

  const handleRunDemo = async () => {
    if (!activeDemo) return;
    setRunning(true);
    setError(null);
    try {
      const payload =
        activeDemo.slug === 'architecture-diagram'
          ? { prompt: inputCode }
          : { code: inputCode, language };
      const res = await executeSafeDemo(activeDemo.slug, payload);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Demo run failed.');
    } finally {
      setRunning(false);
    }
  };

  if (selectedSlug && activeDemo) {
    const Icon = DEMO_ICONS[activeDemo.slug] || Terminal;

    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-14 space-y-8">
        <button
          onClick={() => onNavigateHash('#portfolio/demos')}
          className="inline-flex items-center gap-2 text-xs font-mono text-[#00D4FF] hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>All Safe Demos</span>
        </button>

        <header className="space-y-3 border-b border-slate-800/80 pb-6">
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-400">
            <span className="text-[#00D4FF] font-semibold">{activeDemo.demo_label}</span>
            <span aria-hidden="true">·</span>
            <span>Read-Only Sandbox</span>
            <span aria-hidden="true">·</span>
            <span>{activeDemo.rate_limit}</span>
            <span aria-hidden="true">·</span>
            <span>Results Not Stored</span>
          </div>

          <div className="flex items-center gap-3">
            <Icon className="w-6 h-6 text-[#00D4FF]" />
            <h1 className="text-2xl sm:text-3xl font-bold font-display text-white">
              {activeDemo.title}
            </h1>
          </div>
          <p className="text-sm sm:text-base text-slate-300 max-w-3xl">{activeDemo.description}</p>
        </header>

        {/* Sample Preset Selector */}
        <div className="space-y-2">
          <div className="text-xs font-mono text-slate-400">Load Curated Sample Input:</div>
          <div className="flex flex-wrap gap-2">
            {activeDemo.samples.map((sample, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setInputCode(sample.input_code);
                  setLanguage(sample.language);
                  setResult(null);
                  setError(null);
                }}
                className="px-3 py-1.5 text-xs font-mono bg-[#0F172A] hover:bg-[#162036] text-slate-200 border border-slate-700 hover:border-[#00D4FF]/40 rounded transition-colors whitespace-nowrap shrink-0"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Editor */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label htmlFor="demo-input" className="text-xs font-mono text-slate-300">
              {activeDemo.slug === 'architecture-diagram'
                ? 'System Description (in-memory only):'
                : 'Code Snippet Input (in-memory only, zero filesystem access):'}
            </label>
            {activeDemo.slug === 'code-analyzer' && (
              <div className="flex items-center gap-1 p-0.5 bg-[#0F172A] border border-slate-800 rounded">
                {(['python', 'typescript'] as const).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLanguage(lang)}
                    className={`px-2.5 py-1 text-xs font-mono rounded ${
                      language === lang ? 'bg-[#162036] text-[#00D4FF]' : 'text-slate-400'
                    }`}
                  >
                    {lang}
                  </button>
                ))}
              </div>
            )}
          </div>

          <textarea
            id="demo-input"
            value={inputCode}
            onChange={(e) => setInputCode(e.target.value)}
            rows={activeDemo.slug === 'architecture-diagram' ? 4 : 9}
            className="w-full p-4 bg-[#060913] border border-slate-800 focus:border-[#00D4FF]/60 focus:outline-none rounded font-mono text-xs sm:text-sm text-slate-100 leading-relaxed"
          />

          <div className="flex flex-wrap items-center justify-between gap-4">
            <span className="text-xs font-mono text-slate-500">
              Isolated sandbox · {activeDemo.timeout_seconds}s max timeout · No workbench credentials used
            </span>
            <button
              onClick={handleRunDemo}
              disabled={running || !inputCode.trim()}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-mono font-semibold bg-[#00D4FF] text-[#0A0F1E] hover:bg-[#38BDF8] disabled:opacity-50 rounded transition-colors whitespace-nowrap shrink-0"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{running ? 'Running Isolated Check...' : 'Run Sample Check'}</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-[#0F172A] border border-rose-500/40 rounded flex items-start gap-2.5 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Output Panel */}
        {result && (
          <section className="p-6 bg-[#0F172A] border border-slate-800 rounded-lg space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800 text-xs font-mono">
              <span className="text-[#00D4FF] font-semibold">{result.demo_label}</span>
              <span className="text-slate-400 tabular-nums">
                Completed in {result.execution_ms} ms · Persisted: No
              </span>
            </div>

            {result.slug === 'architecture-diagram' && result.output.mermaid_code ? (
              <Suspense
                fallback={
                  <div className="p-4 text-xs font-mono text-slate-400">Rendering diagram...</div>
                }
              >
                <LazyMermaidViewer
                  code={String(result.output.mermaid_code)}
                  title="Generated Architecture Diagram (Sample)"
                />
              </Suspense>
            ) : result.slug === 'security-scanner' ? (
              <div className="space-y-4">
                <div className="text-sm font-mono text-slate-200 tabular-nums">
                  Findings detected: {result.output.total_findings ?? 0}
                </div>
                {(result.output.findings || []).length === 0 ? (
                  <p className="text-sm text-emerald-300">
                    No matching static security rule violations found in sample input.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {(result.output.findings || []).map((f: any, idx: number) => (
                      <div key={idx} className="p-4 bg-[#0A0F1E] border border-slate-800 rounded space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                          <span className="text-amber-300 uppercase font-semibold">{f.severity}</span>
                          <span className="text-slate-500">·</span>
                          <span className="text-[#00D4FF]">{f.rule_id}</span>
                          <span className="text-slate-500">·</span>
                          <span className="text-slate-400">{f.cwe}</span>
                          <span className="text-slate-500">·</span>
                          <span className="text-slate-400 tabular-nums">Line {f.line}</span>
                        </div>
                        <div className="text-sm font-semibold text-white">{f.title}</div>
                        <div className="text-xs text-slate-400">{f.fix}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="p-3 bg-[#0A0F1E] border border-slate-800 rounded">
                    <div className="text-slate-500">Language</div>
                    <div className="text-white font-semibold mt-1">{result.output.language || language}</div>
                  </div>
                  <div className="p-3 bg-[#0A0F1E] border border-slate-800 rounded">
                    <div className="text-slate-500">Functions Parsed</div>
                    <div className="text-white font-semibold mt-1 tabular-nums">
                      {(result.output.functions || []).length}
                    </div>
                  </div>
                  <div className="p-3 bg-[#0A0F1E] border border-slate-800 rounded">
                    <div className="text-slate-500">Quality Observations</div>
                    <div className="text-white font-semibold mt-1 tabular-nums">
                      {(result.output.issues || []).length}
                    </div>
                  </div>
                </div>

                {(result.output.issues || []).length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-mono text-slate-400">AST / Pattern Observations:</div>
                    <ul className="space-y-2">
                      {(result.output.issues || []).map((iss: any, idx: number) => (
                        <li
                          key={idx}
                          className="p-3 bg-[#0A0F1E] border border-slate-800 rounded text-xs text-slate-300 font-mono"
                        >
                          <span className="text-[#00D4FF]">{iss.type}</span> — {iss.message}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </section>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-10">
      <header className="space-y-3 max-w-2xl">
        <div className="text-xs font-mono text-[#00D4FF]">Demo — Sample Data Sandbox</div>
        <h1 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
          Isolated Read-Only Engineering Demos
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Test core AST analysis, security scanning, and Mermaid topology generation in an isolated sandbox using sample inputs only. Zero internal data exposure, zero stored results.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {demos.map((demo) => {
          const Icon = DEMO_ICONS[demo.slug] || Terminal;
          return (
            <div
              key={demo.slug}
              className="p-6 bg-[#0F172A] border border-slate-800 hover:border-[#00D4FF]/40 rounded-lg flex flex-col justify-between gap-6 transition-colors"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                  <span className="text-[#00D4FF]">{demo.demo_label}</span>
                  <Icon className="w-4 h-4 text-slate-400" />
                </div>
                <h2 className="text-xl font-bold font-display text-white">{demo.title}</h2>
                <p className="text-sm text-slate-300 leading-relaxed">{demo.description}</p>
                <div className="text-xs font-mono text-slate-500 pt-1">
                  {demo.rate_limit} · {demo.timeout_seconds}s timeout
                </div>
              </div>

              <button
                onClick={() => onNavigateHash(`#portfolio/demos/${demo.slug}`)}
                className="w-full py-2 px-4 text-xs font-mono font-medium text-[#00D4FF] bg-[#162036] hover:bg-[#1E2B48] border border-[#00D4FF]/30 rounded flex items-center justify-between transition-colors whitespace-nowrap shrink-0"
              >
                <span>Open Isolated Sandbox</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
