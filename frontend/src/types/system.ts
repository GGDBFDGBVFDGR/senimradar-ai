export type CapabilityStatus = "ready" | "unavailable" | "planned" | "disabled";

export type Capability = {
  key: string;
  status: CapabilityStatus;
  stage: number;
  note_code: string;
};

export type CapabilitiesResponse = {
  product: string;
  stage: number;
  model_configured: boolean;
  third_party_ai_enabled: boolean;
  supported_locales: string[];
  capabilities: Capability[];
};

export type HealthResponse = {
  status: "ok";
  service: string;
  version: string;
  environment: string;
};

export type ReadyResponse = {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
};

export type TextAnalysisResult =
  | { kind: "unavailable"; stage: number; code: string }
  | { kind: "validation" }
  | { kind: "too_large" }
  | { kind: "rate_limited" }
  | { kind: "error" };
