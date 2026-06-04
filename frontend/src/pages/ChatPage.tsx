import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { api } from "../lib/api";
import { alert, page } from "../lib/theme";
import type { Citation, Meta } from "../lib/types";

export function ChatPage() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"docs" | "tests">("docs");
  const [useRouter, setUseRouter] = useState(true);
  const [sourcePick, setSourcePick] = useState<Record<string, boolean>>({});
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [routerCols, setRouterCols] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [ingestMsg, setIngestMsg] = useState<string | null>(null);
  const [healthCounts, setHealthCounts] = useState<Record<string, number> | null>(null);

  const loadMeta = useCallback(() => {
    api<Meta>("/api/meta").then((m) => {
      setMeta(m);
      const init: Record<string, boolean> = {};
      m.collections.forEach((c) => {
        init[c.id] = true;
      });
      setSourcePick(init);
    });
  }, []);

  const refreshHealth = useCallback(() => {
    api<{ collections: Record<string, number> }>("/api/health")
      .then((h) => setHealthCounts(h.collections))
      .catch(() => setHealthCounts(null));
  }, []);

  useEffect(() => {
    loadMeta();
    refreshHealth();
  }, [loadMeta, refreshHealth]);

  const runIngest = async () => {
    setBusy(true);
    setIngestMsg(null);
    setStatusMsg("Reindexing… Watch the API terminal for progress.");
    try {
      const r = await api<{ indexed_chunks: Record<string, number> }>("/api/ingest", {
        method: "POST",
        body: JSON.stringify({ clear: false, collections: ["all"] }),
      });
      setIngestMsg(JSON.stringify(r.indexed_chunks));
      refreshHealth();
    } catch (e) {
      setIngestMsg((e as Error).message);
    } finally {
      setBusy(false);
      setStatusMsg(null);
    }
  };

  const runQuery = async () => {
    if (!query.trim()) return;
    setBusy(true);
    setAnswer(null);
    setCitations([]);
    setStatusMsg("Working… Routing, retrieving, and generating.");
    try {
      const ids = meta?.collections.map((c) => c.id) ?? [];
      let sources: string[] | null = null;
      if (!useRouter) {
        sources = ids.filter((id) => sourcePick[id]);
        if (sources.length === 0) sources = ids;
      }
      const data = await api<{
        answer: string;
        citations: Citation[];
        router_collections: string[];
      }>("/api/query", {
        method: "POST",
        body: JSON.stringify({ query: query.trim(), mode, sources }),
      });
      setAnswer(data.answer);
      setCitations(data.citations);
      setRouterCols(data.router_collections ?? []);
      refreshHealth();
    } catch (e) {
      setAnswer("Error: " + (e as Error).message);
    } finally {
      setBusy(false);
      setStatusMsg(null);
    }
  };

  const totalChunks = healthCounts && Object.values(healthCounts).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Groq · Qdrant · BGE-M3 · Reranker"
        title="Ask your QA co-pilot"
        subtitle="Query VWO docs, test cases, JIRA notes, and Selenium or Playwright frameworks. The router picks the right collections automatically."
      />

      <p className={page.muted}>
        <Link to="/status" className="ui-link">
          Configure paths on Status
        </Link>
        {" · "}
        <Link to="/explorer" className="ui-link">
          Open RAG Explorer
        </Link>
      </p>

      {healthCounts !== null && (
        <div className={totalChunks === 0 ? alert.warn : alert.ok}>
          <p className="font-semibold">
            {totalChunks === 0
              ? "No data indexed yet — click Reindex all before asking."
              : `Indexed chunks in Qdrant: ${totalChunks}`}
          </p>
          {totalChunks !== 0 && (
            <p className="mt-2 font-mono text-xs opacity-90">
              {Object.entries(healthCounts)
                .map(([k, v]) => `${k}: ${v}`)
                .join(" · ")}
            </p>
          )}
        </div>
      )}

      <div className="ui-card flex flex-wrap gap-6">
        <label className="flex flex-col gap-2">
          <span className={page.label}>Mode</span>
          <select className="ui-select" value={mode} onChange={(e) => setMode(e.target.value as "docs" | "tests")}>
            <option value="docs">Explain product / docs</option>
            <option value="tests">Suggest test change</option>
          </select>
        </label>
        <label className="flex items-center gap-3 pt-6">
          <input
            type="checkbox"
            checked={useRouter}
            onChange={(e) => setUseRouter(e.target.checked)}
            className="h-4 w-4 rounded border-white/20 bg-slate-950 text-violet-600 focus:ring-violet-500/40"
          />
          <span className="text-sm text-slate-300">Let router pick collections (recommended)</span>
        </label>
      </div>

      {!useRouter && meta && (
        <div className="ui-card">
          <p className={page.sectionTitle}>Sources</p>
          <div className="mt-4 flex flex-wrap gap-3">
            {meta.collections.map((c) => (
              <label key={c.id} className="flex cursor-pointer items-center gap-2 rounded-lg border border-white/5 bg-slate-950/50 px-3 py-2">
                <input
                  type="checkbox"
                  checked={sourcePick[c.id] ?? false}
                  onChange={(e) => setSourcePick((s) => ({ ...s, [c.id]: e.target.checked }))}
                  className="h-4 w-4 rounded text-violet-600 focus:ring-violet-500/40"
                />
                <span className="text-sm text-slate-300">{c.label}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="ui-card">
        <textarea
          className="ui-textarea font-sans"
          placeholder="Ask about VWO, tests, Selenium, or Playwright…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="mt-4 flex flex-wrap gap-3">
          <button type="button" disabled={busy} className="ui-btn-primary" onClick={() => runQuery()}>
            Ask
          </button>
          <button type="button" disabled={busy} className="ui-btn-secondary" onClick={() => runIngest()}>
            Reindex all
          </button>
        </div>
        {statusMsg && <p className="mt-3 text-xs text-violet-300">{statusMsg}</p>}
        {ingestMsg && <p className="mt-2 text-xs text-emerald-300">Indexed chunks: {ingestMsg}</p>}
      </div>

      {routerCols.length > 0 && (
        <p className={page.muted}>Router collections: {routerCols.join(", ")}</p>
      )}

      {answer && (
        <section className="ui-card">
          <h2 className="text-xs font-bold uppercase tracking-wider text-violet-400">Answer</h2>
          <div className="mt-3 whitespace-pre-wrap text-base leading-relaxed text-slate-100">{answer}</div>
        </section>
      )}

      {citations.length > 0 && (
        <section className="ui-card">
          <h2 className="text-xs font-bold uppercase tracking-wider text-violet-400">Citations</h2>
          <ul className="mt-4 space-y-4">
            {citations.map((c, i) => (
              <li key={i} className="border-l-2 border-violet-500/60 pl-4">
                <div className={page.muted}>
                  #{i + 1} · {c.collection}
                  {c.path ? ` · ${c.path}` : ""}
                </div>
                <pre className="ui-pre mt-2 max-h-40">{c.text.slice(0, 2000)}</pre>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
