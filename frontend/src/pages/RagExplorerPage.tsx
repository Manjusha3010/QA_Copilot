import { useCallback, useState } from "react";
import { PageHeader } from "../components/PageHeader";
import { StepCard } from "../components/StepCard";
import { api } from "../lib/api";
import { chunkDisplayId, COLLECTION_PILLS, routerCaption } from "../lib/collections";
import { alert, page } from "../lib/theme";
import type { RagExploreTrace } from "../lib/types";

const DEFAULT_QUERY = "List P0 Blocker test cases for the Admin module";

export function RagExplorerPage() {
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [autoRouter, setAutoRouter] = useState(true);
  const [sourcePick, setSourcePick] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(COLLECTION_PILLS.map((p) => [p.id, true]))
  );
  const [showFilters, setShowFilters] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [trace, setTrace] = useState<RagExploreTrace | null>(null);

  const runTrace = useCallback(async () => {
    if (!query.trim()) return;
    setBusy(true);
    setErr(null);
    setTrace(null);
    try {
      let sources: string[] | null = null;
      if (!autoRouter) {
        sources = COLLECTION_PILLS.filter((p) => sourcePick[p.id]).map((p) => p.id);
        if (sources.length === 0) sources = COLLECTION_PILLS.map((p) => p.id);
      }
      const data = await api<RagExploreTrace>("/api/rag/explore", {
        method: "POST",
        body: JSON.stringify({ query: query.trim(), sources, history: [] }),
      });
      setTrace(data);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [query, autoRouter, sourcePick]);

  const rerankRows = trace?.rerank_scores_table ?? [];
  const sortedRerank = [...rerankRows].sort((a, b) => (b.rerank_score ?? 0) - (a.rerank_score ?? 0));

  return (
    <div className="space-y-6">
      <PageHeader
        badge="RAG Explorer · Debug pipeline"
        title="Inspect the full retrieval pipeline"
        subtitle="Replay a question and see every stage — query rewrite, router, hybrid search, RRF fusion, rerank, LLM context, and the final answer."
      />

      <div className="ui-card">
        <textarea
          className="ui-textarea font-sans"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a question to trace…"
        />
        <div className="mt-5 flex flex-wrap items-start gap-6">
          <button type="button" disabled={busy} onClick={() => runTrace()} className="ui-btn-primary">
            {busy ? "Running…" : "Run trace"}
          </button>
          <div className="min-w-[200px] flex-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-slate-300">Source filter</span>
              <button type="button" className="ui-link" onClick={() => setShowFilters((s) => !s)}>
                {showFilters ? "hide" : "show"}
              </button>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {autoRouter ? "Auto: router decides." : "Manual: selected collections only."}
            </p>
            {showFilters && (
              <div className="mt-3 space-y-2">
                <label className="flex items-center gap-2 text-xs text-slate-300">
                  <input
                    type="checkbox"
                    checked={autoRouter}
                    onChange={(e) => setAutoRouter(e.target.checked)}
                    className="h-4 w-4 rounded text-violet-600 focus:ring-violet-500/40"
                  />
                  Let router pick collections
                </label>
                {!autoRouter && (
                  <div className="flex flex-wrap gap-2">
                    {COLLECTION_PILLS.map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setSourcePick((s) => ({ ...s, [p.id]: !s[p.id] }))}
                        className={sourcePick[p.id] ? "ui-pill-active" : "ui-pill-inactive"}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                )}
                {autoRouter && (
                  <div className="flex flex-wrap gap-2 opacity-70">
                    {COLLECTION_PILLS.map((p) => (
                      <span key={p.id} className="ui-pill-inactive">
                        {p.label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        {err && <p className={`mt-4 ${alert.err}`}>{err}</p>}
      </div>

      {trace && (
        <div className="space-y-3">
          <StepCard step="01" title="Query Rewrite" defaultOpen>
            <p className={page.muted}>Original</p>
            <p className="font-mono text-sm text-white">{trace.query_original}</p>
            <p className={`mt-3 ${page.muted}`}>Rewritten</p>
            <p className="font-mono text-sm text-white">{trace.query_rewritten}</p>
          </StepCard>

          <StepCard step="02" title="Router Decision" defaultOpen>
            <div className="flex flex-wrap gap-2">
              {trace.router_collections.map((c) => (
                <span key={c} className="ui-pill-active font-mono">
                  {c}
                </span>
              ))}
            </div>
            <p className="mt-3 text-sm italic text-slate-400">{routerCaption(trace.router_collections)}</p>
            {trace.router_fallback_all_collections && (
              <p className="mt-2 text-xs text-amber-300">Router JSON parse failed — searched all collections.</p>
            )}
          </StepCard>

          <StepCard step="03" title="Per-Collection Hits (dense / sparse / fused)">
            {Object.entries(trace.per_collection_hits).map(([col, hits]) => (
              <div key={col} className="mb-4 last:mb-0">
                <h4 className="font-mono text-xs font-semibold text-cyan-300">
                  {col} <span className="font-normal text-slate-500">({hits.length} hits)</span>
                </h4>
                <ul className="mt-2 space-y-2">
                  {hits.slice(0, 8).map((h, i) => (
                    <li key={i} className="rounded-xl border border-white/5 bg-slate-950/60 p-3 text-xs">
                      <span className="text-slate-500">
                        #{i + 1} · RRF {h.hybrid_rrf_score?.toFixed(4) ?? "—"}
                        {h.path ? ` · ${h.path}` : ""}
                      </span>
                      <pre className="mt-2 max-h-24 overflow-auto whitespace-pre-wrap text-slate-300">
                        {h.text_preview}
                      </pre>
                    </li>
                  ))}
                  {hits.length > 8 && <li className="text-xs text-slate-500">+ {hits.length - 8} more…</li>}
                </ul>
              </div>
            ))}
          </StepCard>

          <StepCard step="04" title="Rerank (cross-encoder)" defaultOpen>
            <div className="overflow-x-auto rounded-xl border border-white/5">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/10 bg-slate-950/50 text-slate-500">
                    <th className="px-3 py-2">#</th>
                    <th className="px-3 py-2">CHUNK_ID</th>
                    <th className="px-3 py-2">COLLECTION</th>
                    <th className="px-3 py-2">RERANK</th>
                    <th className="px-3 py-2">FUSED →</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedRerank.map((row, i) => (
                    <tr key={i} className="border-b border-white/5">
                      <td className="px-3 py-2 text-slate-400">{i + 1}</td>
                      <td className="px-3 py-2 font-mono text-slate-300">{chunkDisplayId(row.point_id, i)}</td>
                      <td className="px-3 py-2 font-mono text-slate-400">{row.collection}</td>
                      <td className="px-3 py-2 font-mono font-semibold text-violet-300">
                        {(row.rerank_score ?? 0).toFixed(3)}
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-500">
                        {row.hybrid_rrf_score != null ? Math.round(row.hybrid_rrf_score * 100) / 100 : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </StepCard>

          <StepCard step="05" title={`Final Context Blocks (${trace.final_chunks.length})`}>
            {trace.final_chunks.map((h, i) => (
              <div key={i} className="mb-3 rounded-xl border border-white/5 bg-slate-950/60 p-3 last:mb-0">
                <p className={page.muted}>
                  doc #{i + 1} · {h.collection} · rerank {(h.rerank_score ?? 0).toFixed(4)}
                </p>
                <pre className="ui-pre mt-2 max-h-48">{(h.full_text || h.text_preview || "").slice(0, 4000)}</pre>
              </div>
            ))}
          </StepCard>

          <StepCard step="06" title="LLM Call">
            <p className={page.muted}>System</p>
            <pre className="ui-pre mt-2 max-h-40">{trace.prompt_system}</pre>
            <p className={`mt-4 ${page.muted}`}>User prompt (context + question)</p>
            <pre className="ui-pre mt-2 max-h-64">{trace.prompt_user}</pre>
            <p className={`mt-3 ${page.muted}`}>Model: {trace.groq_model}</p>
          </StepCard>

          <StepCard step="07" title="Answer" defaultOpen>
            <pre className="whitespace-pre-wrap rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">
              {trace.answer}
            </pre>
          </StepCard>
        </div>
      )}
    </div>
  );
}
