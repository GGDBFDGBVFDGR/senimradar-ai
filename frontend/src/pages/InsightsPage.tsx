import { FutureModule } from "../components/ui/FutureModule.tsx";
import { useI18n } from "../i18n/LanguageProvider.tsx";

export function InsightsPage() {
  const { messages } = useI18n();
  return (
    <FutureModule
      title={messages.insights.title}
      description={messages.insights.lead}
      stage={5}
      tone="unavailable"
      points={messages.insights.points}
    >
      <p className="text-sm leading-6 text-ink">{messages.insights.empty}</p>
    </FutureModule>
  );
}
