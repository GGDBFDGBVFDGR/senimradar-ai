import { useState } from "react";
import type { FormEvent } from "react";

import { submitUrlAnalysis } from "../services/api.ts";
import { formatMessage, useI18n } from "../i18n/LanguageProvider.tsx";
import type { UrlAnalysisResult } from "../services/api.ts";
import { Card } from "../components/ui/Card.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";

export function UrlPage() {
  const { messages } = useI18n();
  const [value, setValue] = useState("");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<UrlAnalysisResult | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || pending) {
      return;
    }
    setPending(true);
    setResult(null);
    setResult(await submitUrlAnalysis(trimmed));
    setPending(false);
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow={formatMessage(messages.common.stage, { stage: 4 })} title={messages.url.title} description={messages.url.lead} />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(260px,0.85fr)]">
        <Card>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label htmlFor="url-input" className="text-sm font-semibold text-ink">
                {messages.url.fieldLabel}
              </label>
              <input
                id="url-input"
                type="text"
                inputMode="url"
                autoCapitalize="off"
                autoCorrect="off"
                spellCheck={false}
                value={value}
                maxLength={2048}
                onChange={(event) => setValue(event.target.value)}
                placeholder={messages.url.placeholder}
                aria-describedby="url-privacy"
                className="mt-2 w-full rounded-xl border border-line bg-navy-950 px-4 py-3 text-base text-ink placeholder:text-muted/70"
              />
              <p id="url-privacy" className="mt-2 text-sm leading-6 text-muted">
                {messages.url.fieldHint}
              </p>
            </div>
            <button
              type="submit"
              disabled={pending || value.trim().length === 0}
              className="rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-bold text-navy-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {pending ? messages.url.pending : messages.url.submit}
            </button>
          </form>
        </Card>
        <Card>
          <div data-testid="url-result" aria-live="polite">
            {result ? <UrlResult result={result} /> : <p className="text-sm leading-6 text-muted">{messages.url.emptyResult}</p>}
          </div>
        </Card>
      </div>
    </div>
  );
}

function UrlResult({ result }: { result: UrlAnalysisResult }) {
  const { messages } = useI18n();
  if (result.kind === "unavailable") {
    return <p className="text-sm leading-6 text-amber-50">{messages.url.modelMissing}</p>;
  }
  if (result.kind === "validation" || result.kind === "error") {
    return <p className="text-sm leading-6 text-amber-50">{messages.url.status[result.kind]}</p>;
  }
  const tone =
    result.riskLevel === "high"
      ? "border-rose-300/30 bg-rose-400/10"
      : result.riskLevel === "unknown"
        ? "border-violet-200/30 bg-violet-300/10"
        : "border-line bg-white/5";
  return (
    <div className={`space-y-4 rounded-xl border p-4 ${tone}`}>
      <div>
        <p className="text-base font-semibold text-ink">{messages.url.risk[result.riskLevel]}</p>
        {result.status !== "ok" ? <p className="mt-2 text-sm leading-6 text-amber-50">{messages.url.status[result.status]}</p> : null}
        {result.code ? <p className="mt-2 text-sm leading-6 text-muted">{lookup(messages.url.code, result.code)}</p> : null}
        {!result.classified ? <p className="mt-2 text-sm leading-6 text-muted">{messages.url.notClassified}</p> : null}
      </div>
      <section>
        <h3 className="text-sm font-semibold text-ink">{messages.scanner.indicatorsTitle}</h3>
        {result.indicators.length === 0 ? (
          <p className="mt-2 text-sm leading-6 text-muted">{messages.url.noIndicators}</p>
        ) : (
          <ul className="mt-2 space-y-1 text-sm leading-6 text-ink">
            {result.indicators.map((code) => (
              <li key={code}>{lookup(messages.url.indicator, code)}</li>
            ))}
          </ul>
        )}
      </section>
      <section>
        <h3 className="text-sm font-semibold text-ink">{messages.scanner.recommendationsTitle}</h3>
        <ul className="mt-2 space-y-1 text-sm leading-6 text-ink">
          {result.recommendations.map((code) => (
            <li key={code}>{lookup(messages.url.recommendation, code)}</li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="text-sm font-semibold text-ink">{messages.scanner.limitationsTitle}</h3>
        <ul className="mt-2 space-y-1 text-sm leading-6 text-muted">
          {result.limitations.map((code) => (
            <li key={code}>{lookup(messages.url.limitation, code)}</li>
          ))}
        </ul>
      </section>
      {result.modelVersion ? (
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cyan-200">
          {formatMessage(messages.url.modelLine, { version: result.modelVersion })}
        </p>
      ) : null}
    </div>
  );
}

function lookup(table: Record<string, string>, code: string): string {
  return table[code] ?? code;
}
