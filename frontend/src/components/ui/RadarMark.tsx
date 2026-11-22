export function RadarMark({ className = "h-44 w-44" }: { className?: string }) {
  return (
    <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
      <circle cx="80" cy="80" r="70" fill="none" stroke="rgb(34 211 238 / 0.35)" strokeWidth="1" />
      <circle cx="80" cy="80" r="46" fill="none" stroke="rgb(167 139 250 / 0.45)" strokeWidth="1" />
      <circle cx="80" cy="80" r="22" fill="none" stroke="rgb(103 232 249 / 0.7)" strokeWidth="1.4" />
      <circle cx="80" cy="80" r="4" fill="#67e8f9" />
      <path d="M80 10 V150 M10 80 H150" stroke="rgb(148 163 184 / 0.18)" strokeWidth="1" />
      <g className="radar-sweep">
        <path d="M80 80 L80 12 A68 68 0 0 1 136 48 Z" fill="rgb(34 211 238 / 0.16)" />
        <path d="M80 80 L80 12" stroke="#e0f2fe" strokeWidth="1.5" />
      </g>
    </svg>
  );
}
