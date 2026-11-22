import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import App from "./App.tsx";

const capabilities = {
  product: "SenimRadar AI",
  stage: 1,
  model_configured: false,
  third_party_ai_enabled: false,
  supported_locales: ["ru", "kk"],
  capabilities: [
    { key: "text_analysis", status: "unavailable", stage: 2, note_code: "model_not_configured" },
    { key: "screenshot_analysis", status: "planned", stage: 3, note_code: "scheduled_stage" },
    { key: "url_analysis", status: "planned", stage: 4, note_code: "scheduled_stage" },
    { key: "voice_analysis", status: "planned", stage: 6, note_code: "scheduled_stage" },
    { key: "history", status: "disabled", stage: 7, note_code: "consent_required" },
    { key: "insights", status: "unavailable", stage: 5, note_code: "requires_real_records" },
  ],
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/health/ready")) {
        return json({ status: "degraded", database: "unavailable" }, 503);
      }
      if (url.endsWith("/api/v1/health")) {
        return json({
          status: "ok",
          service: "SenimRadar AI",
          version: "0.1.0",
          environment: "test",
        });
      }
      if (url.endsWith("/api/v1/system/capabilities")) {
        return json(capabilities);
      }
      if (url.endsWith("/api/v1/analysis/text") && init?.method === "POST") {
        return json(
          {
            status: "unavailable",
            code: "model_not_configured",
            stage: 2,
            message: "Text fraud analysis model is not configured.",
            model_version: null,
            risk_level: null,
            risk_score: null,
          },
          503,
        );
      }
      return json({ status: "error", code: "not_found" }, 404);
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

it("starts in Russian and switches the interface to Kazakh", async () => {
  const user = userEvent.setup();
  render(<App />);
  expect(screen.getByRole("heading", { name: "Проверь, прежде чем доверять" })).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Қазақша" }));
  expect(screen.getByRole("heading", { name: "Сенбес бұрын, тексер." })).toBeInTheDocument();
});

it("shows live module status without pretending the model is ready", async () => {
  render(<App />);
  const textModule = await screen.findByTestId("capability-text_analysis");
  expect(textModule).toHaveTextContent("Недоступно");
  expect(await screen.findByText("База данных не запущена")).toBeInTheDocument();
});

it("returns an unavailable analysis instead of a risk score", async () => {
  const user = userEvent.setup();
  render(<App />);
  await user.click(screen.getByRole("link", { name: "AI-сканер" }));
  await user.type(screen.getByLabelText("Текст сообщения"), "Код 123456");
  await user.click(screen.getByRole("button", { name: "Проверить" }));
  const result = await screen.findByTestId("analysis-result");
  expect(result).toHaveTextContent("Анализ недоступен");
  expect(result).not.toHaveTextContent("123456");
  expect(result).not.toHaveTextContent(/высокий|high/i);
});

it("shows a real model result without a percentage", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.mocked(fetch);
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/api/v1/analysis/text") && init?.method === "POST") {
      return json({
        status: "ok",
        language: "ru",
        language_evaluation: "evaluated",
        model_version: "tfidf-logreg-0001",
        risk_level: "high",
        risk_score: null,
        uncertain: false,
        indicators: ["payment_request"],
        cues: ["перевод"],
        recommendations: ["not_proof", "do_not_transfer"],
        limitations: ["synthetic_training_data", "confidence_not_calibrated"],
      });
    }
    if (url.endsWith("/api/v1/health/ready")) {
      return json({ status: "ok", database: "ok" });
    }
    if (url.endsWith("/api/v1/health")) {
      return json({ status: "ok", service: "SenimRadar AI", version: "0.1.0", environment: "test" });
    }
    if (url.endsWith("/api/v1/system/capabilities")) {
      return json({ ...capabilities, stage: 2, model_configured: true });
    }
    return json({ status: "error", code: "not_found" }, 404);
  });
  render(<App />);
  await user.click(screen.getByRole("link", { name: "AI-сканер" }));
  await user.type(screen.getByLabelText("Текст сообщения"), "Код 123456 перевод");
  await user.click(screen.getByRole("button", { name: "Проверить" }));
  const result = await screen.findByTestId("analysis-result");
  expect(result).toHaveTextContent("Высокий предполагаемый риск");
  expect(result).toHaveTextContent("tfidf-logreg-0001");
  expect(result).toHaveTextContent("Просьба перевести или заплатить");
  expect(result).not.toHaveTextContent("123456");
  expect(result).not.toHaveTextContent("%");
});

