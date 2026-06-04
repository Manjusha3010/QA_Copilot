/** Shared typography & layout tokens for pages */
export const page = {
  title: "text-3xl font-bold tracking-tight text-white sm:text-4xl",
  subtitle: "mt-2 max-w-2xl text-base leading-relaxed text-slate-400",
  sectionTitle: "text-lg font-semibold text-white",
  sectionHint: "mt-1 text-xs text-slate-500",
  label: "text-sm text-slate-400",
  muted: "text-xs text-slate-500",
  code: "rounded bg-violet-500/15 px-1.5 py-0.5 font-mono text-xs text-violet-300",
} as const;

export const alert = {
  warn: "rounded-2xl border border-amber-500/35 bg-amber-500/10 p-4 text-amber-100",
  ok: "rounded-2xl border border-emerald-500/35 bg-emerald-500/10 p-4 text-emerald-100",
  err: "text-sm text-rose-400",
} as const;
