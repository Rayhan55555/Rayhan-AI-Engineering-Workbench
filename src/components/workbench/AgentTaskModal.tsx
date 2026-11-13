import React, { useState, useEffect } from 'react';
import { Agent, ExecutionItem } from '../../types';
import { submitExecution, getExecutionById, approveExecution, rejectExecution } from '../../lib/api/executions';
import { DiffView } from './DiffView';
import { 
  X, 
  Terminal, 
  Play, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  ShieldAlert,
  Clock,
  Lock,
  FileCode,
  Check,
  Ban,
  Activity
} from 'lucide-react';

interface AgentTaskModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
  onExecutionCompleted?: (item: ExecutionItem) => void;
}

export const AgentTaskModal: React.FC<AgentTaskModalProps> = ({
  agent,
  isOpen,
  onClose,
  onExecutionCompleted,
}) => {
  const isCodingAgent = agent.codename === 'arch-sentinel' || agent.id === 'arch-sentinel';
  const [instruction, setInstruction] = useState('');
  const [filePath, setFilePath] = useState('');
  const [scope, setScope] = useState<'read_only' | 'suggest' | 'implement'>('read_only');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [execution, setExecution] = useState<ExecutionItem | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isApproving, setIsApproving] = useState(false);

  // Reset state when agent changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setInstruction('');
      setFilePath(isCodingAgent ? 'backend/app/main.py' : '');
      setScope('read_only');
      setIsSubmitting(false);
      setExecutionId(null);
      setExecution(null);
      setErrorMsg(null);
      setIsApproving(false);
    }
  }, [isOpen, agent.id, isCodingAgent]);

  // Polling execution status every 2 seconds until terminal status
  useEffect(() => {
    if (!executionId) return;

    let isPolling = true;
    const interval = setInterval(async () => {
      if (!isPolling) return;
      try {
        const res = await getExecutionById(executionId);
        if (res.data) {
          setExecution(res.data);
          if (
            res.data.status === 'Completed' ||
            res.data.status === 'Failed' ||
            res.data.status === 'Cancelled'
          ) {
            clearInterval(interval);
            setIsSubmitting(false);
            if (onExecutionCompleted) {
              onExecutionCompleted(res.data);
            }
          }
        }
      } catch (err) {
        // Continue polling
      }
    }, 2000);

    return () => {
      isPolling = false;
      clearInterval(interval);
    };
  }, [executionId, onExecutionCompleted]);

  if (!isOpen) return null;

  const isAvailable = agent.status === 'Available';
  const charCount = instruction.length;
  const isOverLimit = charCount > 2000;
  const isSubmitDisabled = !isAvailable || charCount < 3 || isOverLimit || isSubmitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitDisabled) return;

    setIsSubmitting(true);
    setErrorMsg(null);

    const contextPayload: Record<string, any> = {};
    if (filePath.trim()) {
      contextPayload.path = filePath.trim();
    }

    const res = await submitExecution(
      agent.codename || agent.id,
      instruction,
      scope,
      undefined,
      contextPayload
    );

    if (res.error) {
      setErrorMsg(res.error.message);
      setIsSubmitting(false);
    } else if (res.data) {
      setExecutionId(res.data.execution_id);
      // Fetch initial state
      const pollRes = await getExecutionById(res.data.execution_id);
      if (pollRes.data) {
        setExecution(pollRes.data);
      }
    }
  };

  const handleApprove = async () => {
    if (!executionId) return;
    setIsApproving(true);
    setErrorMsg(null);
    const res = await approveExecution(executionId, "Approved by engineer via workbench task modal");
    if (res.error) {
      setErrorMsg(res.error.message);
    } else if (res.data) {
      setExecution(res.data);
    }
    setIsApproving(false);
  };

  const handleReject = async () => {
    if (!executionId) return;
    setIsApproving(true);
    setErrorMsg(null);
    const res = await rejectExecution(executionId, "Rejected by engineer via workbench task modal");
    if (res.error) {
      setErrorMsg(res.error.message);
    } else if (res.data) {
      setExecution(res.data);
    }
    setIsApproving(false);
  };

  // Helper to extract diff string if output is JSON with diff
  let diffText: string | null = null;
  let parsedOutputObj: any = null;
  if (execution?.output) {
    try {
      parsedOutputObj = JSON.parse(execution.output);
      if (parsedOutputObj && parsedOutputObj.diff) {
        diffText = parsedOutputObj.diff;
      }
    } catch {
      // Raw string output
    }
  }

  const isPendingApproval = execution?.status === 'Pending' && execution?.scope === 'implement';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
      <div className="bg-[#0F172A] border border-slate-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-[#162036] border border-[#00D4FF]/30 flex items-center justify-center text-[#00D4FF]">
              <Terminal className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-display">
                Run Task: {agent.name}
              </h3>
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                <span>[{agent.codename}]</span>
                <span aria-hidden="true">·</span>
                <span className={isAvailable ? 'text-emerald-400' : 'text-slate-400'}>
                  Status: {agent.status}
                </span>
                {isCodingAgent && (
                  <>
                    <span aria-hidden="true">·</span>
                    <span className="text-[#00D4FF] bg-[#00D4FF]/10 px-1.5 py-0.2 rounded border border-[#00D4FF]/20">
                      Phase 04 Verified
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 sm:p-6 space-y-5 flex-1">
          {/* Availability Notice */}
          {!isAvailable && (
            <div className="p-3 bg-slate-900/80 border border-slate-700/80 rounded text-xs font-mono text-slate-300 flex items-start gap-2.5">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-white block mb-0.5">
                  Agent Not Available for Execution
                </span>
                <span>
                  Current status is '{agent.status}'. An agent must undergo lifecycle configuration and reach 'Available' status before tasks can be executed.
                </span>
              </div>
            </div>
          )}

          {/* Form */}
          {!executionId ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Target File Input (Coding Agent only) */}
              {isCodingAgent && (
                <div>
                  <label className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-1.5 flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5 text-[#00D4FF]" />
                    <span>Target Workspace File (Safe Sandbox):</span>
                  </label>
                  <input
                    type="text"
                    value={filePath}
                    onChange={(e) => setFilePath(e.target.value)}
                    placeholder="e.g. backend/app/main.py or backend/app/schemas/agent.py"
                    className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-[#00D4FF]"
                  />
                  <span className="text-[10px] text-slate-500 font-mono mt-1 block">
                    Path traversal prevention active. Allowed: .py, .ts, .tsx, .json, .md (max 500KB).
                  </span>
                </div>
              )}

              {/* Task Directive */}
              <div>
                <label className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-1.5">
                  Task Instruction (Prompt Directive):
                </label>
                <textarea
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  disabled={!isAvailable || isSubmitting}
                  placeholder={
                    isCodingAgent
                      ? "Enter directive: 'inspect backend/app/main.py', 'suggest improvements for backend/app/schemas/agent.py', or 'run tests backend/tests/test_permissions.py'..."
                      : "Enter task instruction for the agent..."
                  }
                  rows={4}
                  className="w-full bg-[#0A0F1E] border border-slate-800 rounded p-3 text-xs sm:text-sm text-slate-200 font-mono focus:outline-none focus:border-[#00D4FF] focus:ring-1 focus:ring-[#00D4FF] placeholder:text-slate-600 resize-y disabled:opacity-50"
                />
                <div className="flex justify-between items-center text-[11px] font-mono mt-1">
                  <span className="text-slate-500">Max 2,000 characters</span>
                  <span className={isOverLimit ? 'text-rose-400 font-semibold' : 'text-slate-400'}>
                    {charCount} / 2000
                  </span>
                </div>
              </div>

              {/* Scope Selector */}
              <div>
                <label className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-2">
                  Execution Scope & Permissions:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
                  <label
                    className={`p-2.5 border rounded cursor-pointer transition-colors flex flex-col ${
                      scope === 'read_only'
                        ? 'bg-[#162036] border-[#00D4FF]/40 text-slate-200'
                        : 'bg-[#0A0F1E] border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-semibold text-white mb-0.5">
                      <input
                        type="radio"
                        name="scope"
                        value="read_only"
                        checked={scope === 'read_only'}
                        onChange={() => setScope('read_only')}
                        className="text-[#00D4FF]"
                      />
                      <span>read_only</span>
                    </div>
                    <span className="text-[10px] text-slate-500">Inspect & analyze (safe)</span>
                  </label>

                  <label
                    className={`p-2.5 border rounded cursor-pointer transition-colors flex flex-col ${
                      scope === 'suggest'
                        ? 'bg-[#162036] border-[#00D4FF]/40 text-slate-200'
                        : 'bg-[#0A0F1E] border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-semibold text-white mb-0.5">
                      <input
                        type="radio"
                        name="scope"
                        value="suggest"
                        checked={scope === 'suggest'}
                        onChange={() => setScope('suggest')}
                        className="text-[#00D4FF]"
                      />
                      <span>suggest</span>
                    </div>
                    <span className="text-[10px] text-slate-500">Propose diffs (no write)</span>
                  </label>

                  {isCodingAgent ? (
                    <label
                      className={`p-2.5 border rounded cursor-pointer transition-colors flex flex-col ${
                        scope === 'implement'
                          ? 'bg-[#162036] border-amber-500/40 text-slate-200'
                          : 'bg-[#0A0F1E] border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 font-semibold text-white mb-0.5">
                        <input
                          type="radio"
                          name="scope"
                          value="implement"
                          checked={scope === 'implement'}
                          onChange={() => setScope('implement')}
                          className="text-amber-400"
                        />
                        <span className="text-amber-300">implement</span>
                      </div>
                      <span className="text-[10px] text-amber-400/90">Run tests (approval required)</span>
                    </label>
                  ) : (
                    <div className="p-2.5 border border-slate-800/60 bg-[#0A0F1E]/50 rounded text-slate-500 flex flex-col opacity-60 cursor-not-allowed">
                      <div className="flex items-center gap-1.5 font-semibold text-slate-400 mb-0.5">
                        <Lock className="w-3 h-3 text-slate-500" />
                        <span>implement</span>
                      </div>
                      <span className="text-[10px] text-rose-400/80">Phase 05+ Locked</span>
                    </div>
                  )}
                </div>
              </div>

              {errorMsg && (
                <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded text-xs text-rose-300 font-mono flex items-start gap-2">
                  <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Submit Buttons */}
              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-mono text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitDisabled}
                  className="px-5 py-2 text-xs font-mono font-medium text-[#0A0F1E] bg-[#00D4FF] hover:bg-[#38bdf8] disabled:opacity-40 disabled:cursor-not-allowed rounded transition-colors flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" />
                      <span>Execute Task</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          ) : (
            /* Live Execution Progress & Truthful Outputs */
            <div className="space-y-4">
              {/* Truthful Mode Banner */}
              {isCodingAgent ? (
                <div className="p-3 bg-emerald-950/30 border border-emerald-600/40 rounded text-xs font-mono text-emerald-300 flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block text-emerald-200">
                      ✓ REAL TOOL EXECUTION (Phase 04 Verified)
                    </span>
                    <span>
                      Coding Agent executes sandboxed AST analyzers, unified diff engines, and real subprocess test runners (simulated = false).
                    </span>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-amber-950/40 border border-amber-600/40 rounded text-xs font-mono text-amber-300 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block text-amber-200">
                      ⚠️ SIMULATED EXECUTION (Phase 03 Rule)
                    </span>
                    <span>
                      Non-coding agent stub. Real inference activates in its respective scheduled phase.
                    </span>
                  </div>
                </div>
              )}

              {/* Status Header */}
              <div className="p-3 bg-[#0A0F1E] border border-slate-800 rounded flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  {execution?.status === 'Running' ? (
                    <Loader2 className="w-4 h-4 text-[#00D4FF] animate-spin" />
                  ) : isPendingApproval ? (
                    <Clock className="w-4 h-4 text-amber-400 animate-pulse" />
                  ) : execution?.status === 'Completed' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400" />
                  )}
                  <span className="text-slate-300">
                    Status: <strong className="text-white">{execution?.status || 'Pending'}</strong>
                    {isPendingApproval && <span className="text-amber-400 ml-2">(Approval Required)</span>}
                  </span>
                </div>
                {execution?.duration_ms && (
                  <div className="text-slate-400 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>{execution.duration_ms} ms</span>
                  </div>
                )}
              </div>

              {/* Pending Approval Gate UI */}
              {isPendingApproval && (
                <div className="p-4 bg-amber-950/40 border border-amber-600/50 rounded-lg space-y-3 font-mono text-xs">
                  <div className="flex items-center gap-2 text-amber-300 font-semibold">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span>Explicit Execution Approval Gate</span>
                  </div>
                  <p className="text-slate-300 leading-relaxed text-[11px]">
                    This task requires <strong>IMPLEMENT</strong> scope privileges to execute automated test suites. 
                    In accordance with Phase 04 master security rules, execution is paused until you confirm approval.
                  </p>
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      onClick={handleApprove}
                      disabled={isApproving}
                      className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded flex items-center gap-1.5 transition-colors"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>{isApproving ? 'Approving...' : 'Approve & Run Tests'}</span>
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={isApproving}
                      className="px-4 py-1.5 bg-rose-950 hover:bg-rose-900 border border-rose-700/60 text-rose-300 rounded flex items-center gap-1.5 transition-colors"
                    >
                      <Ban className="w-3.5 h-3.5" />
                      <span>Reject Task</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Diff Viewer Component (if unified diff present) */}
              {diffText && (
                <div>
                  <div className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5">
                    Proposed Code Patch (Diff View):
                  </div>
                  <DiffView diffText={diffText} filePath={filePath || parsedOutputObj?.target_file} />
                </div>
              )}

              {/* Execution Output */}
              <div className="space-y-1 text-xs font-mono">
                <div className="text-slate-400 uppercase text-[10px]">Agent Output & Telemetry:</div>
                <div className="p-3 bg-[#0A0F1E] border border-slate-800 rounded text-slate-200 whitespace-pre-wrap leading-relaxed min-h-[90px] max-h-60 overflow-y-auto">
                  {execution?.output || execution?.error_message || (isSubmitting ? 'Processing in background...' : 'No output')}
                </div>
              </div>

              {/* Footer Actions */}
              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setExecutionId(null);
                    setExecution(null);
                  }}
                  className="px-4 py-2 text-xs font-mono text-slate-400 hover:text-white"
                >
                  Run Another Task
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-mono font-medium text-[#0A0F1E] bg-[#00D4FF] hover:bg-[#38bdf8] rounded transition-colors"
                >
                  Done
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