it("reads a screenshot as text before the existing model sees it", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.mocked(fetch);
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/api/v1/analysis/screenshot") && init?.method === "POST") {
      return json({
        status: "ok",
        text: "Срочно переведите деньги",
        engine: "apple_vision",
        warnings: [],
        line_count: 1,
        selected_language: "ru",
        ml_language: "ru",
        language_locked: false,
      });
    }
    if (url.endsWith("/api/v1/analysis/text") && init?.method === "POST") {
      return json({
        status: "ok",
        language: "ru",
        language_evaluation: "evaluated",
        model_version: "tfidf-linearsvm-0001m",
        risk_level: "high",
        risk_score: null,
        uncertain: false,
        indicators: ["payment_request"],
        cues: ["переведите"],
        recommendations: ["not_proof", "do_not_transfer"],
        limitations: ["synthetic_training_data"],
      });
    }
    if (url.endsWith("/api/v1/health/ready")) {
      return json({ status: "ok", database: "ok" });
    }
    if (url.endsWith("/api/v1/health")) {
      return json({ status: "ok", service: "SenimRadar AI", version: "0.1.0", environment: "test" });
    }
    if (url.endsWith("/api/v1/system/capabilities")) {
      return json(capabilities);
    }
    return json({ status: "error", code: "not_found" }, 404);
  });
  render(<App />);
  await user.click(screen.getByRole("link", { name: "Скриншоты" }));
  const input = screen.getByLabelText(/Перетащите снимок/);
  const file = new File([new Uint8Array([137, 80, 78, 71])], "shot.png", { type: "image/png" });
  await user.upload(input, file);
  await user.click(screen.getByRole("button", { name: "Распознать текст" }));
  expect(await screen.findByLabelText("Распознанный текст")).toHaveValue("Срочно переведите деньги");
  await user.click(screen.getByRole("button", { name: "Проверить текст" }));
  const result = await screen.findByTestId("screenshot-analysis");
  expect(result).toHaveTextContent("Высокий предполагаемый риск");
  expect(result).toHaveTextContent("tfidf-linearsvm-0001m");
  expect(screen.getByText("Распознавание")).toBeInTheDocument();
  expect(screen.getByText("Оценка модели")).toBeInTheDocument();
});

it("does not score a Kazakh screenshot with the Russian model", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.mocked(fetch);
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/api/v1/analysis/screenshot") && init?.method === "POST") {
      return json({
        status: "ok",
        text: "Срочно переведите деньги",
        engine: "tesseract",
        warnings: ["kazakh_script_detected"],
        line_count: 1,
        selected_language: "kk",
        ml_language: "kk",
        language_locked: true,
      });
    }
    if (url.endsWith("/api/v1/analysis/text") && init?.method === "POST") {
      const sent = JSON.parse(String(init.body));
      expect(sent.language).toBe("kk");
      expect(sent.image_language).toBe("kk");
      return json({
        status: "ok",
        language: "kk",
        language_evaluation: "not_evaluated",
        model_version: "tfidf-linearsvm-0001m",
        risk_level: "unknown",
        risk_score: null,
        uncertain: true,
        indicators: [],
        cues: [],
        recommendations: ["result_uncertain"],
        limitations: ["kazakh_not_evaluated"],
      });
    }
    if (url.endsWith("/api/v1/health/ready")) {
      return json({ status: "ok", database: "ok" });
    }
    if (url.endsWith("/api/v1/health")) {
      return json({ status: "ok", service: "SenimRadar AI", version: "0.1.0", environment: "test" });
    }
    if (url.endsWith("/api/v1/system/capabilities")) {
      return json(capabilities);
    }
    return json({ status: "error", code: "not_found" }, 404);
  });
  render(<App />);
  await user.click(screen.getByRole("link", { name: "Скриншоты" }));
  await user.click(screen.getByRole("radio", { name: "Казахский" }));
  const input = screen.getByLabelText(/Перетащите снимок/);
  await user.upload(input, new File([new Uint8Array([137, 80, 78, 71])], "shot.png", { type: "image/png" }));
  await user.click(screen.getByRole("button", { name: "Распознать текст" }));
  expect(await screen.findByLabelText("Язык для проверки")).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Проверить текст" }));
  const result = await screen.findByTestId("screenshot-analysis");
  expect(result).toHaveTextContent("Неопределённый риск");
  expect(result).not.toHaveTextContent("Высокий предполагаемый риск");
});

it("keeps unfinished modules from accepting data", async () => {
  const user = userEvent.setup();
  render(<App />);
  await user.click(screen.getByRole("link", { name: "Скриншоты" }));
  expect(screen.getByLabelText(/Перетащите снимок/)).not.toBeDisabled();
  await user.click(screen.getByRole("link", { name: "Ссылки" }));
  expect(screen.getByLabelText("Адрес")).toBeEnabled();
  await user.click(screen.getByRole("link", { name: "Голос" }));
  expect(screen.getByLabelText("Аудиозапись")).toBeDisabled();
  await user.click(screen.getByRole("link", { name: "История" }));
  expect(screen.getByText("Сохранённых проверок нет.")).toBeInTheDocument();
});

it("shows a URL result without turning the address into a link", async () => {
  const user = userEvent.setup();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/health/ready")) {
        return json({ status: "ok", database: "ok" });
      }
      if (url.endsWith("/api/v1/health")) {
        return json({ status: "ok", service: "SenimRadar AI", version: "0.1.0", environment: "test" });
      }
      if (url.endsWith("/api/v1/system/capabilities")) {
        return json(capabilities);
      }
      if (url.endsWith("/api/v1/analysis/url") && init?.method === "POST") {
        return json({
          status: "ok",
          code: null,
          risk_level: "unknown",
          risk_score: null,
          model_version: "url-tfidf-linearsvm-0001",
          uncertain: true,
          classified: true,
          indicators: ["lookalike_brand"],
          recommendations: ["result_uncertain"],
          limitations: ["not_fetched"],
        });
      }
      return json({ status: "error", code: "not_found" }, 404);
    }),
  );
  render(<App />);
  await user.click(screen.getByRole("link", { name: "Ссылки" }));
  const field = screen.getByLabelText("Адрес");
  await user.type(field, "https://paypa1.example/login");
  await user.click(screen.getByRole("button", { name: "Проверить адрес" }));
  const result = await screen.findByTestId("url-result");
  expect(result).toHaveTextContent("Риск не определён");
  expect(result).toHaveTextContent("url-tfidf-linearsvm-0001");
  expect(result).toHaveTextContent("Часть имени похожа на известный бренд");
  expect(result.querySelector("a")).toBeNull();
  expect(result).not.toHaveTextContent("%");
});
