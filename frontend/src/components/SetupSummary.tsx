import type { Meta } from "../lib/types";
import { page } from "../lib/theme";

const LOCKED_FRONTEND = "React + Vite + Tailwind";
const LOCKED_VECTOR = "Qdrant + bge-m3 + reranker (Recommended)";
const LOCKED_COLLECTIONS = "One collection per source, router decides (Recommended)";

export function SetupSummary({ meta }: { meta: Meta | null }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-violet-400">1. Frontend</p>
        <p className="mt-2 text-sm font-medium text-white">{LOCKED_FRONTEND}</p>
      </div>
      <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-violet-400">2. Vector DB</p>
        <p className="mt-2 text-sm font-medium text-white">{LOCKED_VECTOR}</p>
      </div>
      <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4 sm:col-span-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-violet-400">3. Collections</p>
        <p className="mt-2 text-sm font-medium text-white">{LOCKED_COLLECTIONS}</p>
      </div>
      {meta && (
        <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4 sm:col-span-3">
          <ul className="grid gap-2 sm:grid-cols-2">
            {meta.collections.map((c) => (
              <li key={c.id} className="text-sm text-slate-300">
                <code className={page.code}>{c.id}</code>
                <span className="text-slate-500"> — {c.label}</span>
              </li>
            ))}
          </ul>
          <p className={`mt-4 ${page.muted}`}>
            Models: {meta.embed_model} · {meta.reranker_model} · Groq {meta.groq_model}
          </p>
        </div>
      )}
    </div>
  );
}
