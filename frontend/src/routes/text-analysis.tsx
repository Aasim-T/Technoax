import { createFileRoute } from "@tanstack/react-router";
import { SiteLayout } from "@/components/site/SiteLayout";
import { motion, AnimatePresence } from "framer-motion";
import React, { useState, useRef, useCallback, useEffect } from "react";
import {
  Loader2, ShieldCheck, ShieldAlert, Sparkles, Brain, AlertTriangle,
  ChevronRight, Copy, FileJson, FileText, Printer, History,
  Trash2, ChevronDown, ChevronUp, Search, CheckCircle2, FileSearch,
  Zap, Info, Clock, X,
} from "lucide-react";
import {
  analyzeText,
  saveToHistory,
  loadHistory,
  clearHistory,
  exportAsJson,
  exportAsText,
  exportAsPdf,
  copyReportText,
  TextAnalysisError,
} from "@/services/textAnalysisService";
import type { TextAnalysisResponse, AnalysisHistoryItem } from "@/types/textAnalysis";

export const Route = createFileRoute("/text-analysis")({
  head: () => ({
    meta: [
      { title: "Text Analysis — Technoax" },
      {
        name: "description",
        content:
          "Analyze any text for manipulation, AI generation, fear tactics, clickbait, and conspiracy framing with Technoax.",
      },
    ],
  }),
  component: TextAnalysisPage,
});

// ── Example Inputs ────────────────────────────────────────────────────────────

const EXAMPLES = [
  {
    label: "Safe Article",
    icon: ShieldCheck,
    color: "text-success",
    text: "Scientists at the University of Cambridge have published new research on renewable energy storage. The study, peer-reviewed in Nature Energy, demonstrates that sodium-ion batteries could reduce costs by 30% compared to lithium-ion alternatives. The team tested over 200 prototypes across three years and found consistent results in cold climates. The research has been independently verified by labs in Germany and South Korea.",
  },
  {
    label: "Clickbait News",
    icon: Zap,
    color: "text-warning",
    text: "You WON'T BELIEVE what this doctor discovered! Big Pharma has been hiding this SECRET remedy for DECADES! Click now before they DELETE this article! Thousands of people are CURING themselves at home with this ONE WEIRD TRICK that doctors absolutely HATE! Share before it's too late!!!",
  },
  {
    label: "Fear Content",
    icon: AlertTriangle,
    color: "text-danger",
    text: "WARNING: The government is planning to shut down ALL independent news sources within 90 days. Martial law is imminent. Stores will run out of food and water. Your bank accounts could be FROZEN without notice. Prepare immediately — stock up on emergency supplies, withdraw your cash NOW, and tell everyone you know before it's too late. There is no time left.",
  },
  {
    label: "Conspiracy Content",
    icon: Brain,
    color: "text-purple-600",
    text: "The global elite have been orchestrating world events through a secret cabal operating since 1913. The moon landing was filmed in a Hollywood studio. 5G towers are activating nanoparticles injected through vaccines to control the population. The mainstream media is fully controlled and nothing they report is real. The truth is being suppressed by shadowy organizations that have infiltrated every government.",
  },
  {
    label: "AI Generated",
    icon: Sparkles,
    color: "text-primary",
    text: "In the contemporary digital landscape, the proliferation of artificial intelligence technologies has fundamentally transformed the paradigm of information dissemination and consumption. It is imperative to acknowledge that the multifaceted implications of such technological advancements necessitate a comprehensive and nuanced understanding of the underlying mechanisms. Furthermore, the synergistic integration of machine learning algorithms with natural language processing capabilities has engendered unprecedented opportunities for automated content generation.",
  },
];

// ── Category Color Map ────────────────────────────────────────────────────────

