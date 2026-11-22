import { formatMessage, useI18n } from "../../i18n/LanguageProvider.tsx";

export function StageBanner({
  stage,
  tone,
}: {
  stage: number;
  tone: "planned" | "unavailable" | "disabled";
}) {
  const { messages } = useI18n();
  return (
    <p className="rounded-2xl border border-line bg-navy-900/70 px-4 py-3 text-sm leading-6 text-muted" role="status">
      {formatMessage(messages.banners[tone], { stage })}
    </p>
  );
}
