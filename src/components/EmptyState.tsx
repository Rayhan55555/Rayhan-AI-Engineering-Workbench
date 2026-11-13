import React from 'react';
import { LucideIcon, Layers } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  phaseNote?: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = Layers,
  title,
  description,
  phaseNote = 'Phase 01 Workspace Architecture Shell',
  actionText,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`border border-dashed border-slate-800 bg-[#0F172A]/40 rounded-lg p-8 sm:p-12 text-center max-w-2xl mx-auto flex flex-col items-center justify-center ${className}`}
    >
      <div className="w-12 h-12 rounded-md bg-[#162036] border border-slate-700/60 flex items-center justify-center text-[#00D4FF] mb-4">
        <Icon className="w-6 h-6" />
      </div>

      <h3 className="text-lg font-semibold text-slate-100 font-display mb-2">
        {title}
      </h3>

      <p className="text-sm text-slate-400 max-w-md mx-auto leading-relaxed mb-4">
        {description}
      </p>

      <div className="flex items-center gap-2 text-xs font-mono text-slate-500 mb-6 bg-slate-900/80 px-3 py-1.5 rounded border border-slate-800">
        <span className="text-[#00D4FF]">STATUS:</span>
        <span>{phaseNote}</span>
      </div>

      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 text-xs font-mono font-medium tracking-wide uppercase text-slate-200 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 rounded transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
