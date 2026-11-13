import React, { Suspense, lazy, useEffect, useState } from 'react';
import { PortfolioSection, ViewMode, WorkbenchTab } from './types';
import { TopBar } from './components/TopBar';
import { PublicPortfolio } from './components/portfolio/PublicPortfolio';
import { applyPortfolioSEO } from './lib/seo';

// Code-split internal Workbench modules to keep initial Public Portfolio bundle minimal (Phase 13 Performance)
const Sidebar = lazy(() => import('./components/workbench/Sidebar').then((m) => ({ default: m.Sidebar })));
const DashboardView = lazy(() => import('./components/workbench/DashboardView').then((m) => ({ default: m.DashboardView })));
const AgentRegistryView = lazy(() => import('./components/workbench/AgentRegistryView').then((m) => ({ default: m.AgentRegistryView })));
const ProjectsView = lazy(() => import('./components/workbench/ProjectsView').then((m) => ({ default: m.ProjectsView })));
const KnowledgeView = lazy(() => import('./components/workbench/KnowledgeView').then((m) => ({ default: m.KnowledgeView })));
const IntegrationsView = lazy(() => import('./components/workbench/IntegrationsView').then((m) => ({ default: m.IntegrationsView })));
const ContentStudioView = lazy(() => import('./components/workbench/ContentStudioView').then((m) => ({ default: m.ContentStudioView })));
const SettingsView = lazy(() => import('./components/workbench/SettingsView').then((m) => ({ default: m.SettingsView })));
const ExecutionsView = lazy(() => import('./components/workbench/ExecutionsView').then((m) => ({ default: m.ExecutionsView })));
const SecurityView = lazy(() => import('./components/workbench/SecurityView').then((m) => ({ default: m.SecurityView })));
const TestingView = lazy(() => import('./components/workbench/TestingView').then((m) => ({ default: m.TestingView })));
const GatewayView = lazy(() => import('./components/workbench/GatewayView').then((m) => ({ default: m.GatewayView })));
const ArchitectureView = lazy(() => import('./components/workbench/ArchitectureView').then((m) => ({ default: m.ArchitectureView })));
const DocumentationView = lazy(() => import('./components/workbench/DocumentationView').then((m) => ({ default: m.DocumentationView })));
const DevOpsView = lazy(() => import('./components/workbench/DevOpsView').then((m) => ({ default: m.DevOpsView })));

const VALID_WORKBENCH_TABS: WorkbenchTab[] = [
  'dashboard',
  'agents',
  'executions',
  'security',
  'testing',
  'gateway',
  'architecture',
  'documentation',
  'projects',
  'knowledge',
  'integrations',
  'devops',
  'content-studio',
  'settings',
];

function parsePortfolioHash(rawHash: string): { section: PortfolioSection; slug?: string } {
  const parts = rawHash.split('/').filter(Boolean);
  // parts[0] === 'portfolio' or direct top-level aliases
  const sub = parts[0] === 'portfolio' ? parts[1] : parts[0];
  const slug = parts[0] === 'portfolio' ? parts[2] : parts[1];

  if (!sub || sub === 'portfolio' || sub === 'services' || sub === 'featured-project' || sub === 'engineering-stack') {
    return { section: 'home' };
  }
  if (sub === 'projects') {
    return slug ? { section: 'project-detail', slug } : { section: 'projects' };
  }
  if (sub === 'case-studies') {
    return slug ? { section: 'case-study-detail', slug } : { section: 'case-studies' };
  }
  if (sub === 'articles') {
    return slug ? { section: 'article-detail', slug } : { section: 'articles' };
  }
  if (sub === 'demos') {
    return slug ? { section: 'demo-detail', slug } : { section: 'demos' };
  }
  if (sub === 'contact') {
    return { section: 'contact' };
  }
  return { section: 'home' };
}

