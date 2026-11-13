import React, { useEffect, useState } from 'react';
import { AlertTriangle, ArrowLeft, ArrowUpRight, BookOpen, FileText } from 'lucide-react';
import { PublicArticleDTO, PublicCaseStudyDTO } from '../../types';
import {
  fetchPublicArticleBySlug,
  fetchPublicArticles,
  fetchPublicCaseStudies,
  fetchPublicCaseStudyBySlug,
} from '../../lib/api/portfolio';
import { PortfolioMarkdown } from './PortfolioMarkdown';

interface CaseStudiesViewProps {
  selectedSlug?: string;
  onNavigateHash: (hash: string) => void;
}

export const CaseStudiesView: React.FC<CaseStudiesViewProps> = ({
  selectedSlug,
  onNavigateHash,
}) => {
  const [items, setItems] = useState<PublicCaseStudyDTO[]>([]);
  const [detail, setDetail] = useState<PublicCaseStudyDTO | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    if (selectedSlug) {
      fetchPublicCaseStudyBySlug(selectedSlug)
        .then((res) => {
          if (active) setDetail(res);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    } else {
      fetchPublicCaseStudies()
        .then((list) => {
          if (active) setItems(list);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }
    return () => {
      active = false;
    };
  }, [selectedSlug]);

  if (selectedSlug) {
    if (loading) {
      return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16">
          <div className="h-64 bg-[#0F172A] border border-slate-800 rounded-lg animate-pulse" />
        </div>
      );
    }

    if (!detail) {
      return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16 space-y-6">
          <button
            onClick={() => onNavigateHash('#portfolio/case-studies')}
            className="inline-flex items-center gap-2 text-xs font-mono text-[#00D4FF] hover:underline"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Case Studies</span>
          </button>
          <div className="p-8 bg-[#0F172A] border border-slate-800 rounded-lg">
            <h1 className="text-2xl font-bold font-display text-white mb-2">
              Case Study Not Published
            </h1>
            <p className="text-sm text-slate-400">
              Only approved and explicitly published case studies from Content Studio appear publicly.
            </p>
          </div>
        </div>
      );
    }

    return (
      <article className="max-w-4xl mx-auto px-4 sm:px-6 py-14 space-y-8">
        <button
          onClick={() => onNavigateHash('#portfolio/case-studies')}
          className="inline-flex items-center gap-2 text-xs font-mono text-[#00D4FF] hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>All Published Case Studies</span>
        </button>

        <header className="space-y-3 border-b border-slate-800/80 pb-8">
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-400 tabular-nums">
            <span className="text-[#00D4FF]">Architecture Case Study</span>
            <span aria-hidden="true">·</span>
            <span>{detail.reading_time_min} min read</span>
            {detail.published_at && (
              <>
                <span aria-hidden="true">·</span>
                <span>Published {new Date(detail.published_at).toLocaleDateString()}</span>
              </>
            )}
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
            {detail.title}
          </h1>
          <p className="text-base text-slate-300">{detail.summary}</p>
        </header>

        {detail.benchmark_flags.length > 0 && (
          <div className="p-4 bg-[#0F172A] border border-amber-500/30 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300 space-y-1">
              <div className="font-mono font-semibold text-amber-300">
                Verification Notice — Unobserved Benchmarks Marked
              </div>
              <p className="text-slate-400">
                Any quantitative claim without measured production telemetry preserves explicit{' '}
                <code className="font-mono text-amber-300">[BENCHMARK NEEDED]</code> markers rather than fabricated numbers.
              </p>
            </div>
          </div>
        )}

        <PortfolioMarkdown markdown={detail.body_markdown} renderMermaidBlocks />
      </article>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-10">
      <header className="space-y-3 max-w-2xl">
        <div className="text-xs font-mono text-[#00D4FF]">Published Systems Monographs</div>
        <h1 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
          Architecture Case Studies
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Deep architectural retrospectives published directly from the Content Studio review pipeline — including Mermaid topologies and honest benchmark boundaries.
        </p>
      </header>

      {loading ? (
        <div className="h-48 bg-[#0F172A] border border-slate-800 rounded-lg animate-pulse" />
      ) : items.length === 0 ? (
        <div className="p-10 bg-[#0F172A] border border-slate-800 rounded-lg text-center space-y-2">
          <BookOpen className="w-7 h-7 text-slate-500 mx-auto mb-2" />
          <h2 className="text-lg font-semibold text-white font-display">
            No published case studies yet
          </h2>
          <p className="text-sm text-slate-400 max-w-lg mx-auto">
            Draft case studies remain private inside Content Studio until human review and explicit publication approval are completed.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {items.map((cs) => (
            <article
              key={cs.slug}
              className="p-6 bg-[#0F172A] border border-slate-800 hover:border-slate-700 rounded-lg flex flex-col justify-between gap-5"
            >
              <div className="space-y-2.5">
                <div className="text-xs font-mono text-slate-400 tabular-nums">
                  <span className="text-[#00D4FF]">Case Study</span> · {cs.reading_time_min} min read
                </div>
                <h2 className="text-xl font-bold font-display text-white">{cs.title}</h2>
                <p className="text-sm text-slate-300 leading-relaxed">{cs.summary}</p>
              </div>
              <button
                onClick={() => onNavigateHash(`#portfolio/case-studies/${cs.slug}`)}
                className="text-xs font-mono text-[#00D4FF] hover:underline inline-flex items-center gap-1 w-fit"
              >
                <span>Inspect Full Case Study</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

interface ArticlesViewProps {
  selectedSlug?: string;
  onNavigateHash: (hash: string) => void;
}

export const ArticlesView: React.FC<ArticlesViewProps> = ({
  selectedSlug,
  onNavigateHash,
}) => {
  const [articles, setArticles] = useState<PublicArticleDTO[]>([]);
  const [detail, setDetail] = useState<PublicArticleDTO | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    if (selectedSlug) {
      fetchPublicArticleBySlug(selectedSlug)
        .then((res) => {
          if (active) setDetail(res);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    } else {
      fetchPublicArticles()
        .then((list) => {
          if (active) setArticles(list);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }
    return () => {
      active = false;
    };
  }, [selectedSlug]);

  if (selectedSlug) {
    if (loading) {
      return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16">
          <div className="h-64 bg-[#0F172A] border border-slate-800 rounded-lg animate-pulse" />
        </div>
      );
    }
    if (!detail) {
      return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16 space-y-6">
          <button
            onClick={() => onNavigateHash('#portfolio/articles')}
            className="inline-flex items-center gap-2 text-xs font-mono text-[#00D4FF] hover:underline"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Articles</span>
          </button>
          <div className="p-8 bg-[#0F172A] border border-slate-800 rounded-lg">
            <h1 className="text-2xl font-bold font-display text-white mb-2">Article Not Available</h1>
            <p className="text-sm text-slate-400">
              Unpublished drafts are never exposed on the public portfolio surface.
            </p>
          </div>
        </div>
      );
    }

    return (
      <article className="max-w-4xl mx-auto px-4 sm:px-6 py-14 space-y-8">
        <button
          onClick={() => onNavigateHash('#portfolio/articles')}
          className="inline-flex items-center gap-2 text-xs font-mono text-[#00D4FF] hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>All Published Articles</span>
        </button>

        <header className="space-y-3 border-b border-slate-800/80 pb-8">
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-400 tabular-nums">
            <span className="text-[#00D4FF] capitalize">{detail.content_type}</span>
            <span aria-hidden="true">·</span>
            <span>{detail.reading_time_min} min read</span>
            <span aria-hidden="true">·</span>
            <span>{detail.word_count} words</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
            {detail.title}
          </h1>
          <p className="text-base text-slate-300">{detail.summary}</p>
        </header>

        <PortfolioMarkdown markdown={detail.body_markdown} renderMermaidBlocks />
      </article>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-10">
      <header className="space-y-3 max-w-2xl">
        <div className="text-xs font-mono text-[#00D4FF]">Published Engineering Writing</div>
        <h1 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
          Technical Articles &amp; Tutorials
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Verified technical breakdowns and implementation tutorials published through the Content Studio editorial pipeline.
        </p>
      </header>

      {loading ? (
        <div className="h-48 bg-[#0F172A] border border-slate-800 rounded-lg animate-pulse" />
      ) : articles.length === 0 ? (
        <div className="p-10 bg-[#0F172A] border border-slate-800 rounded-lg text-center space-y-2">
          <FileText className="w-7 h-7 text-slate-500 mx-auto mb-2" />
          <h2 className="text-lg font-semibold text-white font-display">
            No published articles yet
          </h2>
          <p className="text-sm text-slate-400 max-w-lg mx-auto">
            Drafts generated in Content Studio stay internal until manually approved and transitioned to Published status.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {articles.map((art) => (
            <article
              key={art.slug}
              className="p-6 bg-[#0F172A] border border-slate-800 hover:border-slate-700 rounded-lg flex flex-col justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="text-xs font-mono text-slate-400 tabular-nums">
                  <span className="text-[#00D4FF] capitalize">{art.content_type}</span> · {art.reading_time_min} min read
                </div>
                <h2 className="text-lg font-bold font-display text-white">{art.title}</h2>
                <p className="text-sm text-slate-300 leading-relaxed">{art.summary}</p>
              </div>
              <button
                onClick={() => onNavigateHash(`#portfolio/articles/${art.slug}`)}
                className="text-xs font-mono text-[#00D4FF] hover:underline inline-flex items-center gap-1 w-fit"
              >
                <span>Read Article</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};
