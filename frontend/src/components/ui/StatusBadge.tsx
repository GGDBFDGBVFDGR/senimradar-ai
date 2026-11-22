import type { ReactNode } from "react";

const tones: Record<string, string> = {
  ready: "bg-cyan-400/10 text-cyan-100 ring-cyan-300/30",
  ok: "bg-cyan-400/10 text-cyan-100 ring-cyan-300/30",
  unavailable: "bg-amber-300/10 text-amber-100 ring-amber-200/30",
  degraded: "bg-amber-300/10 text-amber-100 ring-amber-200/30",
  planned: "bg-violet-400/15 text-violet-100 ring-violet-300/30",
  disabled: "bg-slate-400/10 text-slate-200 ring-slate-300/20",
  unknown: "bg-slate-400/10 text-slate-200 ring-slate-300/20",
  error: "bg-rose-400/10 text-rose-100 ring-rose-300/30",
  loading: "bg-slate-400/10 text-slate-200 ring-slate-300/20",
};

export function StatusBadge({ status, children }: { status: string; children: ReactNode }) {
  const tone = tones[status] ?? tones.unknown;
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tone}`}>
      {children}
    </span>
  );
}
