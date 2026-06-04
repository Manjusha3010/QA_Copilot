import { NavLink } from "react-router-dom";
import { ktDocUrl } from "../lib/ktDocUrl";

function navClass({ isActive }: { isActive: boolean }) {
  return isActive
    ? "rounded-full bg-gradient-to-r from-violet-600/90 to-indigo-600/90 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-violet-600/25"
    : "rounded-full px-4 py-2 text-sm font-medium text-slate-400 transition hover:bg-white/5 hover:text-slate-200";
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen bg-[#07070f] text-slate-200">
      <div className="app-glow" aria-hidden />
      <header className="relative sticky top-0 z-10 border-b border-white/10 bg-slate-950/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-sm font-bold text-white shadow-lg shadow-violet-600/30">
              QA
            </span>
            <div>
              <span className="block font-semibold tracking-tight text-white">QA Copilot</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
                Modular RAG · v1.0.0
              </span>
            </div>
          </div>
          <nav className="flex flex-wrap items-center gap-1 rounded-full border border-white/10 bg-slate-900/60 p-1">
            <NavLink to="/" end className={navClass}>
              Chat
            </NavLink>
            <NavLink to="/explorer" className={navClass}>
              RAG Explorer
            </NavLink>
            <NavLink to="/status" className={navClass}>
              Status
            </NavLink>
            <a
              href={ktDocUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full px-4 py-2 text-sm font-medium text-slate-400 transition hover:bg-white/5 hover:text-cyan-300"
            >
              KT Doc
            </a>
          </nav>
        </div>
      </header>
      <main className="relative mx-auto max-w-5xl px-4 py-8">{children}</main>
    </div>
  );
}
