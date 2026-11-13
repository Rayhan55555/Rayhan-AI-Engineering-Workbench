import React from 'react';
import { FileCode, Plus, Minus, ArrowRight } from 'lucide-react';

interface DiffViewProps {
  diffText: string;
  filePath?: string;
}

export const DiffView: React.FC<DiffViewProps> = ({ diffText, filePath }) => {
  if (!diffText || !diffText.trim()) {
    return (
      <div className="p-4 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono text-slate-500 text-center">
        No file differences detected.
      </div>
    );
  }

  const lines = diffText.split('\n');

  return (
    <div className="bg-[#0A0F1E] border border-slate-800 rounded-lg overflow-hidden font-mono text-xs shadow-inner">
      {/* File Header */}
      {filePath && (
        <div className="px-3.5 py-2 bg-[#0F172A] border-b border-slate-800 flex items-center justify-between text-slate-400">
          <div className="flex items-center gap-2">
            <FileCode className="w-3.5 h-3.5 text-[#00D4FF]" />
            <span className="text-white font-semibold">{filePath}</span>
          </div>
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">
            Unified Diff Patch (SUGGEST scope)
          </span>
        </div>
      )}

      {/* Diff Content */}
      <div className="p-3 overflow-x-auto max-h-80 space-y-0.5 leading-relaxed">
        {lines.map((line, idx) => {
          if (line.startsWith('+++') || line.startsWith('---')) {
            return (
              <div key={idx} className="text-slate-500 font-semibold py-0.5">
                {line}
              </div>
            );
          }
          if (line.startsWith('@@')) {
            return (
              <div key={idx} className="text-cyan-400/80 bg-cyan-950/20 px-2 py-0.5 rounded my-1 text-[11px]">
                {line}
              </div>
            );
          }
          if (line.startsWith('+')) {
            return (
              <div
                key={idx}
                className="flex items-start gap-2 text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded -mx-1"
              >
                <Plus className="w-3 h-3 shrink-0 text-emerald-500 mt-0.5" />
                <span className="whitespace-pre">{line.slice(1)}</span>
              </div>
            );
          }
          if (line.startsWith('-')) {
            return (
              <div
                key={idx}
                className="flex items-start gap-2 text-rose-400 bg-rose-950/30 px-2 py-0.5 rounded -mx-1"
              >
                <Minus className="w-3 h-3 shrink-0 text-rose-500 mt-0.5" />
                <span className="whitespace-pre">{line.slice(1)}</span>
              </div>
            );
          }
          return (
            <div key={idx} className="text-slate-400 px-2 py-0.5 whitespace-pre">
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
};
