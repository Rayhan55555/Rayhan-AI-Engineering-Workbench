import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Copy, Check, Download, ZoomIn, ZoomOut, RotateCcw, Code, Eye, AlertCircle } from 'lucide-react';

interface Props {
  code: string;
  title?: string;
}

export const MermaidViewer: React.FC<Props> = ({ code, title }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [viewMode, setViewMode] = useState<'diagram' | 'code'>('diagram');

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        darkMode: true,
        background: '#0A0F1E',
        primaryColor: '#00D4FF',
        primaryTextColor: '#F1F5F9',
        primaryBorderColor: '#00D4FF',
        lineColor: '#64748B',
        secondaryColor: '#1E293B',
        tertiaryColor: '#0F172A',
      },
      fontFamily: 'JetBrains Mono, monospace',
      securityLevel: 'strict',
    });
  }, []);

  useEffect(() => {
    let isMounted = true;
    const renderDiagram = async () => {
      setError(null);
      if (!code.trim()) return;

      try {
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, code);
        // Sanitize SVG output via DOMParser and strip script/event-handler attributes
        const parser = new DOMParser();
        const doc = parser.parseFromString(svg, 'image/svg+xml');
        doc.querySelectorAll('script, foreignObject').forEach((el) => el.remove());
        doc.querySelectorAll('*').forEach((el) => {
          for (const attr of Array.from(el.attributes)) {
            const name = attr.name.toLowerCase();
            const val = attr.value.trim().toLowerCase();
            if (name.startsWith('on') || val.startsWith('javascript:')) {
              el.removeAttribute(attr.name);
            }
          }
        });
        const cleanSvg = doc.documentElement ? doc.documentElement.outerHTML : '';
        if (isMounted) {
          setSvgContent(cleanSvg);
          if (containerRef.current && doc.documentElement) {
            containerRef.current.replaceChildren(document.importNode(doc.documentElement, true));
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err?.message || 'Failed to render Mermaid diagram.');
        }
      }
    };

    renderDiagram();
    return () => {
      isMounted = false;
    };
  }, [code]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadSVG = () => {
    if (!svgContent) return;
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(title || 'diagram').toLowerCase().replace(/\s+/g, '_')}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-[#0F172A] border border-slate-800 rounded-lg overflow-hidden shadow-xl">
      {/* Top Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-4 py-3 border-b border-slate-800 bg-[#0A0F1E]">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold text-white">{title || 'Mermaid Diagram'}</span>
          <span className="text-[10px] font-mono text-[#00D4FF] bg-[#00D4FF]/10 px-2 py-0.5 rounded border border-[#00D4FF]/30">
            MERMAID.JS
          </span>
        </div>

        <div className="flex items-center gap-1.5 font-mono text-xs">
          {/* Zoom Controls */}
          {viewMode === 'diagram' && (
            <div className="flex items-center border border-slate-800 rounded bg-[#0F172A] mr-2">
              <button
                onClick={() => setZoom((z) => Math.max(0.5, z - 0.15))}
                className="p-1.5 text-slate-400 hover:text-white"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="px-2 text-[11px] text-slate-300">{Math.round(zoom * 100)}%</span>
              <button
                onClick={() => setZoom((z) => Math.min(2.0, z + 0.15))}
                className="p-1.5 text-slate-400 hover:text-white"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setZoom(1)}
                className="p-1.5 text-slate-400 hover:text-white border-l border-slate-800"
                title="Reset Zoom"
              >
                <RotateCcw className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* Toggle View Mode */}
          <button
            onClick={() => setViewMode(viewMode === 'diagram' ? 'code' : 'diagram')}
            className="flex items-center gap-1 px-2.5 py-1 text-slate-400 hover:text-white border border-slate-800 rounded bg-[#0F172A]"
          >
            {viewMode === 'diagram' ? (
              <>
                <Code className="w-3.5 h-3.5 text-[#00D4FF]" />
                <span>Code</span>
              </>
            ) : (
              <>
                <Eye className="w-3.5 h-3.5 text-[#00D4FF]" />
                <span>Diagram</span>
              </>
            )}
          </button>

          {/* Copy Code */}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 text-slate-400 hover:text-white border border-slate-800 rounded bg-[#0F172A]"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Download SVG */}
          <button
            onClick={handleDownloadSVG}
            disabled={!svgContent}
            className="flex items-center gap-1 px-2.5 py-1 text-[#00D4FF] bg-[#00D4FF]/10 border border-[#00D4FF]/30 hover:bg-[#00D4FF]/20 rounded disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>SVG</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-4 min-h-[380px] flex items-center justify-center overflow-auto max-h-[620px] bg-[#0A0F1E] relative">
        {error ? (
          <div className="flex flex-col items-center justify-center text-rose-400 space-y-2 p-6 max-w-md text-center">
            <AlertCircle className="w-8 h-8 text-rose-400" />
            <h4 className="text-sm font-semibold font-mono">Mermaid Syntax Warning</h4>
            <p className="text-xs text-slate-400 font-mono">{error}</p>
            <pre className="text-[10px] text-slate-500 bg-black/40 p-2 rounded text-left overflow-x-auto w-full">
              {code}
            </pre>
          </div>
        ) : viewMode === 'diagram' ? (
          <div
            ref={containerRef}
            style={{ transform: `scale(${zoom})`, transformOrigin: 'top center', transition: 'transform 0.15s ease-out' }}
            className="w-full flex justify-center py-2"
          />
        ) : (
          <pre className="w-full h-full text-xs font-mono text-slate-300 p-4 bg-black/50 rounded border border-slate-800/80 overflow-x-auto whitespace-pre leading-relaxed">
            {code}
          </pre>
        )}
      </div>
    </div>
  );
};
