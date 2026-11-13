import { PortfolioSection } from '../types';

interface SEOConfig {
  title: string;
  description: string;
  canonicalHash: string;
}

const SECTION_SEO: Record<PortfolioSection, SEOConfig> = {
  home: {
    title: 'Rayhan — Applied AI Systems Architect & Engineer',
    description:
      'Architecting Intelligence. Engineering the Future. Explore production AI agents, hybrid RAG systems, architecture case studies, and safe interactive demos.',
    canonicalHash: '#portfolio',
  },
  projects: {
    title: 'Engineering Projects | Rayhan AI Architecture',
    description:
      'Curated public AI systems, hybrid RAG engines, Model Context Protocol tools, and backend APIs engineered for production reliability.',
    canonicalHash: '#portfolio/projects',
  },
  'project-detail': {
    title: 'Project Architecture | Rayhan AI Architecture',
    description:
      'Technical system overview, stack decisions, architectural challenges, and linked case studies.',
    canonicalHash: '#portfolio/projects',
  },
  'case-studies': {
    title: 'Architecture Case Studies | Rayhan AI Architecture',
    description:
      'Detailed production engineering case studies with Mermaid system topologies, trade-offs, and verified benchmark boundaries.',
    canonicalHash: '#portfolio/case-studies',
  },
  'case-study-detail': {
    title: 'Case Study Deep Dive | Rayhan AI Architecture',
    description:
      'Executive summary, architecture topology diagram, implementation journey, and lessons learned.',
    canonicalHash: '#portfolio/case-studies',
  },
  articles: {
    title: 'Technical Articles & Tutorials | Rayhan AI Architecture',
    description:
      'Published deep-dive engineering articles and implementation walkthroughs on applied AI systems and FastAPI infrastructure.',
    canonicalHash: '#portfolio/articles',
  },
  'article-detail': {
    title: 'Technical Article | Rayhan AI Architecture',
    description: 'Published engineering guide from Rayhan AI Engineering Workbench.',
    canonicalHash: '#portfolio/articles',
  },
  demos: {
    title: 'Safe Interactive Demos | Rayhan AI Architecture',
    description:
      'Isolated, read-only sample sandboxes for AST code analysis, static security scanning, and Mermaid architecture generation.',
    canonicalHash: '#portfolio/demos',
  },
  'demo-detail': {
    title: 'Interactive Tool Sandbox | Rayhan AI Architecture',
    description: 'Isolated read-only sample demonstration with zero stored visitor state.',
    canonicalHash: '#portfolio/demos',
  },
  contact: {
    title: 'Contact | Rayhan — Applied AI Systems Architect',
    description:
      'Connect with Rayhan regarding AI systems architecture roles, technical consulting, or engineering collaborations.',
    canonicalHash: '#portfolio/contact',
  },
};

function setMetaTag(selector: string, attr: 'content' | 'href', value: string) {
  const el = document.querySelector(selector);
  if (el) {
    el.setAttribute(attr, value);
  }
}

export function applyPortfolioSEO(section: PortfolioSection, customTitle?: string, customDescription?: string) {
  if (typeof document === 'undefined') return;
  const base = SECTION_SEO[section] || SECTION_SEO.home;
  const title = customTitle ? `${customTitle} | Rayhan AI Architecture` : base.title;
  const description = customDescription || base.description;
  const canonicalUrl = `${window.location.origin}${window.location.pathname}${base.canonicalHash}`;

  document.title = title;
  setMetaTag('meta[name="description"]', 'content', description);
  setMetaTag('meta[property="og:title"]', 'content', title);
  setMetaTag('meta[property="og:description"]', 'content', description);
  setMetaTag('meta[name="twitter:title"]', 'content', title);
  setMetaTag('meta[name="twitter:description"]', 'content', description);

  let canonical = document.querySelector('link[rel="canonical"]');
  if (!canonical) {
    canonical = document.createElement('link');
    canonical.setAttribute('rel', 'canonical');
    document.head.appendChild(canonical);
  }
  canonical.setAttribute('href', canonicalUrl);
}
