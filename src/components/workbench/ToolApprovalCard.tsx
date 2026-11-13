import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle2, XCircle, Clock, AlertTriangle, FileCode2, Terminal } from 'lucide-react';

export interface PendingApproval {
  id: string;
  tool_name: string;
  agent_slug?: string;
  parameters: Record<string, any>;
  preview: Record<string, any>;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  status: string;
  created_at: string;
  expires_at: string;
}

interface Props {
  approval: PendingApproval;
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string, reason?: string) => Promise<void>;
}

export const ToolApprovalCard: React.FC<Props> = ({ approval, onApprove, onReject }) => {
  const [timeLeft, setTimeLeft] = useState<number>(600);
  const [isProcessing, setIsProcessing] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  useEffect(() => {
    const calculateSeconds = () => {
      const exp = new Date(approval.expires_at).getTime();
      const now = Date.now();
      const diff = Math.max(0, Math.floor((exp - now) / 1000));
      setTimeLeft(diff);
    };

    calculateSeconds();
    const interval = setInterval(calculateSeconds, 1000);
    return () => clearInterval(interval);
  }, [approval.expires_at]);

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const timeFormatted = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

  const riskBadgeStyles: Record<string, string> = {
    low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    medium: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    high: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    critical: 'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse',
  };

  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      await onApprove(approval.id);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    setIsProcessing(true);
    try {
      await onReject(approval.id, rejectReason || undefined);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 shadow-lg space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-semibold text-white font-mono">{approval.tool_name}</span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-medium ${riskBadgeStyles[approval.risk_level] || riskBadgeStyles.medium}`}>
                {approval.risk_level} Risk
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Agent: <span className="text-[#00D4FF]">{approval.agent_slug || 'orchestrator'}</span>
            </p>
          </div>
        </div>

        {/* Expiry countdown */}
        <div className="flex items-center gap-1.5 px-3 py-1 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-400">Expires in:</span>
          <span className={`font-semibold ${timeLeft < 120 ? 'text-rose-400' : 'text-slate-200'}`}>
            {timeFormatted}
          </span>
        </div>
      </div>

      {/* Preview Section */}
      <div className="bg-[#0A0F1E] border border-slate-800/80 rounded-md p-3.5 space-y-2">
        <div className="text-xs font-mono text-slate-300 font-medium flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <FileCode2 className="w-4 h-4 text-[#00D4FF]" />
            Action: {approval.preview.action || approval.tool_name}
          </span>
          {approval.preview.target && (
            <span className="text-slate-400 text-[11px] truncate max-w-[280px]">
              {approval.preview.target}
            </span>
          )}
        </div>

        {approval.preview.reason && (
          <p className="text-xs text-slate-400 italic">
            Rationale: "{approval.preview.reason}"
          </p>
        )}

        {/* Diff preview */}
        {approval.preview.diff && (
          <pre className="text-[11px] font-mono bg-black/50 p-2.5 rounded border border-slate-900 overflow-x-auto text-slate-300 max-h-48 scrollbar-thin">
            {approval.preview.diff}
          </pre>
        )}

        {/* Command or Body preview */}
        {approval.preview.command && (
          <div className="flex items-center gap-2 text-xs font-mono bg-black/40 p-2 rounded text-emerald-400">
            <Terminal className="w-3.5 h-3.5 text-slate-500" />
            <span>{approval.preview.command}</span>
          </div>
        )}

        {approval.preview.body_preview && (
          <p className="text-xs text-slate-300 font-mono bg-black/40 p-2 rounded">
            {approval.preview.body_preview}
          </p>
        )}
      </div>

      {/* Reject reason input */}
      {showRejectInput && (
        <div className="space-y-1.5">
          <label className="text-[11px] font-mono text-slate-400">Rejection Reason (optional):</label>
          <input
            type="text"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="e.g., Unsafe parameter format or incorrect branch"
            className="w-full bg-[#0A0F1E] border border-slate-700 rounded px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-rose-500 font-mono"
          />
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-1">
        {!showRejectInput ? (
          <button
            type="button"
            onClick={() => setShowRejectInput(true)}
            disabled={isProcessing}
            className="px-3 py-1.5 text-xs font-mono font-medium text-slate-400 hover:text-rose-400 transition-colors"
          >
            Reject Request
          </button>
        ) : (
          <button
            type="button"
            onClick={handleReject}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-500/10 border border-rose-500/30 hover:bg-rose-500/20 text-rose-400 rounded text-xs font-mono font-medium transition-colors"
          >
            <XCircle className="w-3.5 h-3.5" />
            Confirm Rejection
          </button>
        )}

        <button
          type="button"
          onClick={handleApprove}
          disabled={isProcessing || timeLeft <= 0}
          className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20 text-emerald-400 rounded text-xs font-mono font-medium transition-colors disabled:opacity-50"
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          {isProcessing ? 'Authorizing...' : 'Authorize & Execute'}
        </button>
      </div>
    </div>
  );
};
