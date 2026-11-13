import React from 'react';
import { DollarSign, BarChart2, TrendingUp, ShieldCheck } from 'lucide-react';

interface UsageSummaryProps {
  totalCost: number;
  totalTokens: number;
  totalRequests: number;
  avgLatency: number;
  costByAgent: { agent_slug: string; cost_usd: number; requests: number; tokens: number }[];
  dailyUsage: { date: string; cost_usd: number; tokens: number; requests: number }[];
}

export const UsageCostChart: React.FC<UsageSummaryProps> = ({
  totalCost,
  totalTokens,
  totalRequests,
  avgLatency,
  costByAgent,
  dailyUsage,
}) => {
  const maxAgentCost = Math.max(0.0001, ...costByAgent.map((a) => a.cost_usd));

  return (
    <div className="space-y-4">
      {/* Top Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded bg-[#0F172A] border border-slate-800">
          <div className="text-[11px] font-mono text-slate-400">Total Month Cost</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            ${totalCost.toFixed(4)}
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-0.5">Real DB accounting</div>
        </div>

        <div className="p-4 rounded bg-[#0F172A] border border-slate-800">
          <div className="text-[11px] font-mono text-slate-400">Total Tokens Processed</div>
          <div className="text-2xl font-bold font-mono text-[#00D4FF] mt-1">
            {totalTokens.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-0.5">Input + Output</div>
        </div>

        <div className="p-4 rounded bg-[#0F172A] border border-slate-800">
          <div className="text-[11px] font-mono text-slate-400">Total Gateway Calls</div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">
            {totalRequests}
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-0.5">Across all models</div>
        </div>

        <div className="p-4 rounded bg-[#0F172A] border border-slate-800">
          <div className="text-[11px] font-mono text-slate-400">Average Latency</div>
          <div className="text-2xl font-bold font-mono text-slate-200 mt-1">
            {avgLatency} ms
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-0.5">Sliding window avg</div>
        </div>
      </div>

      {/* Cost By Agent Breakdown */}
      <div className="p-5 rounded bg-[#0F172A] border border-slate-800 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-[#00D4FF]" />
            <h4 className="text-sm font-semibold text-slate-100 font-display">
              Cost Allocation by Agent
            </h4>
          </div>
          <span className="text-xs font-mono text-slate-400">Real Usage Attribution</span>
        </div>

        {costByAgent.length === 0 ? (
          <div className="p-6 text-center font-mono text-xs text-slate-500">
            No agent completions recorded yet. Execute tasks to view real cost tracking.
          </div>
        ) : (
          <div className="space-y-3 pt-1">
            {costByAgent.map((agent) => {
              const pct = Math.round((agent.cost_usd / maxAgentCost) * 100);
              return (
                <div key={agent.agent_slug} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-300 font-medium">{agent.agent_slug}</span>
                    <span className="text-emerald-400 font-semibold">
                      ${agent.cost_usd.toFixed(4)}{' '}
                      <span className="text-slate-500 text-[10px]">
                        ({agent.tokens.toLocaleString()} tokens • {agent.requests} calls)
                      </span>
                    </span>
                  </div>
                  <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#00D4FF] transition-all duration-500"
                      style={{ width: `${Math.max(6, pct)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
