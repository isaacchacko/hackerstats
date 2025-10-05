'use client';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type ResultItem = {
  index: number;
  similarity: number;
  title: string;
  tagline: string;
  url?: string;
  thumbnail?: string;
  hackathon?: string;
  built_with?: string[];
  awards?: string[];
  team_size?: number;
  project_id?: string;
  file_path?: string;
  won?: boolean;
};

export default function BrainstormPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ResultItem[]>([]);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);

  // Tunable thresholds for quick heuristic analysis
  const SIMILARITY_THRESHOLD = 0.27; // how close a match needs to be considered similar
  const OVERDONE_COUNT_THRESHOLD = 4; // number of similar results to flag saturation
  const COMPETITIVE_COUNT_THRESHOLD = 2; // number of winners among similar to flag competitiveness

  const onSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = query.trim();
    if (!text) return;
    setError(null);
    setLoading(true);
    setResults([]);
    setElapsedMs(null);
    const startTime = performance.now();

    try {
      const res = await fetch('/api/brainstorm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, top_k: 10 })
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || 'Request failed');
      }

      const data = await res.json();
      if (!data?.success || !Array.isArray(data.results)) {
        throw new Error('Malformed response');
      }

      setResults(data.results as ResultItem[]);
      const endTime = performance.now();
      setElapsedMs(Math.round(endTime - startTime));
    } catch (err: any) {
      setError(err?.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-slate-100">
      {/* Navigation (mirrors graph page) */}
      <motion.nav
        className="relative z-50 p-6"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <motion.a
            href="/"
            className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400"
            whileHover={{ scale: 1.05 }}
          >
            HackerStats
          </motion.a>

          <div className="flex space-x-6">
            <a href="/graph" className="text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5">Graph</a>
            <a href="/brainstorm" className="text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5">Brainstorm</a>
          </div>
        </div>
      </motion.nav>

      <div className="w-full max-w-5xl mx-auto px-4 pb-16 flex flex-col">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="mb-6 text-center"
        >
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-3">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Brainstorm
            </span>
          </h1>
          <p className="text-xl text-slate-300">
            Enter a prompt to discover similar hackathon projects and inspiration
          </p>
        </motion.div>

        <form onSubmit={onSubmit} className="mb-8">
          <motion.div
            className="relative max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., AI tool to summarize PDFs with a web UI"
              className="w-full h-14 rounded-2xl border border-slate-800 bg-slate-900/80 outline-none focus:border-blue-500/60 px-5 pr-40 text-slate-100 placeholder-slate-500 shadow-inner"
            />
            <motion.button
              type="submit"
              disabled={loading}
              className="absolute right-2 top-2 h-10 px-5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium disabled:opacity-50"
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
            >
              {loading ? 'Searching…' : 'Find similar'}
            </motion.button>
          </motion.div>
        </form>

        {/* General Analysis */}
        {!loading && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="mb-6 rounded-xl border border-slate-800 bg-slate-800/40 p-5"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-white mb-2">General analysis</h2>
                {(() => {
                  const similarAbove = results.filter(r => (r.similarity ?? 0) >= SIMILARITY_THRESHOLD);
                  const winnersAbove = similarAbove.filter(r => r.won || (r.awards ?? []).length > 0);
                  const isOverdone = similarAbove.length >= OVERDONE_COUNT_THRESHOLD;
                  const isVeryCompetitive = winnersAbove.length >= COMPETITIVE_COUNT_THRESHOLD;

                  return (
                    <div className="space-y-2 text-slate-300">
                      <div>
                        <span className="text-slate-400">Similarity threshold</span>: {SIMILARITY_THRESHOLD.toFixed(2)}
                      </div>
                      <div>
                        <span className="text-slate-400">Similar results above threshold</span>: {similarAbove.length}
                        {" "}
                        {isOverdone && (
                          <span className="ml-2 inline-flex items-center gap-1 text-amber-300">
                            <span>⚠️</span>
                            <span>This idea might be overdone</span>
                          </span>
                        )}
                        {!isOverdone && (
                          <span className="ml-2 inline-flex items-center gap-1 text-emerald-300">
                            <span>✅</span>
                            <span>A similar enough project has not been done before!</span>
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="text-slate-400">Winners among those</span>: {winnersAbove.length}
                        {" "}
                        {isVeryCompetitive && (
                          <span className="ml-2 inline-flex items-center gap-1 text-emerald-300">
                            <span>🏆</span>
                            <span>Very competitive space</span>
                          </span>
                        )}
                        {!isVeryCompetitive && (
                          <span className="ml-2 inline-flex items-center gap-1 text-sky-300">
                            <span>💡</span>
                          <span>There haven&#39;t been many winners with this project idea. You could be the first!</span>
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-slate-400 pt-1">
                        Tip: click any result card to open the Devpost project in a new tab.
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          </motion.div>
        )}

        {/* Loading progress indicator */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
            className="mb-6"
          >
            <div className="flex items-center gap-3 text-slate-300 mb-2">
              <div className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
              <span>Fetching Devpost results…</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div className="h-full w-full bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 animate-pulse" />
            </div>
          </motion.div>
        )}

        {/* Results meta line */}
        {!loading && results.length > 0 && (
          <div className="mb-3 text-slate-400 text-sm">
            <span>
              Results fetched{elapsedMs != null ? ` in ${elapsedMs} ms` : ''}
            </span>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          <AnimatePresence>
            {loading && (
              Array.from({ length: 4 }).map((_, i) => (
                <motion.div
                  key={`skeleton-${i}`}
                  className="rounded-xl border border-slate-800 bg-slate-900/50 h-40 animate-pulse"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                />
              ))
            )}

            {!loading && results.map((r, i) => {
              const tech = (r.built_with || []).slice(0, 4).join(', ');
              const awards = (r.awards || []).slice(0, 1).join(' • ');
              const meta = [r.hackathon, tech, awards].filter(Boolean).join('  •  ');
              return (
                <motion.a
                  href={r.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  key={`${r.project_id}-${i}`}
                  className="block rounded-xl border border-slate-800 bg-slate-800/50 backdrop-blur-sm p-5 hover:border-blue-500/50 transition-colors"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, delay: i * 0.03 }}
                >
                  {(r.won || ((r.awards || []).length > 0)) && (
                    <div className="mb-2 -mt-1 text-amber-300 text-sm flex items-center gap-2">
                      <span>🏆</span>
                      <span className="uppercase tracking-wide">Winner</span>
                    </div>
                  )}
                  <div className="flex items-start gap-4">
                    {r.thumbnail && (
                      <div className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border border-slate-700/50 bg-slate-900/40">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={r.thumbnail} alt="thumbnail" className="w-full h-full object-cover" />
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-4">
                        <h3 className="text-lg font-semibold text-white">
                          {i + 1}. {r.title}
                        </h3>
                        <div className="text-xs text-slate-400">
                          {(r.similarity ?? 0).toFixed(3)}
                        </div>
                      </div>
                      {r.tagline && (
                        <p className="text-slate-300 mt-1">“{r.tagline}”</p>
                      )}
                      {meta && (
                        <div className="text-sm text-slate-400 mt-3">{meta}</div>
                      )}
                    </div>
                  </div>
                </motion.a>
              );
            })}
          </AnimatePresence>
        </div>

        {error && (
          <div className="text-sm text-red-400 mt-4 text-center">{error}</div>
        )}
      </div>
    </div>
  );
}
