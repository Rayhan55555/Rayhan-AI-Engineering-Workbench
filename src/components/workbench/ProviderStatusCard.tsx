import React from 'react';
import { Cpu, CheckCircle2, AlertTriangle, XCircle, Activity } from 'lucide-react';

export interface ProviderHealthData {
  provider: string;
  status: 'healthy' | 'degraded' | 'down';
  models: string[];
  rate_limit_remaining: number;
  message: string;
  latency_ms?: number | null;
}

interface ProviderStatusCardProps {
  health: ProviderHealthData;
  isPrimary?: boolean;
}

export const ProviderStatusCard: React.FC<ProviderStatusCardProps> = ({ health, isPrimary = false }) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" /> Healthy
          </span>
        );
      case 'degraded':
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
            <AlertTriangle className="w-3 h-3" /> Degraded
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-slate-500/10 text-slate-400 border border-slate-700">
            <XCircle className="w-3 h-3" /> Unconfigured
          </span>
        );
    }
  };

  const displayName = health.provider === 'gemini' ? 'Google Gemini API' : 'Anthropic Claude API';

  return (
    <div className="p-4 rounded bg-[#0F172A] border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-[#00D4FF]" />
          <div>
            <div className="text-sm font-semibold text-slate-100 font-display flex items-center gap-2">
              <span>{displayName}</span>
              {isPrimary ? (
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#00D4FF]/20 text-[#00D4FF] border border-[#00D4FF]/30">
                  Primary
                </span>
              ) : (
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  Fallback
                </span>
              )}
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-0.5">
              Provider ID: {health.provider}
            </div>
          </div>
        </div>

        <div>{getStatusBadge(health.status)}</div>
      </div>

      {/* Latency and Rate Limit Meter */}
      <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/80">
        <div className="p-2 rounded bg-[#0A0F1E] border border-slate-800/80">
          <div className="text-[10px] font-mono text-slate-500">Latency</div>
          <div className="text-xs font-mono font-semibold text-slate-200 mt-0.5 flex items-center gap-1">
            <Activity className="w-3 h-3 text-[#00D4FF]" />
            <span>{health.latency_ms ? `${health.latency_ms} ms` : '—'}</span>
          </div>
        </div>

        <div className="p-2 rounded bg-[#0A0F1E] border border-slate-800/80">
          <div className="text-[10px] font-mono text-slate-500">Rate Limit Remaining</div>
          <div className="text-xs font-mono font-semibold text-[#00D4FF] mt-0.5">
            {health.rate_limit_remaining} RPM
          </div>
        </div>
      </div>

      <div className="text-[11px] font-mono text-slate-400 bg-[#0A0F1E] p-2 rounded border border-slate-900 truncate">
        {health.message}
      </div>
    </div>
  );
};
