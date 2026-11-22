import { Menu } from "lucide-react";

import { useSystemStatus } from "../../hooks/useSystemStatus.ts";
import { formatMessage, useI18n } from "../../i18n/LanguageProvider.tsx";
import type { Locale } from "../../i18n/LanguageProvider.tsx";

export function TopBar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const { locale, messages, setLocale } = useI18n();
  const { health } = useSystemStatus();
  const apiOnline = health.isSuccess;

  return (
    <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-line bg-navy-950/85 px-4 py-3 backdrop-blur sm:px-6">
      <button
        type="button"
        onClick={onOpenMenu}
        className="rounded-xl border border-line px-3 py-2 text-sm font-semibold text-ink lg:hidden"
      >
        <span className="flex items-center gap-2">
          <Menu className="h-4 w-4" aria-hidden="true" />
          {messages.common.openMenu}
        </span>
      </button>
      <p className="hidden text-sm font-semibold text-ink sm:block">{messages.meta.appName}</p>
      <div className="ml-auto flex items-center gap-2">
        <span
          className={`hidden items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold sm:inline-flex ${
            health.isLoading
              ? "text-muted"
              : apiOnline
                ? "bg-cyan-400/10 text-cyan-100"
                : "bg-amber-300/10 text-amber-100"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${apiOnline ? "bg-cyan-300" : "bg-amber-200"}`} />
          {health.isLoading ? messages.common.loading : apiOnline ? messages.common.backendOk : messages.common.backendDown}
          {health.data ? <span className="text-muted">{formatMessage(messages.common.version, { version: health.data.version })}</span> : null}
        </span>
        <div role="group" aria-label={messages.language.label} className="flex rounded-xl border border-line p-1">
          <LanguageButton locale="ru" current={locale} label={messages.language.ru} onSelect={setLocale} />
          <LanguageButton locale="kk" current={locale} label={messages.language.kk} onSelect={setLocale} />
        </div>
      </div>
    </header>
  );
}

function LanguageButton({
  locale,
  current,
  label,
  onSelect,
}: {
  locale: Locale;
  current: Locale;
  label: string;
  onSelect: (locale: Locale) => void;
}) {
  const selected = locale === current;
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={() => onSelect(locale)}
      className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
        selected ? "bg-cyan-400 text-navy-950" : "text-muted hover:text-ink"
      }`}
    >
      {label}
    </button>
  );
}
