import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { PathsForm } from "../components/PathsForm";
import { SetupSummary } from "../components/SetupSummary";
import { api } from "../lib/api";
import { pathsFromMeta, saveDataPaths, type DataPaths } from "../lib/paths";
import { alert, page } from "../lib/theme";
import type { Meta } from "../lib/types";

const emptyPaths: DataPaths = {
  pdfs: "",
  markdown: "",
  selenium: "",
  playwright: "",
  vwo_tests: "",
};

export function StatusPage() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [health, setHealth] = useState<{
    version?: string;
    collections: Record<string, number>;
  } | null>(null);
  const [paths, setPaths] = useState<DataPaths>(emptyPaths);
  const [err, setErr] = useState<string | null>(null);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const refresh = useCallback(() => {
    setErr(null);
    Promise.all([
      api<Meta>("/api/meta"),
      api<{ version?: string; collections: Record<string, number> }>("/api/health"),
    ])
      .then(([m, h]) => {
        setMeta(m);
        setHealth(h);
        setPaths(pathsFromMeta(m));
      })
      .catch((e: Error) => setErr(e.message));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const onSavePaths = async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      await saveDataPaths(paths);
      setSaveMsg("Paths saved to local_paths.json.");
      refresh();
    } catch (e) {
      setSaveMsg("Error: " + (e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const total = health ? Object.values(health.collections).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        badge="System · Paths · Qdrant"
        title="System status"
        subtitle="Setup summary, editable data paths, and collection health. Configure folders here — Chat opens on startup."
      />

      {err && <p className={alert.err}>Could not reach API: {err}</p>}

      <section className="ui-card">
        <h2 className={page.sectionTitle}>Setup summary</h2>
        <p className={page.sectionHint}>Stack and collections are fixed for v1. Edit paths below and save.</p>
        <div className="mt-4">
          <SetupSummary meta={meta} />
        </div>
      </section>

      <section className="ui-card">
        <h2 className={page.sectionTitle}>Data paths</h2>
        <p className={page.sectionHint}>
          Saves to <code className={page.code}>local_paths.json</code> via the API.
        </p>
        <div className="mt-4">
          <PathsForm paths={paths} setPaths={setPaths} />
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button type="button" disabled={saving} className="ui-btn-primary" onClick={() => onSavePaths()}>
            {saving ? "Saving…" : "Save paths"}
          </button>
          {saveMsg && (
            <p className={`text-sm ${saveMsg.startsWith("Error") ? "text-rose-400" : "text-emerald-300"}`}>
              {saveMsg}
            </p>
          )}
        </div>
      </section>

      <section className="ui-card">
        <div className="flex items-center justify-between">
          <h2 className={page.sectionTitle}>Qdrant collections</h2>
          <button type="button" className="ui-link text-sm" onClick={refresh}>
            Refresh
          </button>
        </div>
        {health && (
          <>
            <p className="mt-3 text-sm text-slate-300">
              API version <span className="font-mono text-violet-300">{health.version ?? "—"}</span> · Total
              chunks: <strong className="text-white">{total}</strong>
            </p>
            <div className="mt-4 overflow-x-auto rounded-xl border border-white/5">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 bg-slate-950/50 text-slate-500">
                    <th className="px-4 py-3 font-medium">Collection</th>
                    <th className="px-4 py-3 font-medium">Chunks</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(health.collections).map(([name, count]) => (
                    <tr key={name} className="border-b border-white/5">
                      <td className="px-4 py-3 font-mono text-xs text-slate-300">{name}</td>
                      <td
                        className={`px-4 py-3 font-mono font-semibold ${count === 0 ? "text-amber-400" : "text-emerald-400"}`}
                      >
                        {count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      <p className={page.muted}>
        <Link to="/" className="ui-link">
          Chat
        </Link>
        {" · "}
        <Link to="/explorer" className="ui-link">
          RAG Explorer
        </Link>
        {" · reindex from Chat"}
      </p>
    </div>
  );
}
