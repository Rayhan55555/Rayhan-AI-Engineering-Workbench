import React, { useState } from 'react';
import { Copy, Check, FileCode, AlertCircle, ShieldAlert } from 'lucide-react';

interface TestTemplateViewProps {
  functionName: string;
  targetFile: string;
  code: string;
  templateType?: string;
}

export const TestTemplateView: React.FC<TestTemplateViewProps> = ({
  functionName,
  targetFile,
  code,
  templateType = 'unit',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="rounded border border-slate-800 bg-[#0F172A] overflow-hidden my-3">
      {/* Header Bar */}
      <div className="px-4 py-2.5 bg-[#0A0F1E] border-b border-slate-800 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-[#00D4FF]" />
          <span className="font-mono text-xs font-semibold text-slate-200">
            test_{functionName}
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/30 uppercase">
            {templateType}
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 font-semibold flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            GENERATED - REVIEW REQUIRED
          </span>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          title="Copy generated template to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-semibold">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-400" />
              <span>Copy Template</span>
            </>
          )}
        </button>
      </div>

      {/* Code Body with Watermark Banner */}
      <div className="relative">
        {/* Subtle Watermark Badge */}
        <div className="absolute right-3 top-3 pointer-events-none select-none text-[10px] font-mono text-slate-700 uppercase tracking-widest border border-slate-800/60 px-2 py-0.5 rounded bg-[#0A0F1E]/80">
          Deterministic Generator • No LLM
        </div>

        <pre className="p-4 text-xs font-mono text-slate-300 bg-[#0A0F1E] overflow-x-auto leading-relaxed">
          <code>{code}</code>
        </pre>
      </div>

      {/* Safety Notice Footer */}
      <div className="px-4 py-2 bg-[#162036]/40 border-t border-slate-800/80 text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span>No auto-write to disk. Copy and paste into your test suite after verifying assertions.</span>
      </div>
    </div>
  );
};
