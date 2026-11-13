import React, { useState } from 'react';
import { 
  ShieldAlert, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  CheckCircle2, 
  AlertTriangle, 
  Info,
  Lock
} from 'lucide-react';

export interface SecurityFindingData {
  rule_id: string;
  severity: string;
  file: string;
  line: number;
  title: string;
  snippet: string;
  fix: string;
  cwe: string;
}

interface SecurityFindingCardProps {
  finding: SecurityFindingData;
  onMarkReviewed?: (ruleId: string, line: number) => void;
  isReviewed?: boolean;
}

export const SecurityFindingCard: React.FC<SecurityFindingCardProps> = ({
  finding,
  onMarkReviewed,
  isReviewed = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getSeverityStyle = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'high':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'medium':
        return 'bg-yellow-500/10 text-yellow-300 border-yellow-500/30';
      case 'low':
        return 'bg-blue-500/10 text-blue-300 border-blue-500/30';
      default:
        return 'bg-slate-500/10 text-slate-300 border-slate-500/30';
    }
  };

  const getSeverityIcon = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
      case 'high':
        return <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-blue-400 shrink-0" />;
    }
  };

  const cweNumber = finding.cwe.replace(/^CWE-/, '');
  const cweUrl = `https://cwe.mitre.org/data/definitions/${cweNumber}.html`;

  return (
    <div className={`p-4 rounded border transition-colors ${
      isReviewed 
        ? 'bg-[#0B132B]/40 border-slate-800/60 opacity-60' 
        : 'bg-[#0F172A] border-slate-800 hover:border-slate-700'
    }`}>
      {/* Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          {getSeverityIcon(finding.severity)}
          <span className="font-mono text-xs font-semibold text-slate-200">
            {finding.rule_id}
          </span>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-medium ${getSeverityStyle(finding.severity)}`}>
            {finding.severity}
          </span>
          {isReviewed && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Reviewed
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* CWE Link */}
          <a
            href={cweUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-[#00D4FF] transition-colors"
          >
            <span>{finding.cwe}</span>
            <ExternalLink className="w-3 h-3" />
          </a>

          {/* Mark Reviewed Action */}
          {onMarkReviewed && !isReviewed && (
            <button
              onClick={() => onMarkReviewed(finding.rule_id, finding.line)}
              className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors font-medium"
            >
              Mark Reviewed
            </button>
          )}
        </div>
      </div>

      {/* Title & File Location */}
      <div className="mb-2">
        <h4 className="text-sm font-medium text-slate-100">{finding.title}</h4>
        <div className="text-xs font-mono text-slate-400 mt-0.5">
          <span className="text-slate-300 font-semibold">{finding.file}</span>
          <span className="text-slate-500"> : Line {finding.line}</span>
        </div>
      </div>

      {/* Masked Code Snippet */}
      <div className="bg-[#0A0F1E] rounded p-2.5 border border-slate-900 font-mono text-xs text-slate-300 overflow-x-auto my-2">
        <code>{finding.snippet}</code>
      </div>

      {/* Expandable Remediation Guidance */}
      <div className="mt-3 pt-2 border-t border-slate-800/80">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center justify-between w-full text-xs font-medium text-[#00D4FF] hover:text-[#00D4FF]/80 transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5" />
            Remediation Guidance
          </span>
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {isExpanded && (
          <div className="mt-2.5 p-3 rounded bg-[#162036]/60 border border-[#00D4FF]/20 text-xs text-slate-200 space-y-2">
            <div className="font-semibold text-slate-100 flex items-center gap-1.5">
              <span>Fix recommendation:</span>
            </div>
            <p className="text-slate-300 leading-relaxed font-mono text-[11px] bg-[#0A0F1E] p-2 rounded border border-slate-800">
              {finding.fix}
            </p>
            <div className="text-[11px] text-amber-300/90 font-mono">
              ⚠️ Note: Security Agent IMPLEMENT scope is locked. Code modifications must be reviewed and tested by human engineer.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
