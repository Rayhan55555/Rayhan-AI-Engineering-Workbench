import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Agent, ExecutionItem } from '../../types';
import {
  BENGALI_AGENTS_CATALOG,
  BENGALI_LOADING_MESSAGES,
  resolveBengaliReport,
  toBnDigits,
} from '../../data/bengaliAgents';
import { getAgents, BackendAgent } from '../../lib/api/agents';
import { getAccessToken } from '../../lib/api/client';
import {
  approveExecution,
  getExecutionById,
  rejectExecution,
  submitExecution,
} from '../../lib/api/executions';
import { BengaliOutputCard } from './BengaliOutputCard';
import {
  Ban,
  Bot,
  Check,
  FileCode,
  Loader2,
  Play,
  Search,
  Server,
  ShieldAlert,
  Sparkles,
  XCircle,
} from 'lucide-react';

type WorkScope = 'read_only' | 'suggest' | 'implement';

export const AgentRegistryView: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>(BENGALI_AGENTS_CATALOG);
  const [dataSource, setDataSource] = useState<'Workbench Catalog' | 'Live API Connected'>(
    'Workbench Catalog'
  );
  const [selectedSlug, setSelectedSlug] = useState<string>('arch-sentinel');
  const [instruction, setInstruction] = useState<string>('');
  const [targetFile, setTargetFile] = useState<string>('backend/app/main.py');
  const [scope, setScope] = useState<WorkScope>('read_only');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [loadingPhaseIndex, setLoadingPhaseIndex] = useState<number>(0);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [execution, setExecution] = useState<ExecutionItem | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [authNotice, setAuthNotice] = useState<boolean>(false);
  const [isApproving, setIsApproving] = useState<boolean>(false);

  const runnerRef = useRef<HTMLDivElement>(null);

  // Sync live status overrides from backend while preserving all 9 Bengali persona cards
  useEffect(() => {
    let isMounted = true;
    async function loadBackendAgents() {
      try {
        const res = await getAgents();
        if (isMounted && res.data && res.data.length > 0) {
          const statusMap = new Map<string, BackendAgent>(
            res.data.map((b) => [b.slug.toLowerCase(), b])
          );
          setAgents(
            BENGALI_AGENTS_CATALOG.map((catalogAgent) => {
              const live = statusMap.get(catalogAgent.codename);
              if (!live) return catalogAgent;
              return {
                ...catalogAgent,
                tools: live.allowed_tools?.length ? live.allowed_tools : catalogAgent.tools,
                status: (live.status as Agent['status']) || 'Available',
              };
            })
          );
          setDataSource('Live API Connected');
        }
      } catch {
        // Keep full 9 Bengali catalog cards visible even when backend is disconnected
      }
    }
    loadBackendAgents();
    return () => {
      isMounted = false;
    };
  }, []);

  const selectedAgent = useMemo(
    () =>
      agents.find((a) => a.codename === selectedSlug || a.id === selectedSlug) ||
      agents[0],
    [agents, selectedSlug]
  );

  const filteredAgents = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return agents;
    return agents.filter(
      (a) =>
        (a.bengaliName || '').toLowerCase().includes(q) ||
        (a.bengaliTask || '').toLowerCase().includes(q) ||
        a.name.toLowerCase().includes(q) ||
        a.codename.toLowerCase().includes(q) ||
        (a.whenToUseBn || []).some((w) => w.toLowerCase().includes(q))
    );
  }, [agents, searchQuery]);

  // Cycle phased Bengali loading indicator while active task is running
  useEffect(() => {
    if (!isRunning) return;
    setLoadingPhaseIndex(0);
    const t1 = setTimeout(() => setLoadingPhaseIndex(1), 650);
    const t2 = setTimeout(() => setLoadingPhaseIndex(2), 1450);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [isRunning, executionId]);

  // Poll execution status when backend execution is active
  useEffect(() => {
    if (!executionId) return;

    let active = true;
    const pollInterval = setInterval(async () => {
      if (!active) return;
      const res = await getExecutionById(executionId);
      if (!res.data) return;

      setExecution(res.data);
      const st = res.data.status;
      if (st === 'Completed' || st === 'Failed' || st === 'Cancelled') {
        setLoadingPhaseIndex(3);
        setIsRunning(false);
        clearInterval(pollInterval);
      } else if (st === 'Pending' && res.data.scope === 'implement') {
        // Paused awaiting user approval gate
        setIsRunning(false);
      }
    }, 1500);

    return () => {
      active = false;
      clearInterval(pollInterval);
    };
  }, [executionId]);

  const handleSelectAgent = (agent: Agent) => {
    setSelectedSlug(agent.codename);
    setTargetFile(agent.targetPathDefault || '');
    setErrorMsg(null);
    setAuthNotice(false);
    if (!agent.supportsImplement && scope === 'implement') {
      setScope('suggest');
    }
    runnerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleStartTask = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = instruction.trim();
    if (trimmed.length < 3 || isRunning) return;

    setErrorMsg(null);
    setAuthNotice(false);
    setExecution(null);
    setExecutionId(null);

    if (!getAccessToken()) {
      setAuthNotice(true);
      return;
    }

    setIsRunning(true);
    setLoadingPhaseIndex(0);

    const contextPayload: Record<string, any> = { language: 'bn' };
    if (targetFile.trim()) {
      contextPayload.path = targetFile.trim();
    }

    const res = await submitExecution(
      selectedAgent.codename,
      trimmed,
      scope,
      undefined,
      contextPayload
    );

    if (res.error) {
      setIsRunning(false);
      if (res.error.statusCode === 401) {
        setAuthNotice(true);
      } else {
        setErrorMsg(translateApiErrorBn(res.error.message, res.error.code));
      }
      return;
    }

    if (res.data) {
      setExecutionId(res.data.execution_id);
      const initial = await getExecutionById(res.data.execution_id);
      if (initial.data) {
        setExecution(initial.data);
        if (initial.data.status === 'Pending' && initial.data.scope === 'implement') {
          setIsRunning(false);
        } else if (
          initial.data.status === 'Completed' ||
          initial.data.status === 'Failed'
        ) {
          setLoadingPhaseIndex(3);
          setIsRunning(false);
        }
      }
    }
  };

  const handleApprove = async () => {
    if (!executionId) return;
    setIsApproving(true);
    setErrorMsg(null);
    setIsRunning(true);
    const res = await approveExecution(executionId, 'বাংলা UI থেকে অনুমোদিত');
    if (res.error) {
      setErrorMsg(translateApiErrorBn(res.error.message, res.error.code));
      setIsRunning(false);
    } else if (res.data) {
      setExecution(res.data);
    }
    setIsApproving(false);
  };

  const handleReject = async () => {
    if (!executionId) return;
    setIsApproving(true);
    setErrorMsg(null);
    const res = await rejectExecution(executionId, 'ব্যবহারকারী কাজটি বাতিল করেছেন');
    if (res.error) {
      setErrorMsg(translateApiErrorBn(res.error.message, res.error.code));
    } else if (res.data) {
      setExecution(res.data);
    }
    setIsRunning(false);
    setIsApproving(false);
  };

  const showFileInput =
    selectedAgent.codename === 'arch-sentinel' ||
    selectedAgent.codename === 'testing-agent' ||
    selectedAgent.codename === 'security-agent';

  const isPendingApproval =
    execution?.status === 'Pending' && execution?.scope === 'implement';

  const bengaliReport = useMemo(
    () => (execution ? resolveBengaliReport(execution) : null),
    [execution]
  );

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span className="text-[#00D4FF]">AI AGENT STUDIO</span>
            <span aria-hidden="true">·</span>
            <span>{toBnDigits(agents.length)}টি স্পেশালাইজড এজেন্ট</span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            আপনার AI Engineering সহকারীরা
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            সহজ বাংলায় আপনার কাজটি লিখুন, ধরন বেছে নিন এবং সাথে সাথে বিশ্লেষণ ও পরামর্শ পান।
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-2 bg-[#0F172A] border border-slate-800 rounded text-xs font-mono text-slate-400 self-start sm:self-auto">
          <Server className="w-3.5 h-3.5 text-[#00D4FF]" />
          <span>{dataSource}</span>
        </div>
      </div>

      {/* 3-Step Simple Agent Runner */}
      <section
        ref={runnerRef}
        aria-label="৩ ধাপের Agent কমান্ড রানার"
        className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 sm:p-6 space-y-6"
      >
        {/* Selected Agent Active Strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-md bg-[#162036] border border-[#00D4FF]/30 flex items-center justify-center text-[#00D4FF] shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-lg font-bold text-white">
                  {selectedAgent.bengaliName || selectedAgent.name}
                </h3>
                <span className="text-xs font-mono text-slate-400">
                  [{selectedAgent.codename}]
                </span>
              </div>
              <p className="text-sm text-slate-300 mt-0.5">
                {selectedAgent.bengaliTask || selectedAgent.description}
              </p>
            </div>
          </div>

          <span className="text-xs font-mono text-emerald-400 shrink-0">
            ● {selectedAgent.status === 'Available' ? 'প্রস্তুত' : selectedAgent.status}
          </span>
        </div>

        <form onSubmit={handleStartTask} className="space-y-6">
          {/* STEP 1 BOX */}
          <div className="bg-[#0A0F1E] border border-slate-800 rounded-lg p-4 sm:p-5 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <label
                htmlFor="agent-instruction-input"
                className="text-base font-semibold text-white flex items-center gap-2"
              >
                <span className="text-xs font-mono text-[#00D4FF] uppercase tracking-wider">
                  STEP 1
                </span>
                <span>আপনি কী করতে চান?</span>
              </label>
              <span className="text-xs font-mono text-slate-500 tabular-nums">
                {toBnDigits(instruction.length)} / ২০০০
              </span>
            </div>

            <textarea
              id="agent-instruction-input"
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              rows={4}
              placeholder="যেমন: আমার code-এর security check করো"
              className="w-full bg-[#0F172A] border border-slate-700/80 rounded-md p-3.5 text-sm sm:text-base text-white placeholder:text-slate-500 focus:outline-none focus:border-[#00D4FF] focus:ring-1 focus:ring-[#00D4FF] resize-y leading-relaxed"
            />

            {/* Quick Prompt Suggestions + Optional Target Path */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pt-1">
              {selectedAgent.quickPromptsBn && selectedAgent.quickPromptsBn.length > 0 && (
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-[#00D4FF]" />
                    উদাহরণ:
                  </span>
                  {selectedAgent.quickPromptsBn.map((promptText, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setInstruction(promptText)}
                      className="text-xs px-2.5 py-1.5 rounded bg-[#162036] hover:bg-[#1e2c4a] text-slate-200 border border-slate-700/80 transition-colors text-left"
                    >
                      {promptText}
                    </button>
                  ))}
                </div>
              )}

              {showFileInput && (
                <div className="flex items-center gap-2 shrink-0">
                  <FileCode className="w-4 h-4 text-[#00D4FF] shrink-0" />
                  <input
                    type="text"
                    value={targetFile}
                    onChange={(e) => setTargetFile(e.target.value)}
                    placeholder="ফাইল পথ (যেমন: backend/app/main.py)"
                    className="w-full sm:w-64 bg-[#0F172A] border border-slate-800 rounded px-2.5 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-[#00D4FF]"
                  />
                </div>
              )}
            </div>
          </div>

          {/* STEP 2 BOX */}
          <div className="bg-[#0A0F1E] border border-slate-800 rounded-lg p-4 sm:p-5 space-y-3">
            <div className="text-base font-semibold text-white flex items-center gap-2">
              <span className="text-xs font-mono text-[#00D4FF] uppercase tracking-wider">
                STEP 2
              </span>
              <span>কোন ধরনের কাজ?</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setScope('read_only')}
                className={`min-h-[60px] px-4 py-3 rounded-lg border text-left transition-colors flex flex-col justify-center ${
                  scope === 'read_only'
                    ? 'bg-[#162036] border-[#00D4FF] text-white'
                    : 'bg-[#0F172A] border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <span className="text-sm sm:text-base font-semibold">
                  🔍 শুধু দেখো (Read Only)
                </span>
                <span className="text-xs text-slate-400 mt-0.5">
                  কোনো পরিবর্তন ছাড়া শুধু পরীক্ষা করবে
                </span>
              </button>

              <button
                type="button"
                onClick={() => setScope('suggest')}
                className={`min-h-[60px] px-4 py-3 rounded-lg border text-left transition-colors flex flex-col justify-center ${
                  scope === 'suggest'
                    ? 'bg-[#162036] border-[#00D4FF] text-white'
                    : 'bg-[#0F172A] border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <span className="text-sm sm:text-base font-semibold">
                  💡 পরামর্শ দাও (Suggest)
                </span>
                <span className="text-xs text-slate-400 mt-0.5">
                  সমাধান ও code diff তৈরি করে দেখাবে
                </span>
              </button>

              <button
                type="button"
                onClick={() => setScope('implement')}
                className={`min-h-[60px] px-4 py-3 rounded-lg border text-left transition-colors flex flex-col justify-center ${
                  scope === 'implement'
                    ? 'bg-[#162036] border-amber-400 text-white'
                    : 'bg-[#0F172A] border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <span className="text-sm sm:text-base font-semibold">
                  ⚡ কাজ করো (Implement)
                </span>
                <span className="text-xs text-slate-400 mt-0.5">
                  {selectedAgent.supportsImplement === false
                    ? 'নিরাপত্তার জন্য ম্যানুয়াল রিভিউ প্রযোজ্য'
                    : 'অনুমোদন সাপেক্ষে সরাসরি কার্যকর করবে'}
                </span>
              </button>
            </div>
          </div>

          {/* STEP 3 */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="text-xs text-slate-400">
              নির্বাচিত সহকারী:{' '}
              <strong className="text-white">
                {selectedAgent.bengaliName || selectedAgent.name}
              </strong>
            </div>

            <button
              type="submit"
              disabled={instruction.trim().length < 3 || instruction.length > 2000 || isRunning}
              className="w-full sm:w-auto min-h-[48px] px-8 py-3 rounded-lg bg-[#00D4FF] hover:bg-[#38bdf8] disabled:opacity-45 disabled:cursor-not-allowed text-[#0A0F1E] font-bold text-base transition-colors inline-flex items-center justify-center gap-2.5"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>{BENGALI_LOADING_MESSAGES[loadingPhaseIndex]}</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>কাজ শুরু করো</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Bengali Loading Progress Strip */}
        {isRunning && (
          <div className="p-4 bg-[#0A0F1E] border border-[#00D4FF]/30 rounded-lg space-y-2.5">
            <div className="flex items-center gap-2.5 text-sm font-medium text-[#00D4FF]">
              <Loader2 className="w-4 h-4 animate-spin shrink-0" />
              <span>{BENGALI_LOADING_MESSAGES[loadingPhaseIndex]}</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              {BENGALI_LOADING_MESSAGES.map((msg, i) => (
                <div
                  key={msg}
                  className={`px-2.5 py-1.5 rounded border ${
                    i <= loadingPhaseIndex
                      ? 'bg-[#162036] border-[#00D4FF]/40 text-slate-100'
                      : 'bg-[#0F172A] border-slate-800 text-slate-500'
                  }`}
                >
                  {msg}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Auth Required Honest Notice */}
        {authNotice && (
          <div className="p-4 bg-amber-950/30 border border-amber-700/50 rounded-lg text-sm text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-white">
                  বাস্তব Agent চালানোর জন্য আগে লগইন প্রয়োজন
                </div>
                <p className="text-xs sm:text-sm text-amber-200/80 mt-0.5">
                  কোনো ভুয়া ফলাফল দেখানো হয় না। Settings-এ গিয়ে আপনার একাউন্ট দিয়ে লগইন করলে এই Agent সরাসরি সার্ভারের মাধ্যমে কাজ করবে।
                </p>
              </div>
            </div>
            <a
              href="#workbench/settings"
              className="px-4 py-2 bg-[#00D4FF] hover:bg-[#38bdf8] text-[#0A0F1E] font-semibold text-xs rounded shrink-0 text-center"
            >
              Settings-এ লগইন করুন
            </a>
          </div>
        )}

        {/* Error Box */}
        {errorMsg && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-lg text-sm text-rose-200 flex items-start gap-2.5">
            <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Pending Approval Gate */}
        {isPendingApproval && (
          <div className="p-4 bg-amber-950/35 border border-amber-600/50 rounded-lg space-y-3">
            <div className="flex items-center gap-2 text-amber-300 font-semibold text-sm">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>কাজ শুরু করার আগে আপনার অনুমোদন প্রয়োজন</span>
            </div>
            <p className="text-sm text-slate-300">
              আপনি <strong>⚡ কাজ করো (Implement)</strong> মোড বেছে নিয়েছেন। নিরাপত্তা নিশ্চিত করতে আপনার অনুমতি ছাড়া সিস্টেম কোনো পরিবর্তন চালাবে না।
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleApprove}
                disabled={isApproving}
                className="min-h-[44px] px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm rounded inline-flex items-center gap-1.5 transition-colors"
              >
                <Check className="w-4 h-4" />
                <span>{isApproving ? 'অনুমোদন হচ্ছে...' : 'অনুমোদন দিন এবং চালান'}</span>
              </button>
              <button
                type="button"
                onClick={handleReject}
                disabled={isApproving}
                className="min-h-[44px] px-4 py-2 bg-rose-950 hover:bg-rose-900 border border-rose-700/60 text-rose-200 text-sm rounded inline-flex items-center gap-1.5 transition-colors"
              >
                <Ban className="w-4 h-4" />
                <span>বাতিল করুন</span>
              </button>
            </div>
          </div>
        )}

        {/* Completed 4-Part Bengali Result Card */}
        {execution && bengaliReport && !isRunning && (
          <BengaliOutputCard
            report={bengaliReport}
            rawOutput={execution.output}
            errorMessage={execution.error_message}
            durationMs={execution.duration_ms}
            simulated={execution.simulated}
            defaultFilePath={targetFile}
          />
        )}
      </section>

      {/* 9 Bengali Agent Persona Cards Directory */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-xl font-bold font-display text-white">
              সবগুলো AI সহকারী ({toBnDigits(filteredAgents.length)}টি)
            </h3>
            <p className="text-xs sm:text-sm text-slate-400">
              যেকোনো কার্ডে ক্লিক করে উপরের সহজ ৩ ধাপের বক্সে ওই এজেন্টটি চালু করুন।
            </p>
          </div>

          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="এজেন্ট খুঁজুন (যেমন: নিরাপত্তা, RAG)..."
              className="w-full bg-[#0F172A] border border-slate-800 text-sm text-slate-200 pl-9 pr-3 py-2 rounded focus:outline-none focus:border-[#00D4FF] placeholder:text-slate-600"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filteredAgents.map((agent) => {
            const isSelected = agent.codename === selectedAgent.codename;
            return (
              <div
                key={agent.codename}
                className={`bg-[#0F172A] rounded-lg p-5 flex flex-col justify-between transition-colors border ${
                  isSelected
                    ? 'border-[#00D4FF] bg-[#162036]/60'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="space-y-3">
                  {/* Uncluttered Header Metadata */}
                  <div className="flex items-center justify-between gap-2 text-xs font-mono text-slate-400">
                    <span className="text-[#00D4FF] truncate">{agent.name}</span>
                    <span className="text-slate-500 shrink-0">[{agent.codename}]</span>
                  </div>

                  {/* নাম & কাজ */}
                  <div>
                    <h4 className="text-lg font-bold text-white font-display">
                      {agent.bengaliName || agent.name}
                    </h4>
                    <p className="text-sm text-slate-300 mt-1.5 leading-relaxed">
                      <span className="text-slate-400 font-medium">কাজ: </span>
                      {agent.bengaliTask || agent.description}
                    </p>
                  </div>

                  {/* ব্যবহার করুন যখন */}
                  {agent.whenToUseBn && agent.whenToUseBn.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80">
                      <div className="text-xs font-semibold text-slate-400 mb-1.5">
                        ব্যবহার করুন যখন:
                      </div>
                      <ul className="space-y-1 text-sm text-slate-300">
                        {agent.whenToUseBn.map((useCase, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-[#00D4FF] shrink-0">→</span>
                            <span>{useCase}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Card Select Action */}
                <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  <span className="text-[11px] font-mono text-slate-500 truncate">
                    {agent.tools.slice(0, 2).join(' · ')}
                  </span>

                  <button
                    type="button"
                    onClick={() => handleSelectAgent(agent)}
                    className={`min-h-[44px] px-4 py-2 rounded text-xs sm:text-sm font-semibold transition-colors shrink-0 ${
                      isSelected
                        ? 'bg-[#00D4FF] text-[#0A0F1E]'
                        : 'bg-[#162036] text-slate-100 border border-slate-700 hover:border-[#00D4FF]/60'
                    }`}
                  >
                    {isSelected ? '✓ নির্বাচিত' : 'ব্যবহার করুন'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};

function translateApiErrorBn(message: string, code: string): string {
  const lower = (message || '').toLowerCase();
  if (code === 'network_error') {
    return 'Backend সার্ভারের সাথে সংযোগ স্থাপন করা যায়নি। অনুগ্রহ করে সার্ভার চালু আছে কি না পরীক্ষা করুন।';
  }
  if (lower.includes('implement')) {
    return 'এই এজেন্টের জন্য সরাসরি Implement অনুমতি সক্রিয় নয়। অনুগ্রহ করে "🔍 শুধু দেখো" অথবা "💡 পরামর্শ দাও" ব্যবহার করুন।';
  }
  if (lower.includes('not available') || lower.includes('planned')) {
    return 'এই এজেন্টটি বর্তমানে "Planned" অবস্থায় আছে।';
  }
  return `সমস্যা হয়েছে: ${message}`;
}
