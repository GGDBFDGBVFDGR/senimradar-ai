import { Link } from "react-router-dom";

import { useSystemStatus } from "../hooks/useSystemStatus.ts";
import { formatMessage, useI18n } from "../i18n/LanguageProvider.tsx";
import type { Messages } from "../i18n/ru.ts";
import { RadarMark } from "../components/ui/RadarMark.tsx";
import { StatusBadge } from "../components/ui/StatusBadge.tsx";
import { Card } from "../components/ui/Card.tsx";

export function OverviewPage() {
  const { messages } = useI18n();
  const { health, ready, capabilities } = useSystemStatus();

  const databaseLabel = databaseCopy(messages, health.isError, ready.isLoading, ready.isError, ready.data?.database);
  const modelReady = capabilities.data?.model_configured === true;

  return (
    <div className="space-y-8">
      <section className="grid items-center gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(260px,0.85fr)]">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">{messages.overview.eyebrow}</p>
          <h1 className="mt-3 max-w-xl font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            {messages.overview.title}
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted sm:text-lg">{messages.overview.lead}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/scanner"
              className="inline-flex items-center justify-center rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-bold text-navy-950 hover:bg-cyan-300"
            >
              {messages.overview.primaryCta}
            </Link>
            <a
              href="#system-status"
              className="inline-flex items-center justify-center rounded-xl border border-line px-4 py-2.5 text-sm font-semibold text-ink hover:bg-white/5"
            >
              {messages.overview.secondaryCta}
            </a>
          </div>
        </div>
        <Card className="flex flex-col items-center justify-center bg-[radial-gradient(circle_at_center,rgb(34_211_238_/_0.08),transparent_65%)]">
          <RadarMark />
          <p className="mt-2 text-center text-sm font-semibold text-ink">
            {modelReady ? messages.common.modelOn : messages.common.modelOff}
          </p>
        </Card>
      </section>

      <section>
        <h2 className="font-display text-xl font-bold text-ink">{messages.overview.pipelineTitle}</h2>
        <ol className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {messages.overview.steps.map((step, index) => {
            const waiting = !modelReady && index >= 2;
            return (
              <li key={step.title}>
                <Card className="h-full">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-display text-sm font-bold text-cyan-200">0{index + 1}</span>
                    <StatusBadge status={waiting ? "planned" : "ready"}>
                      {waiting ? messages.overview.waiting : messages.overview.activeStep}
                    </StatusBadge>
                  </div>
                  <h3 className="mt-4 font-display text-lg font-bold text-ink">{step.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted">{step.text}</p>
                </Card>
              </li>
            );
          })}
        </ol>
      </section>

      <section>
        <h2 className="font-display text-xl font-bold text-ink">{messages.overview.modulesTitle}</h2>
        {capabilities.isLoading ? <p className="mt-4 text-sm text-muted">{messages.common.loading}</p> : null}
        {capabilities.isError ? (
          <p className="mt-4 text-sm text-amber-100" role="alert">
            {messages.common.apiOffline}
          </p>
        ) : null}
        {capabilities.data ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {capabilities.data.capabilities.map((capability) => {
              const copy = capabilityCopy(messages, capability.key);
              return (
                <Card key={capability.key} className="h-full">
                  <div data-testid={`capability-${capability.key}`}>
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="font-display text-lg font-bold text-ink">{copy.title}</h3>
                      <StatusBadge status={capability.status}>{statusLabel(messages, capability.status)}</StatusBadge>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted">
                      {capability.key === "text_analysis" && capability.status === "ready"
                        ? messages.capabilities.text_analysis.readyBody
                        : copy.body}
                    </p>
                    <p className="mt-4 text-xs font-semibold uppercase tracking-[0.14em] text-violet-200">
                      {formatMessage(noteLabel(messages, capability.note_code), { stage: capability.stage })}
                    </p>
                  </div>
                </Card>
              );
            })}
          </div>
        ) : null}
      </section>

      <section>
        <h2 className="font-display text-xl font-bold text-ink">{messages.overview.principlesTitle}</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {messages.overview.principles.map((principle) => (
            <Card key={principle.title}>
              <h3 className="font-display text-lg font-bold text-ink">{principle.title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted">{principle.text}</p>
            </Card>
          ))}
        </div>
      </section>

      <section id="system-status">
        <h2 className="font-display text-xl font-bold text-ink">{messages.overview.systemTitle}</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <Card>
            <p className="text-sm text-muted">API</p>
            <div className="mt-3">
              <StatusBadge status={health.isLoading ? "loading" : health.isSuccess ? "ok" : "error"}>
                {health.isLoading ? messages.common.loading : health.isSuccess ? messages.common.backendOk : messages.common.backendDown}
              </StatusBadge>
            </div>
            {health.isError ? (
              <button type="button" onClick={() => void health.refetch()} className="mt-4 text-sm font-semibold text-cyan-200">
                {messages.common.retry}
              </button>
            ) : null}
          </Card>
          <Card>
            <p className="text-sm text-muted">MySQL</p>
            <div className="mt-3">
              <StatusBadge status={ready.data?.database === "ok" ? "ok" : ready.isLoading ? "loading" : "degraded"}>
                {databaseLabel}
              </StatusBadge>
            </div>
          </Card>
          <Card>
            <p className="text-sm text-muted">{messages.settings.modelTitle}</p>
            <div className="mt-3">
              <StatusBadge status={modelReady ? "ok" : "unavailable"}>
                {modelReady ? messages.common.modelOn : messages.common.modelOff}
              </StatusBadge>
            </div>
            {health.data ? (
              <p className="mt-4 text-sm text-muted">{formatMessage(messages.common.version, { version: health.data.version })}</p>
            ) : null}
          </Card>
        </div>
        {health.isError ? (
          <p className="mt-4 text-sm text-amber-100" role="alert">
            {messages.common.apiOffline}
          </p>
        ) : null}
      </section>
    </div>
  );
}

function capabilityCopy(messages: Messages, key: string): { title: string; body: string } {
  if (key in messages.capabilities) {
    return messages.capabilities[key as keyof Messages["capabilities"]];
  }
  return { title: key, body: "" };
}

function noteLabel(messages: Messages, code: string): string {
  if (code in messages.notes) {
    return messages.notes[code as keyof Messages["notes"]];
  }
  return code;
}

function statusLabel(messages: Messages, status: string): string {
  if (status in messages.status) {
    return messages.status[status as keyof Messages["status"]];
  }
  return messages.status.unknown;
}

function databaseCopy(
  messages: Messages,
  healthFailed: boolean,
  loading: boolean,
  failed: boolean,
  database: "ok" | "unavailable" | undefined,
): string {
  if (loading) {
    return messages.common.loading;
  }
  if (healthFailed || failed || !database) {
    return messages.common.databaseUnknown;
  }
  return database === "ok" ? messages.common.databaseOk : messages.common.databaseDown;
}
