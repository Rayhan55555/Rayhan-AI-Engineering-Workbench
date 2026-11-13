import React from 'react';
import { CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';

export type IngestionStepStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface IngestionStep {
  id: string;
  label: string;
  status: IngestionStepStatus;
  detail?: string;
}

interface IngestionProgressProps {
  steps: IngestionStep[];
  overallStatus: 'idle' | 'running' | 'completed' | 'failed';
  errorMessage?: string | null;
}

export const IngestionProgress: React.FC<IngestionProgressProps> = ({
  steps,
  overallStatus,
  errorMessage,
}) => {
  if (overallStatus === 'idle') return null;

  return (
    <div className="p-4 bg-[#0F172A] border border-slate-800 rounded-lg space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold flex items-center gap-2">
          {overallStatus === 'running' && <Loader2 className="w-3.5 h-3.5 text-[#00D4FF] animate-spin" />}
          {overallStatus === 'completed' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
          {overallStatus === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-rose-400" />}
          <span>Ingestion Pipeline Execution</span>
        </h4>
        <span className="text-[11px] font-mono text-slate-400">
          {overallStatus === 'running' && 'Processing Real Pipeline...'}
          {overallStatus === 'completed' && 'Indexed Successfully'}
          {overallStatus === 'failed' && 'Pipeline Failed'}
        </span>
      </div>

      {/* Steps List */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
        {steps.map((step, idx) => {
          let badge = (
            <div className="flex items-center gap-1.5 text-slate-500">
              <Clock className="w-3 h-3" />
              <span>Pending</span>
            </div>
          );

          let borderColor = 'border-slate-800';
          let textColor = 'text-slate-400';

          if (step.status === 'running') {
            badge = (
              <div className="flex items-center gap-1.5 text-[#00D4FF]">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Active</span>
              </div>
            );
            borderColor = 'border-[#00D4FF]/40 bg-[#00D4FF]/5';
            textColor = 'text-white';
          } else if (step.status === 'completed') {
            badge = (
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="w-3 h-3" />
                <span>Done</span>
              </div>
            );
            borderColor = 'border-emerald-500/30 bg-emerald-500/5';
            textColor = 'text-slate-200';
          } else if (step.status === 'failed') {
            badge = (
              <div className="flex items-center gap-1.5 text-rose-400">
                <AlertCircle className="w-3 h-3" />
                <span>Failed</span>
              </div>
            );
            borderColor = 'border-rose-500/40 bg-rose-500/5';
            textColor = 'text-rose-200';
          }

          return (
            <div
              key={step.id}
              className={`p-2.5 rounded border ${borderColor} transition-all space-y-1`}
            >
              <div className="text-[10px] font-mono text-slate-500">0{idx + 1}. STEP</div>
              <div className={`text-xs font-semibold ${textColor}`}>{step.label}</div>
              <div className="text-[10px] font-mono">{badge}</div>
              {step.detail && (
                <div className="text-[10px] text-slate-500 truncate" title={step.detail}>
                  {step.detail}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {errorMessage && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-xs text-rose-300 font-mono">
          <strong>Pipeline Error:</strong> {errorMessage}
        </div>
      )}
    </div>
  );
};
