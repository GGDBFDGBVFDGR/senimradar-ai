import { FutureModule } from "../components/ui/FutureModule.tsx";
import { useI18n } from "../i18n/LanguageProvider.tsx";

export function ScreenshotPage() {
  const { messages } = useI18n();
  return (
    <FutureModule
      title={messages.screenshot.title}
      description={messages.screenshot.lead}
      stage={3}
      tone="planned"
      points={messages.screenshot.points}
    >
      <label htmlFor="screenshot-file" className="text-sm font-semibold text-ink">
        {messages.screenshot.fileLabel}
      </label>
      <input
        id="screenshot-file"
        type="file"
        disabled
        className="mt-2 block w-full cursor-not-allowed text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-navy-800 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-muted"
      />
      <p className="mt-2 text-sm leading-6 text-muted">{messages.screenshot.fileHint}</p>
    </FutureModule>
  );
}
