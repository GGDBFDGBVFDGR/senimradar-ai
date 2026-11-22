import { FutureModule } from "../components/ui/FutureModule.tsx";
import { useI18n } from "../i18n/LanguageProvider.tsx";

export function UrlPage() {
  const { messages } = useI18n();
  return (
    <FutureModule
      title={messages.url.title}
      description={messages.url.lead}
      stage={4}
      tone="planned"
      points={messages.url.points}
    >
      <label htmlFor="url-input" className="text-sm font-semibold text-ink">
        {messages.url.fieldLabel}
      </label>
      <input
        id="url-input"
        type="text"
        disabled
        readOnly
        value=""
        placeholder="https://"
        className="mt-2 w-full cursor-not-allowed rounded-xl border border-line bg-navy-950 px-3 py-2.5 text-sm text-muted"
      />
      <p className="mt-2 text-sm leading-6 text-muted">{messages.url.fieldHint}</p>
    </FutureModule>
  );
}
