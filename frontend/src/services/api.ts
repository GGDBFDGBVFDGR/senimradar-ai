import type {
  CapabilitiesResponse,
  HealthResponse,
  ReadyResponse,
  TextAnalysisResult,
} from "../types/system.ts";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

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
    response = await fetch(`${API_BASE_URL}${path}`, {
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
    response = await fetch(`${API_BASE_URL}/api/v1/health/ready`, {
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

export async function submitTextAnalysis(text: string, language: string): Promise<TextAnalysisResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/analysis/text`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text, language }),
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

function stringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}
