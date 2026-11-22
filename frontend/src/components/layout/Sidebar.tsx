import { NavLink } from "react-router-dom";

import { useSystemStatus } from "../../hooks/useSystemStatus.ts";
import { useI18n } from "../../i18n/LanguageProvider.tsx";
import { Logo } from "../ui/Logo.tsx";
import { NAV_ITEMS } from "./navigation.ts";

export function Sidebar({ onNavigate, onClose }: { onNavigate?: () => void; onClose?: () => void }) {
  const { messages } = useI18n();
  const { capabilities } = useSystemStatus();
  const modelReady = capabilities.data?.model_configured === true;

  return (
    <div className="flex h-full flex-col bg-navy-900 px-4 py-5">
      <div className="flex items-start justify-between gap-3 px-2">
        <Logo />
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-sm text-muted hover:bg-white/5 hover:text-ink"
          >
            {messages.common.closeMenu}
          </button>
        ) : null}
      </div>
      <p className="mt-8 px-3 text-xs font-semibold uppercase tracking-[0.16em] text-muted">{messages.nav.primary}</p>
      <nav className="mt-3 space-y-1 overflow-y-auto" aria-label={messages.nav.primary}>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onNavigate}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors",
                  isActive ? "bg-cyan-400/10 text-cyan-100" : "text-muted hover:bg-white/5 hover:text-ink",
                ].join(" ")
              }
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              {messages.nav[item.key]}
            </NavLink>
          );
        })}
      </nav>
      <p className="mt-auto px-3 pt-6 text-xs font-medium text-muted">
        {modelReady ? messages.common.modelOn : messages.common.modelOff}
      </p>
    </div>
  );
}
