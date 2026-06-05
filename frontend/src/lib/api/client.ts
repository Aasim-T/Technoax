// API Service Configuration
// Connects to the FastAPI video-analysis backend (backend-video) on port 8001

export const VIDEO_API_BASE_URL =
  (import.meta as any).env?.VITE_VIDEO_API_URL || "http://localhost:8001";

/**
 * Combined result returned by POST /analyze-video.
 * The backend now runs full multi-frame analysis and returns everything
 * in a single response — no second /frame-analysis call needed.
 */
export interface AnalysisResult {
  // Core
  risk_score: number;
  risk_level: "Low" | "Medium" | "High" | string;
  status: "authentic" | "deepfake" | "inconclusive" | "Processed" | string;
  filename?: string;

  // Video metadata
  frames_analyzed: number;
  fps?: number;
  duration_seconds?: number;
  resolution?: string;
  file_size_mb?: number;

  // Frame-level analysis (embedded in the single response)
  faces_detected?: number;
  blur_score?: number;
  brightness?: number;
  deepfake_probability?: number;
  explanation?: string;

  // Legacy / optional
  analysis_details?: string;
  processing_time?: number;
}

/** Kept for backward-compat with the standalone /frame-analysis route */
export interface FrameAnalysisResult {
  frame: string;
  faces_detected: number;
  blur_score: number;
  brightness: number;
  deepfake_probability: number;
  risk_score: number;
  risk_level: string;
  explanation: string;
}

// Analyze video — POST /analyze-video
// Returns full analysis including frame-level metrics in one round-trip.
export async function analyzeVideo(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${VIDEO_API_BASE_URL}/analyze-video`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(`Analysis failed: ${text}`);
  }
  return response.json();
}

// Frame analysis — GET /frame-analysis (standalone; only call if you need it separately)
export async function getFrameAnalysis(): Promise<FrameAnalysisResult> {
  const response = await fetch(`${VIDEO_API_BASE_URL}/frame-analysis`);

  if (!response.ok) {
    throw new Error(`Frame analysis failed: ${response.statusText}`);
  }
  return response.json();
}

// Risk score — POST /media-risk-score
export async function calculateRiskScore(
  file: File
): Promise<{ risk_score: number; confidence: number }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${VIDEO_API_BASE_URL}/media-risk-score`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Risk score calculation failed: ${response.statusText}`);
  }
  return response.json();
}

// Health check — GET /health
export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${VIDEO_API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}
