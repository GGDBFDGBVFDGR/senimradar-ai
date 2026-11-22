export function Logo() {
  return (
    <span className="flex items-center gap-3">
      <svg viewBox="0 0 40 40" className="h-10 w-10 shrink-0" aria-hidden="true">
        <circle cx="20" cy="20" r="16" fill="none" stroke="#22d3ee" strokeWidth="1.4" />
        <circle cx="20" cy="20" r="9" fill="none" stroke="#a78bfa" strokeWidth="1.4" />
        <circle cx="20" cy="20" r="2.2" fill="#67e8f9" />
        <path d="M20 20 L31 11" stroke="#e0f2fe" strokeWidth="1.4" />
      </svg>
      <span>
        <span className="block font-display text-sm font-bold tracking-wide text-ink">SenimRadar</span>
        <span className="block text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-300">AI</span>
      </span>
    </span>
  );
}