const CATEGORY_COLORS: Record<string, { bg: string; text: string; chip: string; mark: string }> = {
  fear:        { bg: "bg-red-100",    text: "text-red-700",    chip: "border-red-200 bg-red-50 text-red-700",      mark: "#fecaca" },
  urgency:     { bg: "bg-orange-100", text: "text-orange-700", chip: "border-orange-200 bg-orange-50 text-orange-700", mark: "#fed7aa" },
  clickbait:   { bg: "bg-yellow-100", text: "text-yellow-700", chip: "border-yellow-200 bg-yellow-50 text-yellow-700", mark: "#fef08a" },
  conspiracy:  { bg: "bg-purple-100", text: "text-purple-700", chip: "border-purple-200 bg-purple-50 text-purple-700", mark: "#e9d5ff" },
  emotional:   { bg: "bg-pink-100",   text: "text-pink-700",   chip: "border-pink-200 bg-pink-50 text-pink-700",    mark: "#fbcfe8" },
  manipulation:{ bg: "bg-rose-100",   text: "text-rose-700",   chip: "border-rose-200 bg-rose-50 text-rose-700",    mark: "#fecdd3" },
};

function getCategoryStyle(category: string) {
  const key = category.toLowerCase();
  return CATEGORY_COLORS[key] ?? { bg: "bg-gray-100", text: "text-gray-700", chip: "border-gray-200 bg-gray-50 text-gray-700", mark: "#e5e7eb" };
}

// ── Trust Score Ring ──────────────────────────────────────────────────────────

function TrustScoreRing({ score }: { score: number }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color =
    score >= 70 ? "#16a34a" : score >= 40 ? "#d97706" : "#dc2626";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="140" height="140" className="-rotate-90">
        <circle cx="70" cy="70" r={radius} stroke="#f3f4f6" strokeWidth="12" fill="none" />
        <motion.circle
          cx="70"
          cy="70"
          r={radius}
          stroke={color}
          strokeWidth="12"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="font-display text-4xl font-semibold"
          style={{ color }}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
        >
          {score}
        </motion.span>
        <span className="text-xs text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
}

// ── Trust Meter Badge ─────────────────────────────────────────────────────────

