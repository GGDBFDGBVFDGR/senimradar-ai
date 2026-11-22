import type {
  CapabilitiesResponse,
  HealthResponse,
  ReadyResponse,
  TextAnalysisResult,
} from "../types/system.ts";

const LOCAL_API_BASE_URL = "http://127.0.0.1:8000";

export async function apiBaseUrl(): Promise<string> {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (typeof configured === "string" && configured.length > 0) {
    return configured.replace(/\/$/, "");
  }
  if (typeof window !== "undefined" && window.location.hostname.endsWith("github.io")) {
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}api-config.json`, { cache: "no-store" });
      if (response.ok) {
        const body = (await response.json()) as { apiBaseUrl?: unknown };
        if (typeof body.apiBaseUrl === "string" && body.apiBaseUrl.startsWith("https://")) {
          return body.apiBaseUrl.replace(/\/$/, "");
        }
      }
    } catch {
      return LOCAL_API_BASE_URL;
    }
  }
  return LOCAL_API_BASE_URL;
}

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string) {
    super(code);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${await apiBaseUrl()}${path}`, {
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new ApiError(0, "network");
  }
  if (!response.ok) {
    throw new ApiError(response.status, "request_failed");
  }
  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/api/v1/health");
}

export async function getReady(): Promise<ReadyResponse> {
  let response: Response;
  try {
    response = await fetch(`${await apiBaseUrl()}/api/v1/health/ready`, {
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new ApiError(0, "network");
  }
  if (response.status === 200 || response.status === 503) {
    return (await response.json()) as ReadyResponse;
  }
  throw new ApiError(response.status, "request_failed");
}

export function getCapabilities(): Promise<CapabilitiesResponse> {
  return getJson<CapabilitiesResponse>("/api/v1/system/capabilities");
}

export async function submitTextAnalysis(
  text: string,
  language: string,
  imageLanguage?: "ru" | "kk",
): Promise<TextAnalysisResult> {
  let response: Response;
  try {
    response = await fetch(`${await apiBaseUrl()}/api/v1/analysis/text`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(imageLanguage ? { text, language, image_language: imageLanguage } : { text, language }),
    });
  } catch {
    return { kind: "error" };
  }

  if (response.status === 200) {
    const body = (await response.json()) as {
      status?: unknown;
      language?: unknown;
      language_evaluation?: unknown;
      model_version?: unknown;
      risk_level?: unknown;
      risk_score?: unknown;
      uncertain?: unknown;
      indicators?: unknown;
      cues?: unknown;
      recommendations?: unknown;
      limitations?: unknown;
    };
    const risk = body.risk_level;
    if (
      (body.status === "ok" || body.status === "insufficient") &&
      (risk === "low" || risk === "medium" || risk === "high" || risk === "unknown") &&
      body.risk_score == null &&
      typeof body.model_version === "string"
    ) {
      return {
        kind: body.status,
        language: typeof body.language === "string" ? body.language : "unknown",
        languageEvaluation: typeof body.language_evaluation === "string" ? body.language_evaluation : "not_confirmed",
        modelVersion: body.model_version,
        riskLevel: risk,
        riskScore: null,
        uncertain: body.uncertain === true,
        indicators: stringList(body.indicators),
        cues: stringList(body.cues),
        recommendations: stringList(body.recommendations),
        limitations: stringList(body.limitations),
      };
    }
    return { kind: "error" };
  }
  if (response.status === 503) {
    const body = (await response.json()) as { stage?: unknown; code?: unknown };
    return {
      kind: "unavailable",
      stage: typeof body.stage === "number" ? body.stage : 2,
      code: typeof body.code === "string" ? body.code : "model_not_configured",
    };
  }
  if (response.status === 422) {
    return { kind: "validation" };
  }
  if (response.status === 413) {
    return { kind: "too_large" };
  }
  if (response.status === 429) {
    return { kind: "rate_limited" };
  }
  return { kind: "error" };
}

export type ScreenshotOcrResult =
  | {
      kind: "ok" | "no_text";
      text: string;
      engine: string;
      warnings: string[];
      lineCount: number;
      selectedLanguage: string;
      mlLanguage: "ru" | "kk" | "unconfirmed";
      languageLocked: boolean;
    }
  | { kind: "error"; code: string };

export async function submitScreenshot(file: File, language: "auto" | "ru" | "kk"): Promise<ScreenshotOcrResult> {
  const body = new FormData();
  body.append("upload", file, "screenshot");
  body.append("language", language);
  let response: Response;
  try {
    response = await fetch(`${await apiBaseUrl()}/api/v1/analysis/screenshot`, {
      method: "POST",
      headers: { Accept: "application/json" },
      body,
    });
  } catch {
    return { kind: "error", code: "network" };
  }
  if (response.status === 200) {
    const payload = (await response.json()) as {
      status?: unknown;
      text?: unknown;
      engine?: unknown;
      warnings?: unknown;
      line_count?: unknown;
      selected_language?: unknown;
      ml_language?: unknown;
      language_locked?: unknown;
    };
    const mlLanguage = payload.ml_language === "ru" || payload.ml_language === "kk" ? payload.ml_language : "unconfirmed";
    if ((payload.status === "ok" || payload.status === "no_text") && typeof payload.text === "string") {
      return {
        kind: payload.status,
        text: payload.text,
        engine: typeof payload.engine === "string" ? payload.engine : "apple_vision",
        warnings: stringList(payload.warnings),
        lineCount: typeof payload.line_count === "number" ? payload.line_count : 0,
        selectedLanguage: typeof payload.selected_language === "string" ? payload.selected_language : language,
        mlLanguage,
        languageLocked: payload.language_locked === true || mlLanguage === "kk",
      };
    }
    return { kind: "error", code: "request_failed" };
  }
  const payload = (await response.json().catch(() => null)) as { code?: unknown } | null;
  const code = typeof payload?.code === "string" ? payload.code : "request_failed";
  return { kind: "error", code };
}

export type UrlAnalysisResult =
  | {
      kind: "ok" | "needs_review" | "limited";
      status: "ok" | "needs_review" | "limited";
      code: keyof MessagesUrlCode | null;
      riskLevel: "low" | "high" | "unknown";
      modelVersion: string | null;
      uncertain: boolean;
      classified: boolean;
      indicators: string[];
      recommendations: string[];
      limitations: string[];
    }
  | { kind: "unavailable" }
  | { kind: "validation" }
  | { kind: "error" };

type MessagesUrlCode = {
  ocr_damaged: string;
  internal_address: string;
  local_name: string;
  unsupported_scheme: string;
  scheme_required: string;
  invalid_address: string;
};

export async function submitUrlAnalysis(url: string): Promise<UrlAnalysisResult> {
  let response: Response;
  try {
    response = await fetch(`${await apiBaseUrl()}/api/v1/analysis/url`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });
  } catch {
    return { kind: "error" };
  }
  if (response.status === 503) {
    return { kind: "unavailable" };
  }
  if (response.status === 422) {
    return { kind: "validation" };
  }
  if (response.status !== 200) {
    return { kind: "error" };
  }
  const body = (await response.json()) as {
    status?: unknown;
    code?: unknown;
    risk_level?: unknown;
    risk_score?: unknown;
    model_version?: unknown;
    uncertain?: unknown;
    classified?: unknown;
    indicators?: unknown;
    recommendations?: unknown;
    limitations?: unknown;
  };
  const risk = body.risk_level;
  const status = body.status;
  if (
    (status === "ok" || status === "needs_review" || status === "limited") &&
    (risk === "low" || risk === "high" || risk === "unknown") &&
    body.risk_score == null
  ) {
    const code = typeof body.code === "string" ? body.code : null;
    return {
      kind: status,
      status,
      code: isUrlCode(code) ? code : null,
      riskLevel: risk,
      modelVersion: typeof body.model_version === "string" ? body.model_version : null,
      uncertain: body.uncertain === true,
      classified: body.classified === true,
      indicators: stringList(body.indicators),
      recommendations: stringList(body.recommendations),
      limitations: stringList(body.limitations),
    };
  }
  return { kind: "error" };
}

function isUrlCode(value: string | null): value is keyof MessagesUrlCode {
  return (
    value === "ocr_damaged" ||
    value === "internal_address" ||
    value === "local_name" ||
    value === "unsupported_scheme" ||
    value === "scheme_required" ||
    value === "invalid_address"
  );
}

function stringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}
