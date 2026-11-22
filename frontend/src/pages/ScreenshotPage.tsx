import { useEffect, useState } from "react";
import type { DragEvent } from "react";

import { AnalysisResultCard } from "../components/analysis/AnalysisResult.tsx";
import { submitScreenshot, submitTextAnalysis } from "../services/api.ts";
import { useI18n } from "../i18n/LanguageProvider.tsx";
import type { TextAnalysisResult } from "../types/system.ts";
import { Card } from "../components/ui/Card.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";

const MAX_BYTES = 8 * 1024 * 1024;

type Phase = "idle" | "selected" | "recognizing" | "ok" | "no_text" | "analyzing" | "done" | "error";

export function ScreenshotPage() {
  const { messages } = useI18n();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [text, setText] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [language, setLanguage] = useState("ru");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TextAnalysisResult | null>(null);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  function choose(next: File | null) {
    setFile(next);
    setPreview((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return next ? URL.createObjectURL(next) : null;
    });
    setText("");
    setWarnings([]);
    setResult(null);
    setError(null);
    setPhase(next ? "selected" : "idle");
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragOver(false);
    const next = event.dataTransfer.files.item(0);
    if (next) {
      choose(next);
    }
  }

  async function recognize() {
    if (!file || phase === "recognizing") {
      return;
    }
    if (file.size > MAX_BYTES) {
      setPhase("error");
      setError("payload_too_large");
      return;
    }
    setPhase("recognizing");
    setError(null);
    setResult(null);
    const ocr = await submitScreenshot(file);
    if (ocr.kind === "error") {
      setPhase("error");
      setError(ocr.code);
      setText("");
      setWarnings([]);
      return;
    }
    setText(ocr.text);
    setWarnings(ocr.warnings);
    setPhase(ocr.kind);
    if (ocr.warnings.includes("kazakh_glyphs_detected")) {
      setLanguage("kk");
    } else if (ocr.warnings.includes("low_ocr_confidence")) {
      setLanguage("unknown");
    }
  }

  async function analyze() {
    const trimmed = text.trim();
    if (!trimmed || phase === "analyzing") {
      return;
    }
    setPhase("analyzing");
    setError(null);
    const next = await submitTextAnalysis(trimmed, language);
    setResult(next);
    setPhase(next.kind === "error" ? "error" : "done");
    if (next.kind === "error") {
      setError("request_failed");
    }
  }

  const errorText = error ? (messages.screenshot.error[error as keyof typeof messages.screenshot.error] ?? error) : null;

  return (
    <div className="space-y-6">
      <PageHeader eyebrow={messages.scanner.eyebrow} title={messages.screenshot.title} description={messages.screenshot.lead} />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(260px,0.85fr)]">
        <Card>
          <label
            htmlFor="screenshot-file"
            onDragOver={(event) => {
              event.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={`block rounded-xl border border-dashed px-4 py-8 text-center ${dragOver ? "border-cyan-300 bg-cyan-400/10" : "border-line"}`}
          >
            <p className="text-sm font-semibold text-ink">{messages.screenshot.drop}</p>
            <p className="mt-2 text-sm text-muted">{messages.screenshot.fileHint}</p>
            <span className="mt-4 inline-flex rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-bold text-navy-950">
              {messages.screenshot.choose}
            </span>
          </label>
          <input
            id="screenshot-file"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="sr-only"
            onChange={(event) => choose(event.target.files?.item(0) ?? null)}
          />
          {preview ? (
            <img src={preview} alt={messages.screenshot.preview} className="mt-4 max-h-72 w-full rounded-xl object-contain" />
          ) : null}
          <p className="mt-3 text-xs font-semibold uppercase tracking-[0.14em] text-violet-200" data-testid="screenshot-state">
            {messages.screenshot.state[phase]}
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={recognize}
              disabled={!file || phase === "recognizing"}
              className="rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-bold text-navy-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {phase === "recognizing" ? messages.screenshot.recognizing : messages.screenshot.recognize}
            </button>
          </div>
          {errorText ? (
            <p className="mt-3 text-sm text-amber-100" role="alert">
              {errorText}
            </p>
          ) : null}
          {phase === "ok" || phase === "no_text" || phase === "analyzing" || phase === "done" ? (
            <div className="mt-5 space-y-3">
              <h2 className="font-display text-lg font-bold text-ink">{messages.screenshot.ocrTitle}</h2>
              {phase === "no_text" ? <p className="text-sm leading-6 text-amber-50">{messages.screenshot.noText}</p> : null}
              {warnings.map((code) => (
                <p key={code} className="text-sm leading-6 text-amber-50">
                  {messages.screenshot.warning[code as keyof typeof messages.screenshot.warning] ?? code}
                </p>
              ))}
              <label htmlFor="ocr-text" className="text-sm font-semibold text-ink">
                {messages.screenshot.textLabel}
              </label>
              <textarea
                id="ocr-text"
                value={text}
                onChange={(event) => setText(event.target.value)}
                aria-describedby="ocr-hint"
                className="mt-2 min-h-40 w-full resize-y rounded-xl border border-line bg-navy-950 px-4 py-3 text-base leading-6 text-ink"
              />
              <p id="ocr-hint" className="text-sm leading-6 text-muted">
                {messages.screenshot.textHint}
              </p>
              <label htmlFor="ocr-language" className="text-sm font-semibold text-ink">
                {messages.screenshot.languageLabel}
              </label>
              <select
                id="ocr-language"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
                className="mt-2 w-full rounded-xl border border-line bg-navy-950 px-3 py-2.5 text-sm text-ink"
              >
                <option value="ru">{messages.scanner.langRu}</option>
                <option value="kk">{messages.scanner.langKk}</option>
                <option value="en">{messages.scanner.langEn}</option>
                <option value="unknown">{messages.scanner.langUnknown}</option>
              </select>
              <button
                type="button"
                onClick={analyze}
                disabled={text.trim().length === 0 || phase === "analyzing"}
                className="rounded-xl border border-line px-4 py-2.5 text-sm font-semibold text-ink hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {phase === "analyzing" ? messages.screenshot.analyzing : messages.screenshot.analyze}
              </button>
            </div>
          ) : null}
        </Card>
        <Card>
          <h2 className="font-display text-lg font-bold text-ink">{messages.screenshot.mlTitle}</h2>
          <div data-testid="screenshot-analysis" aria-live="polite" className="mt-4">
            {result && (result.kind === "ok" || result.kind === "insufficient") ? (
              <AnalysisResultCard result={result} />
            ) : (
              <p className="text-sm leading-6 text-muted">{messages.scanner.emptyResult}</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
