import React from 'react';

interface CoverageBarProps {
  file: string;
  coverage: number;
  uncoveredLines?: number[];
  totalLines?: number;
  coveredLines?: number;
}

export const CoverageBar: React.FC<CoverageBarProps> = ({
  file,
  coverage,
  uncoveredLines = [],
  totalLines,
  coveredLines,
}) => {
  const getBadgeStyle = (pct: number) => {
    if (pct >= 80) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (pct >= 50) return 'bg-yellow-500/10 text-yellow-300 border-yellow-500/30';
    return 'bg-red-500/10 text-red-400 border-red-500/30';
  };

  const getBarColor = (pct: number) => {
    if (pct >= 80) return 'bg-emerald-500';
    if (pct >= 50) return 'bg-yellow-400';
    return 'bg-red-500';
  };

  return (
    <div className="p-3 rounded bg-[#0A0F1E] border border-slate-800/80 hover:border-slate-700 transition-colors">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
        <div className="font-mono text-xs text-slate-200 truncate max-w-md" title={file}>
          {file}
        </div>
        <div className="flex items-center gap-2">
          {totalLines !== undefined && coveredLines !== undefined && (
            <span className="text-[11px] font-mono text-slate-400">
              {coveredLines}/{totalLines} lines
            </span>
          )}
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${getBadgeStyle(coverage)}`}>
            {coverage.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
        <div
          className={`h-full ${getBarColor(coverage)} transition-all duration-500`}
          style={{ width: `${Math.min(100, Math.max(0, coverage))}%` }}
        />
      </div>

      {/* Uncovered Lines Preview (if any) */}
      {uncoveredLines.length > 0 && coverage < 100 && (
        <div className="mt-1.5 text-[10px] font-mono text-slate-500 truncate">
          Uncovered lines:{' '}
          <span className="text-amber-400/90">
            {uncoveredLines.slice(0, 10).join(', ')}
            {uncoveredLines.length > 10 ? ` (+${uncoveredLines.length - 10} more)` : ''}
          </span>
        </div>
      )}
    </div>
  );
};
