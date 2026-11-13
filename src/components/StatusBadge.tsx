import React from 'react';
import { AgentStatus } from '../types';

interface StatusBadgeProps {
  status: AgentStatus;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  // Anti-slop / Zero-Pill discipline: Clean unboxed or geometric tag with subtle border, no pill capsules
  const getStyle = () => {
    switch (status) {
      case 'Planned':
        return 'text-slate-400 bg-slate-900/60 border-slate-700/60';
      case 'Prototype':
        return 'text-[#00D4FF] bg-[#00D4FF]/10 border-[#00D4FF]/30';
      case 'In Development':
        return 'text-emerald-400 bg-emerald-950/40 border-emerald-600/30';
      case 'Active':
        return 'text-cyan-300 bg-cyan-950/40 border-cyan-500/40';
      default:
        return 'text-slate-400 bg-slate-900/40 border-slate-700';
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-mono tracking-wider uppercase border rounded-sm ${getStyle()} ${className}`}
    >
      <span className="w-1.5 h-1.5 bg-current rounded-xs opacity-75" aria-hidden="true" />
      {status}
    </span>
  );
};
