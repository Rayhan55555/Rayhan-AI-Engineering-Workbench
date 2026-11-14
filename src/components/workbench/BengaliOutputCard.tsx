import React, { useState } from 'react';
import { BengaliReport } from '../../types';
import { DiffView } from './DiffView';
import { ChevronDown, ChevronUp, Code2, Clock } from 'lucide-react';

interface BengaliOutputCardProps {
  report: BengaliReport;
  rawOutput?: string | null;
  errorMessage?: string | null;
  durationMs?: number | null;
  simulated?: boolean;
  defaultFilePath?: string;
}

export const BengaliOutputCard: React.FC<BengaliOutputCardProps> = ({
  report,
  rawOutput,
  errorMessage,
  durationMs,
  simulated,
  defaultFilePath,
}) => {
  const [showRaw, setShowRaw] = useState(false);

  // Extract optional unified diff if JSON payload carries `diff`
  let diffText: string | null = null;
  let targetFile = defaultFilePath;
  if (rawOutput) {
    try {
      const parsed = JSON.parse(rawOutput);
      if (parsed && typeof parsed.diff === 'string' && parsed.diff.trim()) {
        diffText = parsed.diff;
      }
      if (parsed && typeof parsed.target_file === 'string') {
        targetFile = parsed.target_file;
      }
    } catch {
      // Markdown or plain text output
    }
  }

  return (
    <div className="bg-[#0F172A] border border-slate-800 rounded-lg overflow-hidden">
      {/* Top Headline Summary */}
      <div className="px-5 py-4 bg-[#162036]/70 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <div className="text-xs font-mono text-[#00D4FF] mb-0.5">
            {report.agent_name_bn} · [{report.agent_slug}]
          </div>
          <h4 className="text-base sm:text-lg font-semibold text-white">
            {report.summary_bn}
          </h4>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-400 tabular-nums shrink-0">
          {typeof durationMs === 'number' && (
            <span className="inline-flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              {durationMs} ms
            </span>
          )}
          {typeof simulated === 'boolean' && (
            <span className={simulated ? 'text-amber-300' : 'text-emerald-400'}>
              {simulated ? 'Simulated' : 'Real Tool'}
            </span>
          )}
        </div>
      </div>

      {/* Structured 4-Part Bengali Report */}
      <div className="p-5 space-y-5 text-sm sm:text-base leading-relaxed">
        {/* Part 1 */}
        <section className="space-y-1.5">
          <h5 className="text-sm font-semibold text-white">
            🤖 Agent কী করলো:
          </h5>
          <p className="text-slate-300 pl-1">
            {report.what_agent_did}
          </p>
        </section>

        <div className="border-t border-slate-800/80" />

        {/* Part 2 */}
        <section className="space-y-2">
          <h5 className="text-sm font-semibold text-white">
            📋 কী পাওয়া গেলো:
          </h5>
          <ul className="space-y-1.5 text-slate-300 pl-1">
            {report.findings.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-[#00D4FF] mt-0.5 select-none">•</span>
                <span className="break-words">{item}</span>
              </li>
            ))}
          </ul>
        </section>

        <div className="border-t border-slate-800/80" />

        {/* Part 3 */}
        <section className="space-y-2">
          <h5 className="text-sm font-semibold text-white">
            ✅ পরামর্শ:
          </h5>
          <ol className="space-y-1.5 text-slate-300 pl-1">
            {report.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <span className="text-emerald-400 font-mono text-xs mt-1 shrink-0 tabular-nums">
                  {idx + 1}.
                </span>
                <span className="break-words">{rec}</span>
              </li>
            ))}
          </ol>
        </section>

        <div className="border-t border-slate-800/80" />

        {/* Part 4 */}
        <section className="space-y-2">
          <h5 className="text-sm font-semibold text-amber-300">
            ⚠️ সীমাবদ্ধতা:
          </h5>
          <ul className="space-y-1.5 text-slate-400 text-xs sm:text-sm pl-1">
            {report.limitations.map((lim, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-400 mt-0.5 select-none">•</span>
                <span className="break-words">{lim}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Diff View if Coding Agent generated a patch */}
        {diffText && (
          <div className="pt-2">
            <div className="text-xs font-mono text-slate-400 mb-2">
              প্রস্তাবিত Code Patch (Diff):
            </div>
            <DiffView diffText={diffText} filePath={targetFile} />
          </div>
        )}

        {/* Collapsible Raw Output Toggle */}
        {(rawOutput || errorMessage) && (
          <div className="pt-2 border-t border-slate-800/80">
            <button
              type="button"
              onClick={() => setShowRaw((prev) => !prev)}
              className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-[#00D4FF] transition-colors py-1"
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>{showRaw ? 'Technical Output লুকান' : 'বিস্তারিত Technical Output দেখুন'}</span>
              {showRaw ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showRaw && (
              <pre className="mt-2 p-3.5 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono text-slate-300 whitespace-pre-wrap max-h-72 overflow-y-auto leading-relaxed">
                {rawOutput || errorMessage}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
