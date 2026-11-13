import React, { useState } from 'react';
import { FileText, Copy, Check, ExternalLink, Bookmark, ShieldCheck } from 'lucide-react';

export interface CitationProps {
  document: string;
  source: string;
  chunk: string;
  score: number;
  page?: number | null;
  line?: number | null;
  chunk_index?: number | null;
  strategy?: string | null;
}

export const CitationCard: React.FC<CitationProps> = ({
  document,
  source,
  chunk,
  score,
  page,
  line,
  chunk_index,
  strategy,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(`[Citation: ${document}] "${chunk}" (Source: ${source})`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Score color grading
  const scorePercent = Math.round(score * 100);
  const scoreColor =
    scorePercent >= 85
      ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30'
      : scorePercent >= 70
      ? 'text-[#00D4FF] bg-[#00D4FF]/10 border-[#00D4FF]/30'
      : 'text-amber-400 bg-amber-400/10 border-amber-400/30';

  const barColor =
    scorePercent >= 85
      ? 'bg-emerald-400'
      : scorePercent >= 70
      ? 'bg-[#00D4FF]'
      : 'bg-amber-400';

  return (
    <div className="p-4 bg-[#0F172A] border border-slate-800 rounded-lg hover:border-slate-700 transition-all space-y-3 group">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1.5 bg-slate-800 rounded text-[#00D4FF] shrink-0">
            <FileText className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-white truncate group-hover:text-[#00D4FF] transition-colors">
              {document}
            </h4>
            <div className="text-[11px] font-mono text-slate-400 truncate flex items-center gap-1.5">
              <span>{source}</span>
              {page !== undefined && page !== null && (
                <>
                  <span aria-hidden="true">·</span>
                  <span>p. {page}</span>
                </>
              )}
              {line !== undefined && line !== null && (
                <>
                  <span aria-hidden="true">·</span>
                  <span>line {line}</span>
                </>
              )}
              {strategy && (
                <>
                  <span aria-hidden="true">·</span>
                  <span className="uppercase text-[10px] text-slate-500">{strategy}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Score Pill */}
        <div className={`px-2.5 py-1 rounded text-xs font-mono font-semibold border shrink-0 ${scoreColor}`}>
          {scorePercent}% MATCH
        </div>
      </div>

      {/* Similarity Bar */}
      <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${Math.min(100, Math.max(5, scorePercent))}%` }}
        />
      </div>

      {/* Excerpt Body */}
      <p className="text-xs text-slate-300 font-mono leading-relaxed bg-[#0A0F1E] p-3 rounded border border-slate-800/60 relative">
        <span className="text-slate-500 select-none">“</span>
        {chunk}
        <span className="text-slate-500 select-none">”</span>
      </p>

      {/* Card Footer Actions */}
      <div className="flex items-center justify-between pt-1 text-[11px] font-mono text-slate-400">
        <div className="flex items-center gap-1.5 text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Ground-truth citation · Zero fabrication</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
          title="Copy citation excerpt"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
