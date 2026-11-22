import { useState } from "react";
import type { FormEvent } from "react";

import { AnalysisResultCard } from "../components/analysis/AnalysisResult.tsx";
import { submitTextAnalysis } from "../services/api.ts";
import { formatMessage, useI18n } from "../i18n/LanguageProvider.tsx";
import type { TextAnalysisResult } from "../types/system.ts";
import { Card } from "../components/ui/Card.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";

const MAX_LENGTH = 8000;

export function ScannerPage() {
  const { messages } = useI18n();
  const [text, setText] = useState("");
  const [language, setLanguage] = useState("ru");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<TextAnalysisResult | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || pending) {
      return;
    }
    setPending(true);
    setResult(null);
    const next = await submitTextAnalysis(trimmed, language);
    setResult(next);
    setPending(false);
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow={messages.scanner.eyebrow} title={messages.scanner.title} description={messages.scanner.lead} />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(260px,0.85fr)]">
        <Card>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label htmlFor="message-text" className="text-sm font-semibold text-ink">
                {messages.scanner.label}
              </label>
              <textarea
                id="message-text"
                value={text}
                maxLength={MAX_LENGTH}
                onChange={(event) => setText(event.target.value)}
                placeholder={messages.scanner.placeholder}
                aria-describedby="message-privacy message-count"
                className="mt-2 min-h-52 w-full resize-y rounded-xl border border-line bg-navy-950 px-4 py-3 text-base leading-6 text-ink placeholder:text-muted/70"
              />
              <div className="mt-2 flex items-start justify-between gap-4">
                <p id="message-privacy" className="text-sm leading-6 text-muted">
                  {messages.scanner.privacy}
                </p>
                <p id="message-count" className="shrink-0 text-xs font-semibold text-muted">
                  {formatMessage(messages.scanner.chars, { count: text.trim().length })}
                </p>
              </div>
            </div>
            <div>
              <label htmlFor="message-language" className="text-sm font-semibold text-ink">
                {messages.scanner.languageLabel}
              </label>
              <select
                id="message-language"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
                aria-describedby="message-language-hint"
                className="mt-2 w-full rounded-xl border border-line bg-navy-950 px-3 py-2.5 text-sm text-ink"
              >
                <option value="ru">{messages.scanner.langRu}</option>
                <option value="kk">{messages.scanner.langKk}</option>
                <option value="en">{messages.scanner.langEn}</option>
                <option value="unknown">{messages.scanner.langUnknown}</option>
              </select>
              <p id="message-language-hint" className="mt-2 text-sm text-muted">
                {messages.scanner.languageHint}
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={pending || text.trim().length === 0}
                className="rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-bold text-navy-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {pending ? messages.scanner.submitting : messages.scanner.submit}
              </button>
              <button
                type="button"
                onClick={() => {
                  setText("");
                  setResult(null);
                }}
                className="rounded-xl border border-line px-4 py-2.5 text-sm font-semibold text-ink hover:bg-white/5"
              >
                {messages.scanner.clear}
              </button>
            </div>
          </form>
        </Card>
        <Card>
          <h2 className="font-display text-lg font-bold text-ink">{messages.scanner.resultTitle}</h2>
          <div data-testid="analysis-result" aria-live="polite" className="mt-4">
            <ResultPanel pending={pending} result={result} />
          </div>
        </Card>
      </div>
    </div>
  );
}

function ResultPanel({ pending, result }: { pending: boolean; result: TextAnalysisResult | null }) {
  const { messages } = useI18n();
  if (pending) {
    return (
      <div>
        <p className="text-base font-semibold text-ink">{messages.scanner.submitting}</p>
        <p className="mt-2 text-sm leading-6 text-muted">{messages.scanner.submittingNote}</p>
      </div>
    );
  }
  if (!result) {
    return <p className="text-sm leading-6 text-muted">{messages.scanner.emptyResult}</p>;
  }
  if (result.kind === "ok" || result.kind === "insufficient") {
    return <AnalysisResultCard result={result} />;
  }
  if (result.kind === "unavailable") {
    return (
      <div className="rounded-xl border border-amber-200/20 bg-amber-300/10 p-4">
        <p className="text-base font-semibold text-amber-50">{messages.scanner.unavailableTitle}</p>
        <p className="mt-2 text-sm leading-6 text-amber-50/90">{messages.scanner.unavailableBody}</p>
        <p className="mt-3 text-xs font-semibold uppercase tracking-[0.14em] text-amber-100">
          {formatMessage(messages.common.stage, { stage: result.stage })}
        </p>
      </div>
    );
  }
  const copy =
    result.kind === "validation"
      ? { title: messages.scanner.validationTitle, body: messages.scanner.validationBody }
      : result.kind === "too_large"
        ? { title: messages.scanner.validationTitle, body: messages.scanner.tooLarge }
        : result.kind === "rate_limited"
          ? { title: messages.scanner.validationTitle, body: messages.scanner.rateLimited }
          : { title: messages.status.error, body: messages.scanner.network };
  return (
    <div className="rounded-xl border border-rose-300/20 bg-rose-400/10 p-4" role="alert">
      <p className="text-base font-semibold text-rose-50">{copy.title}</p>
      <p className="mt-2 text-sm leading-6 text-rose-50/90">{copy.body}</p>
    </div>
  );
}

