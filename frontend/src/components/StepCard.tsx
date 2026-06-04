import { useState } from "react";

export function StepCard({
  step,
  title,
  defaultOpen = false,
  children,
}: {
  step: string;
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70 shadow-lg shadow-black/20">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left transition hover:bg-white/5"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="flex items-center gap-3">
          <span className="font-mono text-xs font-bold text-violet-400">{step}</span>
          <span className="font-medium text-white">{title}</span>
        </span>
        <span className="text-slate-500">{open ? "▾" : "▸"}</span>
      </button>
      {open && <div className="border-t border-white/10 px-5 py-4 text-slate-300">{children}</div>}
    </section>
  );
}
