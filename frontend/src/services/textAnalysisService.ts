import type {
  TextAnalysisRequest,
  TextAnalysisResponse,
  AnalysisHistoryItem,
} from "../types/textAnalysis";

const HISTORY_KEY = "technoax_text_history";
const MAX_HISTORY = 10;

/** Resolve API base URL from Vite env or fall back to localhost */
function getApiBase(): string {
  // @ts-ignore — VITE_API_URL injected at build time
  return (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_URL) || "http://localhost:8000";
}

export class TextAnalysisError extends Error {
  constructor(
    message: string,
    public readonly code: "NETWORK" | "TIMEOUT" | "SERVER" | "INVALID_RESPONSE" | "OFFLINE",
    public readonly status?: number,
  ) {
    super(message);
    this.name = "TextAnalysisError";
  }
}

/**
 * POST /analyze-text
 * Sends text to the backend and returns a structured analysis result.
 */
export async function analyzeText(
  req: TextAnalysisRequest,
  signal?: AbortSignal,
): Promise<TextAnalysisResponse> {
  const url = `${getApiBase()}/analyze-text`;

  if (!navigator.onLine) {
    throw new TextAnalysisError(
      "You appear to be offline. Please check your network connection and try again.",
      "OFFLINE",
    );
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal,
    });
  } catch (err: any) {
    if (err?.name === "AbortError") throw err;
    const isTimeout = err?.name === "TimeoutError";
    throw new TextAnalysisError(
      isTimeout
        ? "The request timed out. The server may be busy — please try again."
        : "Unable to reach the analysis server. Please ensure the backend is running.",
      isTimeout ? "TIMEOUT" : "NETWORK",
    );
  }

  if (!response.ok) {
    let detail = `Server returned ${response.status}`;
    try {
      const body = await response.json();
      detail = body?.detail ?? detail;
    } catch {
      /* ignore parse error */
    }
    throw new TextAnalysisError(
      response.status >= 500
        ? `Server error (${response.status}): ${detail}. Please try again later.`
        : `Request failed (${response.status}): ${detail}`,
      "SERVER",
      response.status,
    );
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new TextAnalysisError(
      "The server returned an unreadable response. Please try again.",
      "INVALID_RESPONSE",
    );
  }

  if (
    data === null ||
    typeof data !== "object" ||
    typeof (data as any).trust_score !== "number"
  ) {
    throw new TextAnalysisError(
      "Unexpected response format from the server.",
      "INVALID_RESPONSE",
    );
  }

  return data as TextAnalysisResponse;
}

// ── Local History ──────────────────────────────────────────────────────────────

export function loadHistory(): AnalysisHistoryItem[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as AnalysisHistoryItem[];
  } catch {
    return [];
  }
}

export function saveToHistory(text: string, result: TextAnalysisResponse): void {
  try {
    const history = loadHistory();
    const item: AnalysisHistoryItem = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      timestamp: Date.now(),
      textPreview: text.slice(0, 100).trim(),
      result,
    };
    const updated = [item, ...history].slice(0, MAX_HISTORY);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  } catch {
    /* ignore storage errors */
  }
}

export function clearHistory(): void {
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch {
    /* ignore */
  }
}

// ── Export Helpers ─────────────────────────────────────────────────────────────

export function exportAsJson(result: TextAnalysisResponse, text: string): void {
  const payload = { analyzed_text: text, ...result };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  triggerDownload(blob, "technoax-analysis.json");
}

export function exportAsText(result: TextAnalysisResponse, text: string): void {
  const lines = [
    "TECHNOAX TEXT ANALYSIS REPORT",
    "=".repeat(40),
    `Trust Score:            ${result.trust_score} / 100`,
    `Trust Meter:            ${result.trust_meter}`,
    `Risk Level:             ${result.risk_level}`,
    `AI Generated Prob:      ${result.ai_generated_probability}%`,
    "",
    "AI EXPLANATION",
    "-".repeat(40),
    result.ai_explanation,
    "",
    "AI GENERATION EXPLANATION",
    "-".repeat(40),
    result.ai_generation_explanation,
    "",
    "RECOMMENDATION",
    "-".repeat(40),
    result.recommendation,
    "",
    "DETECTED PATTERNS",
    "-".repeat(40),
    result.detected_patterns.join(", ") || "None",
    "",
    "ANALYZED TEXT",
    "-".repeat(40),
    text,
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  triggerDownload(blob, "technoax-analysis.txt");
}

export function exportAsPdf(): void {
  window.print();
}

export function copyReportText(result: TextAnalysisResponse, text: string): string {
  return [
    `Trust Score: ${result.trust_score}/100 | ${result.trust_meter}`,
    `Risk Level: ${result.risk_level} | AI Prob: ${result.ai_generated_probability}%`,
    `Patterns: ${result.detected_patterns.join(", ") || "None"}`,
    ``,
    `AI Explanation: ${result.ai_explanation}`,
    `Recommendation: ${result.recommendation}`,
    ``,
    `Analyzed Text: ${text.slice(0, 300)}${text.length > 300 ? "…" : ""}`,
  ].join("\n");
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}
