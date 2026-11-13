import React from 'react';
import { ShieldCheck, AlertCircle } from 'lucide-react';

interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info?: number;
}

interface SecuritySummaryChartProps {
  counts: SeverityCounts;
  totalScanned: number;
  totalFindings: number;
}

export const SecuritySummaryChart: React.FC<SecuritySummaryChartProps> = ({
  counts,
  totalScanned,
  totalFindings,
}) => {
  const categories = [
    { label: 'Critical', count: counts.critical, color: 'bg-red-500', barBg: 'bg-red-500/20', text: 'text-red-400' },
    { label: 'High', count: counts.high, color: 'bg-amber-500', barBg: 'bg-amber-500/20', text: 'text-amber-400' },
    { label: 'Medium', count: counts.medium, color: 'bg-yellow-400', barBg: 'bg-yellow-400/20', text: 'text-yellow-300' },
    { label: 'Low', count: counts.low, color: 'bg-blue-400', barBg: 'bg-blue-400/20', text: 'text-blue-300' },
  ];

  const maxCount = Math.max(1, ...categories.map(c => c.count));

  return (
    <div className="bg-[#0F172A] p-5 rounded border border-slate-800">
      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="p-3 rounded bg-[#0A0F1E] border border-slate-800/80">
          <div className="text-[11px] font-mono text-slate-400">Total Scanned</div>
          <div className="text-xl font-bold font-mono text-slate-100 mt-1">{totalScanned} files</div>
        </div>
        <div className="p-3 rounded bg-[#0A0F1E] border border-slate-800/80">
          <div className="text-[11px] font-mono text-slate-400">Total Findings</div>
          <div className={`text-xl font-bold font-mono mt-1 ${totalFindings > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {totalFindings}
          </div>
        </div>
        <div className="p-3 rounded bg-[#0A0F1E] border border-slate-800/80">
          <div className="text-[11px] font-mono text-slate-400">Critical / High</div>
          <div className={`text-xl font-bold font-mono mt-1 ${counts.critical + counts.high > 0 ? 'text-red-400' : 'text-slate-300'}`}>
            {counts.critical + counts.high}
          </div>
        </div>
        <div className="p-3 rounded bg-[#0A0F1E] border border-slate-800/80">
          <div className="text-[11px] font-mono text-slate-400">Tool Scope</div>
          <div className="text-sm font-semibold font-mono text-[#00D4FF] mt-1">READ_ONLY / SUGGEST</div>
        </div>
      </div>

      {/* Findings Breakdown by Severity */}
      <div className="space-y-3">
        <div className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>Findings by Severity</span>
          <span className="text-[11px] text-slate-500 font-sans">Offline Pattern Matching</span>
        </div>

        {categories.map((cat) => {
          const percentage = Math.round((cat.count / maxCount) * 100);
          return (
            <div key={cat.label} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className={cat.text}>{cat.label}</span>
                <span className="text-slate-300">{cat.count}</span>
              </div>
              <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                <div
                  className={`h-full ${cat.color} transition-all duration-500`}
                  style={{ width: `${cat.count > 0 ? Math.max(8, percentage) : 0}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Safety Notice */}
      <div className="mt-5 p-3 rounded bg-[#162036]/40 border border-slate-800 text-xs text-slate-400 font-mono flex items-start gap-2">
        <ShieldCheck className="w-4 h-4 text-[#00D4FF] shrink-0 mt-0.5" />
        <p className="text-[11px] leading-relaxed">
          Truthful audit: Hardcoded credentials are automatically masked. Implementation scope is locked to prevent automated code corruptions.
        </p>
      </div>
    </div>
  );
};