export default function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('portfolio');
  const [portfolioSection, setPortfolioSection] = useState<PortfolioSection>('home');
  const [portfolioSlug, setPortfolioSlug] = useState<string | undefined>(undefined);
  const [activeWorkbenchTab, setActiveWorkbenchTab] = useState<WorkbenchTab>('dashboard');

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '');
      if (hash.startsWith('workbench')) {
        setViewMode('workbench');
        const parts = hash.split('/');
        if (parts[1]) {
          const tabCandidate = parts[1] as WorkbenchTab;
          if (VALID_WORKBENCH_TABS.includes(tabCandidate)) {
            setActiveWorkbenchTab(tabCandidate);
          }
        }
        return;
      }

      setViewMode('portfolio');
      const parsed = parsePortfolioHash(hash);
      setPortfolioSection(parsed.section);
      setPortfolioSlug(parsed.slug);
      applyPortfolioSEO(parsed.section);
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    if (mode === 'portfolio') {
      window.location.hash = '#portfolio';
    } else {
      window.location.hash = `#workbench/${activeWorkbenchTab}`;
    }
  };

  const handleNavigatePortfolioHash = (hash: string) => {
    setViewMode('portfolio');
    window.location.hash = hash;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleWorkbenchTabChange = (tab: WorkbenchTab) => {
    setActiveWorkbenchTab(tab);
    window.location.hash = `#workbench/${tab}`;
  };

  return (
    <div className="min-h-screen bg-[#0A0F1E] text-slate-100 flex flex-col font-sans">
      <TopBar
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
        portfolioSection={portfolioSection}
        onNavigatePortfolioHash={handleNavigatePortfolioHash}
        activeWorkbenchTab={activeWorkbenchTab}
        onWorkbenchTabChange={handleWorkbenchTabChange}
      />

      {viewMode === 'portfolio' ? (
        <main className="flex-1">
          <PublicPortfolio
            section={portfolioSection}
            slug={portfolioSlug}
            onNavigateHash={handleNavigatePortfolioHash}
            onSwitchToWorkbench={() => handleViewModeChange('workbench')}
          />
        </main>
      ) : (
        <Suspense
          fallback={
            <div className="flex-1 flex items-center justify-center p-12 text-xs font-mono text-slate-400">
              Loading AI Engineering Workbench...
            </div>
          }
        >
          <div className="flex-1 flex flex-col md:flex-row">
            <Sidebar
              activeTab={activeWorkbenchTab}
              onTabChange={handleWorkbenchTabChange}
            />

            <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl overflow-y-auto">
              <div className="mb-6 flex items-center gap-2 text-xs font-mono text-slate-500">
                <span className="text-slate-400">Rayhan AI Workbench</span>
                <span aria-hidden="true">/</span>
                <span className="text-[#00D4FF] uppercase">{activeWorkbenchTab}</span>
              </div>

              {activeWorkbenchTab === 'dashboard' && (
                <DashboardView
                  onTabChange={handleWorkbenchTabChange}
                  onSwitchToPortfolio={() => handleViewModeChange('portfolio')}
                />
              )}
              {activeWorkbenchTab === 'agents' && <AgentRegistryView />}
              {activeWorkbenchTab === 'executions' && (
                <ExecutionsView
                  onNavigateToAgents={() => handleWorkbenchTabChange('agents')}
                />
              )}
              {activeWorkbenchTab === 'security' && <SecurityView />}
              {activeWorkbenchTab === 'testing' && <TestingView />}
              {activeWorkbenchTab === 'gateway' && <GatewayView />}
              {activeWorkbenchTab === 'architecture' && <ArchitectureView />}
              {activeWorkbenchTab === 'documentation' && <DocumentationView />}
              {activeWorkbenchTab === 'projects' && <ProjectsView />}
              {activeWorkbenchTab === 'knowledge' && <KnowledgeView />}
              {activeWorkbenchTab === 'integrations' && <IntegrationsView />}
              {activeWorkbenchTab === 'devops' && <DevOpsView />}
              {activeWorkbenchTab === 'content-studio' && <ContentStudioView />}
              {activeWorkbenchTab === 'settings' && <SettingsView />}
            </main>
          </div>
        </Suspense>
      )}
    </div>
  );
}
