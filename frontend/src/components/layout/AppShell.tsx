import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";

import { useI18n } from "../../i18n/LanguageProvider.tsx";
import { Sidebar } from "./Sidebar.tsx";
import { TopBar } from "./TopBar.tsx";

export function AppShell() {
  const { messages } = useI18n();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[270px_minmax(0,1fr)]">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-cyan-300 focus:px-3 focus:py-2 focus:text-navy-950"
      >
        {messages.common.skipToContent}
      </a>
      <aside className="hidden border-r border-line lg:block">
        <div className="sticky top-0 h-screen">
          <Sidebar />
        </div>
      </aside>
      {menuOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-navy-950/75"
            aria-label={messages.common.closeMenu}
            onClick={() => setMenuOpen(false)}
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label={messages.nav.primary}
            className="absolute inset-y-0 left-0 w-[min(100%,290px)] border-r border-line shadow-2xl"
          >
            <Sidebar onNavigate={() => setMenuOpen(false)} onClose={() => setMenuOpen(false)} />
          </div>
        </div>
      ) : null}
      <div className="min-w-0">
        <TopBar onOpenMenu={() => setMenuOpen(true)} />
        <main id="content" className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
          <Outlet />
          <footer className="mt-10 border-t border-line pt-4 text-sm leading-6 text-muted">{messages.meta.disclaimer}</footer>
        </main>
      </div>
    </div>
  );
}
