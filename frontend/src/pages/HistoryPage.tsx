import { FutureModule } from "../components/ui/FutureModule.tsx";
import { useI18n } from "../i18n/LanguageProvider.tsx";

export function HistoryPage() {
  const { messages } = useI18n();
  return (
    <FutureModule
      title={messages.history.title}
      description={messages.history.lead}
      stage={7}
      tone="disabled"
      points={messages.history.points}
    >
      <p className="text-sm leading-6 text-ink">{messages.history.empty}</p>
    </FutureModule>
  );
}
