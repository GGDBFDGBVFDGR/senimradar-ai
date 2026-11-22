import { FutureModule } from "../components/ui/FutureModule.tsx";
import { useI18n } from "../i18n/LanguageProvider.tsx";

export function VoicePage() {
  const { messages } = useI18n();
  return (
    <FutureModule
      title={messages.voice.title}
      description={messages.voice.lead}
      stage={6}
      tone="planned"
      points={messages.voice.points}
    >
      <label htmlFor="voice-file" className="text-sm font-semibold text-ink">
        {messages.voice.fileLabel}
      </label>
      <input id="voice-file" type="file" disabled className="mt-2 block w-full cursor-not-allowed text-sm text-muted" />
      <p className="mt-2 text-sm leading-6 text-muted">{messages.voice.fileHint}</p>
    </FutureModule>
  );
}
