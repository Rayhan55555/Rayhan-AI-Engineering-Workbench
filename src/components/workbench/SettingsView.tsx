import React from 'react';
import { RAYHAN_PROFILE } from '../../data/workbenchData';
import { Settings, Shield, Sliders, KeyRound, Monitor } from 'lucide-react';

export const SettingsView: React.FC = () => {
  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span className="text-[#00D4FF]">SYSTEM CONFIG</span>
            <span aria-hidden="true">·</span>
            <span>WORKBENCH PREFERENCES</span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white">
            Workspace Settings
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Environment definitions, architectural constraints, and personal workbench branding.
          </p>
        </div>
      </div>

      {/* Engineer Identity & Brand */}
      <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-white font-mono mb-4 flex items-center gap-2">
          <Monitor className="w-4 h-4 text-[#00D4FF]" />
          <span>Engineer Identity & Positioning</span>
        </h3>

        <div className="space-y-4 text-xs font-mono">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-slate-400 block mb-1">Engineer Name</label>
              <input
                type="text"
                readOnly
                value={RAYHAN_PROFILE.name}
                className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Professional Title</label>
              <input
                type="text"
                readOnly
                value={RAYHAN_PROFILE.title}
                className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-2 text-slate-200"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-slate-400 block mb-1">Personal Brand</label>
              <input
                type="text"
                readOnly
                value={RAYHAN_PROFILE.brand}
                className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Base Location</label>
              <input
                type="text"
                readOnly
                value={RAYHAN_PROFILE.location}
                className="w-full bg-[#0A0F1E] border border-slate-800 rounded px-3 py-2 text-slate-200"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Environment & API Key Posture */}
      <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-white font-mono mb-2 flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-[#00D4FF]" />
          <span>API Key & Execution Security</span>
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          In compliance with security rules, no API secrets are exposed in the client UI.
        </p>

        <div className="p-3 bg-[#0A0F1E] border border-slate-800 rounded text-xs font-mono text-slate-400 space-y-2">
          <div className="flex items-center justify-between">
            <span>GEMINI_API_KEY:</span>
            <span className="text-emerald-400">Configured via Server Proxy Secrets</span>
          </div>
          <div className="flex items-center justify-between">
            <span>RUNTIME_ENVIRONMENT:</span>
            <span className="text-slate-300">Phase 01 UI Shell (Port 3000)</span>
          </div>
          <div className="flex items-center justify-between">
            <span>BACKEND_PERSISTENCE:</span>
            <span className="text-slate-500">Scheduled for Phase 02</span>
          </div>
        </div>
      </div>

      {/* Strict Phase 01 Rules Guardrail */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2 text-slate-200 font-semibold mb-2">
          <Shield className="w-4 h-4 text-[#00D4FF]" />
          <span>Phase 01 Architectural Guardrails</span>
        </div>
        <ul className="space-y-1 text-slate-500 list-disc list-inside">
          <li>Zero fake metrics or simulated benchmark numbers.</li>
          <li>No premature backend deployment before Phase 02.</li>
          <li>All 8 registered agents verified with "Planned" status tags.</li>
          <li>Empty states displayed honestly across all workbench shells.</li>
        </ul>
      </div>
    </div>
  );
};
