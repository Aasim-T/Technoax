/** Request body sent to POST /analyze-text */
export interface TextAnalysisRequest {
  text: string;
}

/** A single matched word entry from the backend */
export interface MatchedWord {
  word: string;
  category: string;
  severity: string;
}

/** A single manipulation heatmap entry — uses character offsets */
export interface ManipulationHeatmapEntry {
  word: string;
  category: string;
  severity: string;
  start_index: number;
  end_index: number;
}

/** API response from POST /analyze-text */
export interface TextAnalysisResponse {
  trust_score: number;
  trust_meter: "High Trust" | "Moderate Trust" | "Suspicious" | "High Risk" | string;
  risk_level: "Low" | "Medium" | "High" | "Critical" | string;
  detected_patterns: string[];
  matched_words: MatchedWord[];
  manipulation_heatmap: ManipulationHeatmapEntry[];
  ai_explanation: string;
  recommendation: string;
  ai_generated_probability: number;
  ai_generation_explanation: string;
}

/** One item stored in localStorage history */
export interface AnalysisHistoryItem {
  id: string;
  timestamp: number;
  textPreview: string;
  result: TextAnalysisResponse;
}

export type ExportFormat = "pdf" | "json" | "text";
