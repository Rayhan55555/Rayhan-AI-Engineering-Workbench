import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Activity, Radio, Cpu, CheckCircle2, Wrench, Sparkles, Terminal } from 'lucide-react';

interface StreamEvent {
  id: string;
  type: 'thinking' | 'tool_call' | 'tool_result' | 'llm_start' | 'llm_chunk' | 'complete' | 'error';
  timestamp: string;
  data: any;
}

export const StreamingView: React.FC = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [streamingText, setStreamingText] = useState('');
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [events, streamingText]);

  const startStream = () => {
    setIsStreaming(true);
    setEvents([]);
    setStreamingText('');

    // Connect to live SSE endpoint or fallback simulation
    const eventSource = new EventSource('/api/v1/mcp/stream/demo');

    eventSource.addEventListener('thinking', (e: MessageEvent) => {
      const parsed = JSON.parse(e.data);
      setEvents((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          type: 'thinking',
          timestamp: new Date().toLocaleTimeString(),
          data: parsed,
        },
      ]);
    });

    eventSource.addEventListener('tool_call', (e: MessageEvent) => {
      const parsed = JSON.parse(e.data);
      setEvents((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          type: 'tool_call',
          timestamp: new Date().toLocaleTimeString(),
          data: parsed,
        },
      ]);
    });

    eventSource.addEventListener('tool_result', (e: MessageEvent) => {
      const parsed = JSON.parse(e.data);
      setEvents((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          type: 'tool_result',
          timestamp: new Date().toLocaleTimeString(),
          data: parsed,
        },
      ]);
    });

    eventSource.addEventListener('llm_start', (e: MessageEvent) => {
      const parsed = JSON.parse(e.data);
      setEvents((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          type: 'llm_start',
          timestamp: new Date().toLocaleTimeString(),
          data: parsed,
        },
      ]);
    });

    eventSource.addEventListener('llm_chunk', (e: MessageEvent) => {
      const parsed = JSON.parse(e.data);
      setStreamingText((prev) => prev + (parsed.text || ''));
    });

    eventSource.addEventListener('complete', (e: MessageEvent) => {
      const parsed = JSON.parse(e.data);
      setEvents((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          type: 'complete',
          timestamp: new Date().toLocaleTimeString(),
          data: parsed,
        },
      ]);
      setIsStreaming(false);
      eventSource.close();
    });

    eventSource.onerror = () => {
      setIsStreaming(false);
      eventSource.close();
    };
  };

  const clearStream = () => {
    setEvents([]);
    setStreamingText('');
  };

  return (
    <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <Radio className={`w-4 h-4 ${isStreaming ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
            <h3 className="text-sm font-semibold text-white font-mono">
              Live Event Stream (SSE Transport & WebSockets)
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time streaming channel for multi-step agent reasoning, tool dispatch, and chunked LLM completions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={startStream}
            disabled={isStreaming}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00D4FF]/10 border border-[#00D4FF]/30 hover:bg-[#00D4FF]/20 text-[#00D4FF] rounded text-xs font-mono font-medium transition-colors disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isStreaming ? 'Streaming...' : 'Run Live SSE Stream'}
          </button>
          <button
            type="button"
            onClick={clearStream}
            disabled={isStreaming || events.length === 0}
            className="p-1.5 text-slate-400 hover:text-slate-200 border border-slate-800 rounded bg-[#0A0F1E] disabled:opacity-40"
            title="Clear Stream"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Terminal log output */}
      <div
        ref={logContainerRef}
        className="bg-[#0A0F1E] border border-slate-800/80 rounded-md p-4 font-mono text-xs min-h-[260px] max-h-[420px] overflow-y-auto space-y-2.5 scrollbar-thin"
      >
        {events.length === 0 && !streamingText && (
          <div className="h-44 flex flex-col items-center justify-center text-slate-500 space-y-2">
            <Terminal className="w-6 h-6 text-slate-600" />
            <p>Click "Run Live SSE Stream" to observe real-time tool lifecycle events.</p>
          </div>
        )}

        {events.map((ev) => {
          if (ev.type === 'thinking') {
            return (
              <div key={ev.id} className="flex items-start gap-2 text-cyan-400 bg-cyan-950/20 p-2 rounded border border-cyan-800/30">
                <Cpu className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <div className="space-y-0.5">
                  <span className="text-[10px] text-slate-500 uppercase">{ev.timestamp} · THINKING</span>
                  <p className="text-slate-200">{ev.data.step}</p>
                </div>
              </div>
            );
          }
          if (ev.type === 'tool_call') {
            return (
              <div key={ev.id} className="flex items-start gap-2 text-purple-400 bg-purple-950/20 p-2 rounded border border-purple-800/30">
                <Wrench className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <div className="space-y-0.5">
                  <span className="text-[10px] text-slate-500 uppercase">{ev.timestamp} · DISPATCH TOOL</span>
                  <p className="text-purple-300 font-semibold">{ev.data.tool}</p>
                  <pre className="text-[10px] text-slate-400">{JSON.stringify(ev.data.parameters)}</pre>
                </div>
              </div>
            );
          }
          if (ev.type === 'tool_result') {
            return (
              <div key={ev.id} className="flex items-start gap-2 text-emerald-400 bg-emerald-950/20 p-2 rounded border border-emerald-800/30">
                <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <div className="space-y-0.5">
                  <span className="text-[10px] text-slate-500 uppercase">{ev.timestamp} · TOOL OUTPUT</span>
                  <p className="text-slate-300">{ev.data.summary}</p>
                </div>
              </div>
            );
          }
          if (ev.type === 'llm_start') {
            return (
              <div key={ev.id} className="flex items-center gap-2 text-amber-400 text-[11px] pt-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Synthesis Model: {ev.data.model}</span>
              </div>
            );
          }
          if (ev.type === 'complete') {
            return (
              <div key={ev.id} className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 p-2 rounded border border-emerald-500/30 font-semibold text-xs">
                <CheckCircle2 className="w-4 h-4" />
                <span>Execution finished successfully ({ev.data.total_steps} steps).</span>
              </div>
            );
          }
          return null;
        })}

        {streamingText && (
          <div className="p-3 bg-black/40 border border-slate-800 rounded text-slate-200 whitespace-pre-wrap leading-relaxed">
            {streamingText}
            {isStreaming && <span className="inline-block w-1.5 h-3.5 bg-[#00D4FF] ml-1 animate-pulse" />}
          </div>
        )}
      </div>
    </div>
  );
};
