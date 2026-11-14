import React, { useState, useEffect } from 'react';
import { ExecutionItem, ExecutionStatusType } from '../../types';
import { listExecutions } from '../../lib/api/executions';
import { EmptyState } from '../EmptyState';
import { BengaliOutputCard } from './BengaliOutputCard';
import { findAgentBengaliProfile, resolveBengaliReport } from '../../data/bengaliAgents';
import { 
  PlayCircle, 
  RotateCw, 
  Filter, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Loader2,
  Terminal,
  Calendar
} from 'lucide-react';

interface ExecutionsViewProps {
  onNavigateToAgents?: () => void;
}

export const ExecutionsView: React.FC<ExecutionsViewProps> = ({ onNavigateToAgents }) => {
  const [executions, setExecutions] = useState<ExecutionItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [selectedItem, setSelectedItem] = useState<ExecutionItem | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    const filter = statusFilter === 'All' ? undefined : (statusFilter as ExecutionStatusType);
    const res = await listExecutions(undefined, filter, 1, 30);
    if (res.data?.items) {
      setExecutions(res.data.items);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const getStatusBadge = (status: ExecutionStatusType) => {
    switch (status) {
      case 'Completed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-600/30 rounded">
            <CheckCircle2 className="w-3 h-3" />
            <span>Completed</span>
          </span>
        );
      case 'Running':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono text-[#00D4FF] bg-[#00D4FF]/10 border border-[#00D4FF]/30 rounded">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>Running</span>
          </span>
        );
      case 'Pending':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono text-amber-400 bg-amber-950/40 border border-amber-600/30 rounded">
            <Clock className="w-3 h-3" />
            <span>Pending</span>
          </span>
        );
      case 'Failed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono text-rose-400 bg-rose-950/40 border border-rose-600/30 rounded">
            <XCircle className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      case 'Cancelled':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono text-slate-400 bg-slate-900 border border-slate-700 rounded">
            <span>Cancelled</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span className="text-[#00D4FF]">RUNTIME TELEMETRY</span>
            <span aria-hidden="true">·</span>
            <span>TASK EXECUTION LOGS</span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Execution History
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real-time audit log of agent runs, permission scopes, and verified simulated outputs.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="px-3 py-1.5 text-xs font-mono text-slate-300 hover:text-white bg-[#0F172A] border border-slate-800 hover:border-slate-700 rounded flex items-center gap-1.5 transition-colors self-start sm:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Honest Warning Banner */}
      <div className="p-3 bg-amber-950/30 border border-amber-700/40 rounded text-xs font-mono text-amber-300 flex items-center gap-2.5">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong>Phase 03 Strict Protocol:</strong> All executions are strictly labeled ⚠️ Simulated. No external LLM token calls are made until Phase 07.
        </span>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1 p-1 bg-[#0F172A] border border-slate-800 rounded-md">
        {['All', 'Completed', 'Running', 'Pending', 'Failed', 'Cancelled'].map((f) => (
          <button
            key={f}
            onClick={() => setStatusFilter(f)}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              statusFilter === f
                ? 'bg-[#162036] text-[#00D4FF] border border-[#00D4FF]/30 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Table */}
      {executions.length > 0 ? (
        <div className="bg-[#0F172A] border border-slate-800 rounded-lg overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0A0F1E] border-b border-slate-800 text-slate-400 uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">Agent</th>
                <th className="py-3 px-4">Instruction</th>
                <th className="py-3 px-4">Scope</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Mode</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {executions.map((item) => (
                <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-200 whitespace-nowrap">
                    {item.agent_slug}
                  </td>
                  <td className="py-3 px-4 text-slate-300 max-w-xs truncate">
                    {item.instruction}
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    <span className="px-1.5 py-0.5 bg-slate-900 border border-slate-800 rounded text-[10px]">
                      {item.scope}
                    </span>
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    {getStatusBadge(item.status)}
                  </td>
                  <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                    {item.duration_ms ? `${item.duration_ms} ms` : '—'}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    {!item.simulated ? (
                      <span className="text-[10px] text-emerald-300 bg-emerald-950/40 border border-emerald-600/30 px-1.5 py-0.5 rounded">
                        ✓ Real Tool
                      </span>
                    ) : (
                      <span className="text-[10px] text-amber-300 bg-amber-950/40 border border-amber-600/30 px-1.5 py-0.5 rounded">
                        ⚠️ Simulated
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                    {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={() => setSelectedItem(item)}
                      className="text-xs text-[#00D4FF] hover:underline"
                    >
                      View Output
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          icon={PlayCircle}
          title="No Executions Recorded"
          description="No tasks have been submitted yet in this session. Configure an agent to 'Available' in the Agent Registry and run a task to observe the complete execution lifecycle."
          phaseNote="Database Execution Tracking Active"
        />
      )}

      {/* Details Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-[#0F172A] border border-slate-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Terminal className="w-4 h-4 text-[#00D4FF]" />
                <span>
                  {findAgentBengaliProfile(selectedItem.agent_slug).bengaliName} [{selectedItem.agent_slug}]
                </span>
              </h3>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-slate-400 hover:text-white px-2 py-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase mb-1">নির্দেশনা:</span>
                <p className="p-2.5 bg-[#0A0F1E] border border-slate-800 rounded text-slate-300">
                  {selectedItem.instruction}
                </p>
              </div>

              <BengaliOutputCard
                report={resolveBengaliReport(selectedItem)}
                rawOutput={selectedItem.output}
                errorMessage={selectedItem.error_message}
                durationMs={selectedItem.duration_ms}
                simulated={selectedItem.simulated}
              />

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-slate-800">
                <div>
                  <span className="text-slate-500">Status: </span>
                  <span className="text-white">{selectedItem.status}</span>
                </div>
                <div>
                  <span className="text-slate-500">Task ID: </span>
                  <span className="text-slate-400">{selectedItem.task_id.slice(0, 8)}...</span>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 text-xs font-mono text-[#0A0F1E] font-semibold bg-[#00D4FF] hover:bg-[#38bdf8] rounded"
              >
                বন্ধ করুন
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
