import React from 'react';
import { Layers, Zap, DollarSign } from 'lucide-react';

export interface ModelCatalogItem {
  id: string;
  display_name: string;
  provider: string;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
  max_tokens: number;
  capabilities: string[];
  use_case: string;
}

interface ModelCatalogTableProps {
  models: ModelCatalogItem[];
}

export const ModelCatalogTable: React.FC<ModelCatalogTableProps> = ({ models }) => {
  return (
    <div className="rounded border border-slate-800 bg-[#0F172A] overflow-hidden">
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#00D4FF]" />
          <h3 className="text-sm font-semibold text-slate-100 font-display">
            Multi-Model Routing Catalog
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {models.length} Models Configured
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#0A0F1E] text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
            <tr>
              <th className="p-3">Model</th>
              <th className="p-3">Provider</th>
              <th className="p-3">Input Cost / 1K</th>
              <th className="p-3">Output Cost / 1K</th>
              <th className="p-3">Use Case</th>
              <th className="p-3">Router Priority</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {models.map((m) => {
              const isPrimary = m.provider === 'gemini';
              return (
                <tr key={m.id} className="hover:bg-[#162036]/40 transition-colors">
                  <td className="p-3 font-semibold text-slate-200">
                    <div className="flex items-center gap-1.5">
                      <Zap className={`w-3.5 h-3.5 ${isPrimary ? 'text-[#00D4FF]' : 'text-purple-400'}`} />
                      <span>{m.display_name}</span>
                    </div>
                    <div className="text-[10px] text-slate-500">{m.id}</div>
                  </td>
                  <td className="p-3 capitalize">{m.provider}</td>
                  <td className="p-3 text-slate-200">
                    ${m.input_cost_per_1k.toFixed(6)}
                  </td>
                  <td className="p-3 text-slate-200">
                    ${m.output_cost_per_1k.toFixed(6)}
                  </td>
                  <td className="p-3 text-slate-400 max-w-xs truncate" title={m.use_case}>
                    {m.use_case}
                  </td>
                  <td className="p-3">
                    {m.id === 'gemini-1.5-flash' && (
                      <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px]">
                        Primary (Routine)
                      </span>
                    )}
                    {m.id === 'gemini-1.5-pro' && (
                      <span className="px-2 py-0.5 rounded bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 text-[10px]">
                        Primary (Complex)
                      </span>
                    )}
                    {m.id === 'claude-3-5-haiku-20241022' && (
                      <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30 text-[10px]">
                        Fallback (Routine)
                      </span>
                    )}
                    {m.id === 'claude-3-5-sonnet-20241022' && (
                      <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[10px]">
                        Fallback (Complex)
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
