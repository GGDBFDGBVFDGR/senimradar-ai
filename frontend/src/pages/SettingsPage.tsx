import { useI18n } from "../i18n/LanguageProvider.tsx";
import type { Locale } from "../i18n/LanguageProvider.tsx";
import { Card } from "../components/ui/Card.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";

export function SettingsPage() {
  const { locale, messages, setLocale } = useI18n();
  return (
    <div className="space-y-6">
      <PageHeader title={messages.settings.title} description={messages.settings.lead} />
      <Card>
        <h2 className="font-display text-lg font-bold text-ink">{messages.settings.languageTitle}</h2>
        <p className="mt-2 text-sm leading-6 text-muted">{messages.settings.languageBody}</p>
        <div role="group" aria-label={messages.language.label} className="mt-4 flex flex-wrap gap-2">
          <LocaleChoice locale="ru" current={locale} label={messages.language.ru} onSelect={setLocale} />
          <LocaleChoice locale="kk" current={locale} label={messages.language.kk} onSelect={setLocale} />
        </div>
      </Card>
      <Card>
        <h2 className="font-display text-lg font-bold text-ink">{messages.settings.privacyTitle}</h2>
        <div className="mt-4 space-y-5">
          <SettingSwitch
            id="history"
            label={messages.settings.historyLabel}
            description={messages.settings.historyBody}
          />
          <SettingSwitch
            id="third-party"
            label={messages.settings.thirdPartyLabel}
            description={messages.settings.thirdPartyBody}
          />
        </div>
        <p className="mt-5 text-sm leading-6 text-muted">{messages.settings.localOnly}</p>
      </Card>
      <Card>
        <h2 className="font-display text-lg font-bold text-ink">{messages.settings.modelTitle}</h2>
        <p className="mt-2 text-sm leading-6 text-muted">{messages.settings.modelBody}</p>
        <dl className="mt-5 grid gap-4 sm:grid-cols-2">
          <Info label={messages.settings.modelName} value={messages.settings.notConfigured} />
          <Info label={messages.settings.modelVersion} value={messages.settings.valueMissing} />
          <Info label={messages.settings.modelProvider} value={messages.settings.valueMissing} />
          <Info label={messages.settings.modelState} value={messages.settings.switchedOff} />
        </dl>
      </Card>
    </div>
  );
}

function LocaleChoice({
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
      className={`rounded-xl px-4 py-2 text-sm font-semibold ${
        selected ? "bg-cyan-400 text-navy-950" : "border border-line text-ink hover:bg-white/5"
      }`}
    >
      {label}
    </button>
  );
}

function SettingSwitch({ id, label, description }: { id: string; label: string; description: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <p id={`${id}-label`} className="text-sm font-semibold text-ink">
          {label}
        </p>
        <p id={`${id}-help`} className="mt-1 text-sm leading-6 text-muted">
          {description}
        </p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={false}
        aria-labelledby={`${id}-label`}
        aria-describedby={`${id}-help`}
        disabled
        className="relative mt-1 h-7 w-12 shrink-0 cursor-not-allowed rounded-full bg-navy-800 ring-1 ring-line"
      >
        <span className="absolute top-1 left-1 h-5 w-5 rounded-full bg-slate-500" />
      </button>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">{label}</dt>
      <dd className="mt-1 text-sm font-semibold text-ink">{value}</dd>
    </div>
  );
}