function TrustMeterBadge({ meter }: { meter: string }) {
  const map: Record<string, { cls: string; icon: typeof ShieldCheck }> = {
    "High Trust":     { cls: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: ShieldCheck },
    "Moderate Trust": { cls: "bg-amber-50 text-amber-700 border-amber-200",       icon: Info },
    "Low Trust":      { cls: "bg-red-50 text-red-700 border-red-200",             icon: ShieldAlert },
  };
  const { cls, icon: Icon } = map[meter] ?? { cls: "bg-gray-50 text-gray-700 border-gray-200", icon: Info };
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm font-semibold ${cls}`}>
      <Icon size={15} />
      {meter}
    </span>
  );
}

// ── Risk Level Badge ──────────────────────────────────────────────────────────

function RiskLevelBadge({ level }: { level: string }) {
  const map: Record<string, string> = {
    Low:      "bg-emerald-50 text-emerald-700 border-emerald-200",
    Medium:   "bg-amber-50 text-amber-700 border-amber-200",
    High:     "bg-orange-50 text-orange-700 border-orange-200",
    Critical: "bg-red-50 text-red-700 border-red-200",
  };
  const cls = map[level] ?? "bg-gray-50 text-gray-700 border-gray-200";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${cls}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {level}
    </span>
  );
}

// ── Manipulation Heatmap ──────────────────────────────────────────────────────

function ManipulationHeatmap({
  text,
  heatmap,
}: {
  text: string;
  heatmap: { word: string; start_index: number; end_index: number; category: string }[];
}) {
  if (!heatmap.length || !text) {
    return (
      <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">{text}</p>
    );
  }

  // Sort heatmap entries by start_index to process in order
  const sorted = [...heatmap].sort((a, b) => a.start_index - b.start_index);

  // Build segments: plain text and highlighted spans
  const segments: React.ReactElement[] = [];
  let cursor = 0;

  sorted.forEach((entry, i) => {
    const start = Math.max(cursor, entry.start_index);
    const end = Math.min(text.length, entry.end_index);
    if (start >= end) return; // skip overlapping or invalid entries

    // Plain text before this highlight
    if (start > cursor) {
      segments.push(<span key={`plain-${i}`}>{text.slice(cursor, start)}</span>);
    }

    const { mark } = getCategoryStyle(entry.category);
    segments.push(
      <mark
        key={`mark-${i}`}
        title={entry.category}
        style={{ backgroundColor: mark, borderRadius: "3px", padding: "0 2px" }}
      >
        {text.slice(start, end)}
      </mark>,
    );
    cursor = end;
  });

  // Any remaining plain text after the last highlight
  if (cursor < text.length) {
    segments.push(<span key="plain-end">{text.slice(cursor)}</span>);
  }

  return (
    <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">{segments}</p>
  );
}

// ── Matched Words Table ───────────────────────────────────────────────────────

function MatchedWordsTable({
  words,
}: {
  words: { word: string; category: string; severity: string }[];
}) {
  const [search, setSearch] = useState("");
  const filtered = words.filter(
    (w) =>
      w.word.toLowerCase().includes(search.toLowerCase()) ||
      w.category.toLowerCase().includes(search.toLowerCase()) ||
      w.severity.toLowerCase().includes(search.toLowerCase()),
  );

  const severityOrder: Record<string, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 };

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          id="matched-words-search"
          type="text"
          placeholder="Search words, categories…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-md border border-border bg-surface/60 py-2 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {filtered.length === 0 ? (
        <p className="text-center text-sm text-muted-foreground py-4">No matches found.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface/60">
                <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Word</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Category</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Severity</th>
              </tr>
            </thead>
            <tbody>
              {[...filtered]
                .sort((a, b) => (severityOrder[a.severity] ?? 9) - (severityOrder[b.severity] ?? 9))
                .map((w, i) => {
                  const { chip } = getCategoryStyle(w.category);
                  const sevCls =
                    w.severity === "Critical" ? "text-red-700 bg-red-50 border-red-200"
                    : w.severity === "High" ? "text-orange-700 bg-orange-50 border-orange-200"
                    : w.severity === "Medium" ? "text-amber-700 bg-amber-50 border-amber-200"
                    : "text-gray-700 bg-gray-50 border-gray-200";
                  return (
                    <tr key={i} className="border-b border-border last:border-0 hover:bg-surface/40">
                      <td className="px-4 py-2.5 font-medium">{w.word}</td>
                      <td className="px-4 py-2.5">
                        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${chip}`}>
                          {w.category}
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${sevCls}`}>
                          {w.severity}
                        </span>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── AI Probability Gauge ──────────────────────────────────────────────────────

function AiProbabilityGauge({ probability }: { probability: number }) {
  const color =
    probability >= 70 ? "#dc2626" : probability >= 40 ? "#d97706" : "#16a34a";
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <motion.span
          className="font-display text-3xl font-semibold"
          style={{ color }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {probability}%
        </motion.span>
        <span className="text-xs text-muted-foreground">AI Generated Probability</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-muted">
        <motion.div
          className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${color}99, ${color})` }}
          initial={{ width: 0 }}
          animate={{ width: `${probability}%` }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        {probability >= 70 ? "Likely AI-generated content" : probability >= 40 ? "Possibly AI-assisted" : "Likely human-written"}
      </p>
    </div>
  );
}

// ── History Panel ─────────────────────────────────────────────────────────────

