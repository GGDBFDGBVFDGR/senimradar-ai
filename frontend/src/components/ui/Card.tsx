import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border border-line bg-navy-900/80 p-5 shadow-[0_18px_50px_rgb(0_0_0_/_0.22)] ${className}`}>
      {children}
    </section>
  );
}
