import React, { Suspense, lazy } from 'react';

const LazyMermaidViewer = lazy(() =>
  import('../workbench/MermaidViewer').then((m) => ({ default: m.MermaidViewer }))
);

interface PortfolioMarkdownProps {
  markdown: string;
  renderMermaidBlocks?: boolean;
}

type Block =
  | { type: 'heading'; level: number; text: string }
  | { type: 'code'; lang: string; content: string }
  | { type: 'quote'; text: string }
  | { type: 'list'; items: string[] }
  | { type: 'table'; rows: string[][] }
  | { type: 'paragraph'; text: string };

function parseMarkdownBlocks(src: string): Block[] {
  const lines = (src || '').replace(/\r\n/g, '\n').split('\n');
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i += 1;
      continue;
    }

    // Fenced code / mermaid blocks
    if (trimmed.startsWith('```')) {
      const lang = trimmed.slice(3).trim().toLowerCase();
      const buf: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        buf.push(lines[i]);
        i += 1;
      }
      i += 1; // skip closing fence
      blocks.push({ type: 'code', lang, content: buf.join('\n') });
      continue;
    }

    // Headings
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      blocks.push({
        type: 'heading',
        level: headingMatch[1].length,
        text: headingMatch[2].trim(),
      });
      i += 1;
      continue;
    }

    // Blockquotes
    if (trimmed.startsWith('>')) {
      const qLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        qLines.push(lines[i].trim().replace(/^>\s?/, ''));
        i += 1;
      }
      blocks.push({ type: 'quote', text: qLines.join(' ') });
      continue;
    }

    // Markdown table
    if (trimmed.startsWith('|') && i + 1 < lines.length && lines[i + 1].trim().startsWith('|')) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        const rowLine = lines[i].trim();
        if (!/^\|[\s\-:|]+\|$/.test(rowLine)) {
          const cells = rowLine
            .split('|')
            .slice(1, -1)
            .map((c) => c.trim());
          rows.push(cells);
        }
        i += 1;
      }
      if (rows.length > 0) {
        blocks.push({ type: 'table', rows });
      }
      continue;
    }

    // Bullet or numbered lists
    if (/^(?:[-*]|\d+\.)\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^(?:[-*]|\d+\.)\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^(?:[-*]|\d+\.)\s+/, ''));
        i += 1;
      }
      blocks.push({ type: 'list', items });
      continue;
    }

    // Paragraph
    const pLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== '' &&
      !lines[i].trim().startsWith('#') &&
      !lines[i].trim().startsWith('```') &&
      !lines[i].trim().startsWith('>') &&
      !/^(?:[-*]|\d+\.)\s+/.test(lines[i].trim())
    ) {
      pLines.push(lines[i].trim());
      i += 1;
    }
    blocks.push({ type: 'paragraph', text: pLines.join(' ') });
  }

  return blocks;
}

function renderInlineFormatting(text: string): React.ReactNode[] {
  const parts = text.split(/(\[BENCHMARK NEEDED\]|`[^`]+`|\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    if (part === '[BENCHMARK NEEDED]') {
      return (
        <span
          key={idx}
          className="font-mono text-xs text-amber-300 border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 rounded mx-0.5"
        >
          [BENCHMARK NEEDED]
        </span>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={idx} className="font-mono text-xs text-[#00D4FF] bg-[#162036] px-1.5 py-0.5 rounded">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={idx} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

export const PortfolioMarkdown: React.FC<PortfolioMarkdownProps> = ({
  markdown,
  renderMermaidBlocks = true,
}) => {
  const blocks = parseMarkdownBlocks(markdown);

  return (
    <div className="space-y-5 text-slate-300 leading-relaxed max-w-[75ch]">
      {blocks.map((block, idx) => {
        if (block.type === 'heading') {
          if (block.level === 1) {
            return (
              <h2 key={idx} className="text-2xl sm:text-3xl font-bold font-display text-white pt-2">
                {renderInlineFormatting(block.text)}
              </h2>
            );
          }
          if (block.level === 2) {
            return (
              <h3 key={idx} className="text-xl font-bold font-display text-white pt-4 border-t border-slate-800/70">
                {renderInlineFormatting(block.text)}
              </h3>
            );
          }
          return (
            <h4 key={idx} className="text-base font-semibold font-display text-slate-100 pt-2">
              {renderInlineFormatting(block.text)}
            </h4>
          );
        }

        if (block.type === 'quote') {
          return (
            <div
              key={idx}
              className="p-4 bg-[#0F172A] border border-slate-800 rounded text-sm text-slate-300"
            >
              {renderInlineFormatting(block.text)}
            </div>
          );
        }

        if (block.type === 'code') {
          if (renderMermaidBlocks && block.lang === 'mermaid') {
            return (
              <div key={idx} className="my-4">
                <Suspense
                  fallback={
                    <div className="p-6 bg-[#0F172A] border border-slate-800 rounded text-xs font-mono text-slate-400">
                      Loading architecture diagram renderer...
                    </div>
                  }
                >
                  <LazyMermaidViewer code={block.content} title="Architecture Topology" />
                </Suspense>
              </div>
            );
          }
          return (
            <pre
              key={idx}
              className="p-4 bg-[#060913] border border-slate-800 rounded font-mono text-xs text-slate-200 overflow-x-auto leading-relaxed"
            >
              <code>{block.content}</code>
            </pre>
          );
        }

        if (block.type === 'table') {
          const [header, ...bodyRows] = block.rows;
          return (
            <div key={idx} className="overflow-x-auto border border-slate-800 rounded">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0F172A] text-slate-300 border-b border-slate-800">
                  <tr>
                    {header.map((cell, cIdx) => (
                      <th key={cIdx} className="px-4 py-2.5 font-semibold">
                        {cell}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 text-slate-400">
                  {bodyRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-[#0F172A]/60">
                      {row.map((cell, cIdx) => (
                        <td key={cIdx} className="px-4 py-2.5 tabular-nums">
                          {renderInlineFormatting(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }

        if (block.type === 'list') {
          return (
            <ul key={idx} className="space-y-2 pl-4">
              {block.items.map((item, itemIdx) => (
                <li key={itemIdx} className="flex items-start gap-2.5 text-sm sm:text-base text-slate-300">
                  <span className="text-[#00D4FF] font-mono mt-0.5">›</span>
                  <span>{renderInlineFormatting(item)}</span>
                </li>
              ))}
            </ul>
          );
        }

        return (
          <p key={idx} className="text-sm sm:text-base text-slate-300 leading-relaxed">
            {renderInlineFormatting(block.text)}
          </p>
        );
      })}
    </div>
  );
};