function HistoryPanel({
  history,
  onSelect,
  onClear,
}: {
  history: AnalysisHistoryItem[];
  onSelect: (item: AnalysisHistoryItem) => void;
  onClear: () => void;
}) {
  const [open, setOpen] = useState(false);

  if (history.length === 0) return null;

  return (
    <div className="surface-card overflow-hidden">
      <button
        id="history-toggle-btn"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-6 py-4 text-sm font-semibold hover:bg-surface/50 transition"
      >
        <span className="flex items-center gap-2">
          <History size={16} className="text-primary" />
          Analysis History
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">{history.length}</span>
        </span>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="border-t border-border px-6 pb-4 pt-3">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-xs text-muted-foreground">Last {history.length} analyses (stored locally)</p>
                <button
                  id="history-clear-btn"
                  onClick={onClear}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-danger transition"
                >
                  <Trash2 size={12} /> Clear all
                </button>
              </div>
              <ul className="space-y-2">
                {history.map((item) => (
                  <li key={item.id}>
                    <button
                      onClick={() => onSelect(item)}
                      className="flex w-full items-start gap-3 rounded-lg border border-border bg-surface/40 p-3 text-left hover:border-primary/30 hover:bg-primary/[0.03] transition"
                    >
                      <Clock size={14} className="mt-0.5 shrink-0 text-muted-foreground" />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-xs font-medium">{item.textPreview}{item.textPreview.length === 100 ? "…" : ""}</p>
                        <div className="mt-1 flex items-center gap-3">
                          <span className="text-xs text-muted-foreground">
                            {new Date(item.timestamp).toLocaleString()}
                          </span>
                          <RiskLevelBadge level={item.result.risk_level} />
                          <span className="text-xs text-muted-foreground">Score: {item.result.trust_score}</span>
                        </div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Copy Button ───────────────────────────────────────────────────────────────

function CopyButton({ text, label, id }: { text: string; label: string; id: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      id={id}
      onClick={handleCopy}
      className="flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted transition"
    >
      {copied ? <CheckCircle2 size={13} className="text-success" /> : <Copy size={13} />}
      {copied ? "Copied!" : label}
    </button>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

function TextAnalysisPage() {
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TextAnalysisResponse | null>(null);
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!inputText.trim() || loading) return;
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeText({ text: inputText.trim() }, abortRef.current.signal);
      setResult(data);
      saveToHistory(inputText.trim(), data);
      setHistory(loadHistory());
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (err: any) {
      if (err?.name === "AbortError") return;
      setError(
        err instanceof TextAnalysisError
          ? err.message
          : "An unexpected error occurred. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }, [inputText, loading]);

  const handleHistorySelect = useCallback((item: AnalysisHistoryItem) => {
    setInputText(item.result.ai_explanation ? inputText : "");
    setResult(item.result);
    setError(null);
    setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  }, [inputText]);

  const handleClearHistory = useCallback(() => {
    clearHistory();
    setHistory([]);
  }, []);

  const charCount = inputText.length;
  const MAX_CHARS = 10000;

  return (
    <SiteLayout>
      <div className="mx-auto max-w-5xl px-6 pb-24 pt-8 print:pt-0">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Technoax</span>
            <ChevronRight size={12} />
            <span className="text-foreground">Text Analysis</span>
          </div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">
            Text Analysis
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Detect manipulation, AI generation, fear tactics, clickbait, and conspiracy framing in any text.
          </p>
        </div>

        {/* Example Inputs */}
        <div className="mb-6">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Try an example
          </p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.label}
                id={`example-${ex.label.toLowerCase().replace(/\s+/g, "-")}`}
                onClick={() => setInputText(ex.text)}
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium hover:border-primary/40 hover:bg-primary/[0.04] transition"
              >
                <ex.icon size={12} className={ex.color} />
                {ex.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Area */}
        <div className="surface-card overflow-hidden print:hidden">
          <div className="p-6">
            <label htmlFor="analysis-textarea" className="mb-2 block text-sm font-semibold">
              Paste your content
            </label>
            <textarea
              id="analysis-textarea"
              value={inputText}
              onChange={(e) => setInputText(e.target.value.slice(0, MAX_CHARS))}
              placeholder="Paste an article, social media post, news headline, message, transcript, or any text you want to analyze…"
              rows={8}
              className="w-full resize-y rounded-lg border border-border bg-surface/40 p-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition"
            />
            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()} characters
              </span>
              {inputText && (
                <button
                  id="clear-input-btn"
                  onClick={() => { setInputText(""); setResult(null); setError(null); }}
                  className="flex items-center gap-1 hover:text-danger transition"
                >
                  <X size={12} /> Clear
                </button>
              )}
            </div>
          </div>

          <div className="border-t border-border bg-surface/30 px-6 py-4">
            <button
              id="analyze-btn"
              disabled={!inputText.trim() || loading}
              onClick={handleAnalyze}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground transition hover:bg-primary-soft disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  Analyzing content…
                </>
              ) : (
                <>
                  <FileSearch size={15} />
                  Analyze Text
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error State */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-4 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4"
            >
              <AlertTriangle size={16} className="mt-0.5 shrink-0 text-danger" />
              <div>
                <p className="text-sm font-semibold text-danger">Analysis Failed</p>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Results ─────────────────────────────────────────────────────── */}
        <AnimatePresence>
          {result && (
            <motion.div
              ref={resultsRef}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mt-8 space-y-6"
              id="analysis-results"
            >
              {/* Summary Row */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {/* Trust Score */}
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 }}
                  className="surface-card flex flex-col items-center gap-2 p-5"
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Trust Score</p>
                  <div className="relative flex items-center justify-center">
                    <TrustScoreRing score={result.trust_score} />
                  </div>
                </motion.div>

                {/* Trust Meter */}
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="surface-card flex flex-col items-center justify-center gap-3 p-5"
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Trust Meter</p>
                  <TrustMeterBadge meter={result.trust_meter} />
                  <p className="text-center text-xs text-muted-foreground">Overall content trustworthiness</p>
                </motion.div>

                {/* Risk Level */}
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 }}
                  className="surface-card flex flex-col items-center justify-center gap-3 p-5"
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Risk Level</p>
                  <RiskLevelBadge level={result.risk_level} />
                  <p className="text-center text-xs text-muted-foreground">Manipulation risk classification</p>
                </motion.div>

                {/* Signals Detected */}
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="surface-card flex flex-col items-center justify-center gap-3 p-5"
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Signals Detected</p>
                  <span className="font-display text-4xl font-light text-foreground">
                    {result.detected_patterns.length}
                  </span>
                  <p className="text-center text-xs text-muted-foreground">Manipulation patterns found</p>
                </motion.div>
              </div>

              {/* AI Probability */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25 }}
                className="surface-card p-6"
              >
                <div className="mb-4">
                  <h3 className="text-sm font-semibold">AI Generation Probability</h3>
                  <p className="mt-1 text-xs text-muted-foreground">Likelihood this content was generated by an AI model</p>
                </div>
                <AiProbabilityGauge probability={result.ai_generated_probability} />
              </motion.div>

              {/* Detected Patterns */}
              {result.detected_patterns.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="surface-card p-6"
                >
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold">Detected Patterns</h3>
                    <p className="mt-1 text-xs text-muted-foreground">Manipulation categories identified in the text</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {result.detected_patterns.map((p) => {
                      const { chip } = getCategoryStyle(p);
                      return (
                        <span
                          key={p}
                          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold capitalize ${chip}`}
                        >
                          <span className="h-1.5 w-1.5 rounded-full bg-current" />
                          {p}
                        </span>
                      );
                    })}
                  </div>
                </motion.div>
              )}

              {/* AI Explanation + AI Gen Explanation + Recommendation */}
              <div className="grid gap-6 lg:grid-cols-3">
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.35 }}
                  className="surface-card p-6"
                >
                  <div className="mb-4 flex items-center gap-2">
                    <div className="grid h-8 w-8 place-items-center rounded-md bg-primary/10 text-primary">
                      <Brain size={15} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold">AI Explanation</h3>
                      <p className="text-xs text-muted-foreground">Why this content was flagged</p>
                    </div>
                  </div>
                  <p className="text-sm leading-relaxed text-muted-foreground">{result.ai_explanation || "No explanation provided."}</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="surface-card p-6"
                >
                  <div className="mb-4 flex items-center gap-2">
                    <div className="grid h-8 w-8 place-items-center rounded-md bg-purple-100 text-purple-600">
                      <Sparkles size={15} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold">AI Generation Analysis</h3>
                      <p className="text-xs text-muted-foreground">Signals of synthetic authorship</p>
                    </div>
                  </div>
                  <p className="text-sm leading-relaxed text-muted-foreground">{result.ai_generation_explanation || "No analysis provided."}</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.45 }}
                  className="surface-card p-6"
                >
                  <div className="mb-4 flex items-center gap-2">
                    <div className="grid h-8 w-8 place-items-center rounded-md bg-emerald-100 text-emerald-600">
                      <ShieldCheck size={15} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold">Recommendation</h3>
                      <p className="text-xs text-muted-foreground">Suggested action</p>
                    </div>
                  </div>
                  <p className="text-sm leading-relaxed text-muted-foreground">{result.recommendation || "No recommendation provided."}</p>
                </motion.div>
              </div>

              {/* Manipulation Heatmap */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="surface-card p-6"
              >
                <div className="mb-4">
                  <h3 className="text-sm font-semibold">Manipulation Heatmap</h3>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Highlighted words indicate detected manipulation patterns.
                  </p>
                </div>

                {/* Legend */}
                {result.manipulation_heatmap.length > 0 && (
                  <div className="mb-3 flex flex-wrap gap-2">
                    {Object.entries(CATEGORY_COLORS).map(([cat, colors]) => (
                      <span key={cat} className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                        <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: colors.mark }} />
                        <span className="capitalize">{cat}</span>
                      </span>
                    ))}
                  </div>
                )}

                <div className="rounded-lg border border-border bg-surface/40 p-4">
                  <ManipulationHeatmap
                    text={inputText.trim() || result.ai_explanation}
                    heatmap={result.manipulation_heatmap}
                  />
                </div>
              </motion.div>

              {/* Matched Words Table */}
              {result.matched_words.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.55 }}
                  className="surface-card p-6"
                >
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold">Matched Words</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {result.matched_words.length} flagged term{result.matched_words.length !== 1 ? "s" : ""} found
                    </p>
                  </div>
                  <MatchedWordsTable words={result.matched_words} />
                </motion.div>
              )}

              {/* Export + Copy Panel */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="surface-card p-6 print:hidden"
              >
                <div className="mb-4">
                  <h3 className="text-sm font-semibold">Export & Share</h3>
                  <p className="mt-1 text-xs text-muted-foreground">Download the analysis or copy to clipboard</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    id="export-pdf-btn"
                    onClick={exportAsPdf}
                    className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted transition"
                  >
                    <Printer size={13} /> Export PDF
                  </button>
                  <button
                    id="export-json-btn"
                    onClick={() => exportAsJson(result, inputText.trim())}
                    className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted transition"
                  >
                    <FileJson size={13} /> Download JSON
                  </button>
                  <button
                    id="export-txt-btn"
                    onClick={() => exportAsText(result, inputText.trim())}
                    className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted transition"
                  >
                    <FileText size={13} /> Download Text
                  </button>
                  <div className="ml-2 h-6 w-px bg-border" />
                  <CopyButton
                    id="copy-report-btn"
                    text={copyReportText(result, inputText.trim())}
                    label="Copy Report"
                  />
                  <CopyButton
                    id="copy-json-btn"
                    text={JSON.stringify(result, null, 2)}
                    label="Copy JSON"
                  />
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* History Panel */}
        <div className="mt-8 print:hidden">
          <HistoryPanel
            history={history}
            onSelect={handleHistorySelect}
            onClear={handleClearHistory}
          />
        </div>
      </div>

      {/* Print styles */}
      <style>{`
        @media print {
          header, nav, .print\\:hidden { display: none !important; }
          #analysis-results { page-break-inside: avoid; }
          body { background: white !important; }
          .surface-card { border: 1px solid #e5e7eb !important; box-shadow: none !important; }
        }
      `}</style>
    </SiteLayout>
  );
}
