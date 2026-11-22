import { formatMessage, useI18n } from "../../i18n/LanguageProvider.tsx";
import type { TextAnalysisResult } from "../../types/system.ts";

export function AnalysisResultCard({
  result,
}: {
  result: Extract<TextAnalysisResult, { kind: "ok" | "insufficient" }>;
}) {
  const { messages } = useI18n();
  const tone =
    result.riskLevel === "high"
      ? "border-rose-300/30 bg-rose-400/10"
      : result.riskLevel === "medium"
        ? "border-amber-200/30 bg-amber-300/10"
        : result.riskLevel === "unknown"
          ? "border-violet-200/30 bg-violet-300/10"
          : "border-line bg-white/5";
  const lead =
    result.kind === "insufficient"
      ? messages.scanner.insufficientBody
      : result.riskLevel === "high" || result.riskLevel === "medium"
        ? messages.scanner.recommendation.not_proof
        : result.riskLevel === "unknown"
          ? messages.scanner.unknownNotLow
          : messages.scanner.lowNotSafe;
  return (
    <div className={`space-y-4 rounded-xl border p-4 ${tone}`}>
      <div>
        <p className="text-base font-semibold text-ink">{messages.scanner.risk[result.riskLevel]}</p>
        <p className="mt-2 text-sm leading-6 text-muted">{lead}</p>
        {result.uncertain ? <p className="mt-2 text-sm leading-6 text-amber-50">{messages.scanner.uncertain}</p> : null}
      </div>
      <section>
        <h3 className="text-sm font-semibold text-ink">{messages.scanner.indicatorsTitle}</h3>
        <p className="mt-1 text-xs leading-5 text-muted">{messages.scanner.indicatorsNote}</p>
        {result.indicators.length === 0 ? (
          <p className="mt-2 text-sm leading-6 text-muted">{messages.scanner.noIndicators}</p>
        ) : (
          <ul className="mt-2 space-y-1 text-sm leading-6 text-ink">
            {result.indicators.map((code) => (
              <li key={code}>{lookup(messages.scanner.indicator, code)}</li>
            ))}
          </ul>
        )}
      </section>
      {result.cues.length > 0 ? (
        <section>
          <h3 className="text-sm font-semibold text-ink">{messages.scanner.cuesTitle}</h3>
          <p className="mt-2 text-sm leading-6 text-muted">{result.cues.join(" · ")}</p>
        </section>
      ) : null}
      <section>
        <h3 className="text-sm font-semibold text-ink">{messages.scanner.recommendationsTitle}</h3>
        <ul className="mt-2 space-y-1 text-sm leading-6 text-ink">
          {result.recommendations.map((code) => (
            <li key={code}>{lookup(messages.scanner.recommendation, code)}</li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="text-sm font-semibold text-ink">{messages.scanner.limitationsTitle}</h3>
        <ul className="mt-2 space-y-1 text-sm leading-6 text-muted">
          {result.limitations.map((code) => (
            <li key={code}>{lookup(messages.scanner.limitation, code)}</li>
          ))}
        </ul>
      </section>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-violet-200">
        {lookup(messages.scanner.evaluation, result.languageEvaluation)}
      </p>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cyan-200">
        {formatMessage(messages.scanner.modelLine, { version: result.modelVersion })}
      </p>
    </div>
  );
}

function lookup(table: Record<string, string>, code: string): string {
  return table[code] ?? code;
}
