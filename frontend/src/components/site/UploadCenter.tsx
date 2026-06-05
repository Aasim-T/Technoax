import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  UploadCloud, FileVideo, FileImage, CheckCircle2,
  Loader2, X, ShieldCheck, ShieldAlert, AlertTriangle, Info,
} from "lucide-react";
import { analyzeVideo, type AnalysisResult } from "@/lib/api/client";

type Phase = "idle" | "uploading" | "analyzing" | "done" | "error";

type UploadFile = {
  name: string;
  size: number;
  type: string;
};

function RiskBadge({ score }: { score: number }) {
  if (score >= 70)
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 border border-red-200 px-3 py-1 text-xs font-semibold text-red-700">
        <ShieldAlert size={12} /> AI-Generated
      </span>
    );
  if (score >= 40)
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-xs font-semibold text-amber-700">
        <AlertTriangle size={12} /> Suspicious
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1 text-xs font-semibold text-emerald-700">
      <ShieldCheck size={12} /> Authentic
    </span>
  );
}

export function UploadCenter() {
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<UploadFile | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const startProcessing = useCallback(async (f: File) => {
    setFile({ name: f.name, size: f.size, type: f.type });
    setPhase("uploading");
    setProgress(0);
    setResult(null);
    setErrorMessage(null);

    // Animate progress bar while waiting for the backend
    let p = 0;
    const tick = setInterval(() => {
      p += Math.random() * 10 + 5;
      if (p >= 90) {
        p = 90; // hold at 90% until the response arrives
        clearInterval(tick);
      }
      setProgress(p);
    }, 200);

    try {
      setPhase("analyzing");

      // Single call — /analyze-video now returns full frame analysis too
      const analysisResult = await analyzeVideo(f);
      setResult(analysisResult);

      clearInterval(tick);
      setProgress(100);
      setPhase("done");
    } catch (err: any) {
      clearInterval(tick);
      setProgress(0);
      setPhase("error");
      setErrorMessage(
        err?.message?.includes("Failed to fetch")
          ? "Cannot reach the video analysis server. Make sure backend-video is running on port 8001."
          : err?.message || "An unexpected error occurred."
      );
    }
  }, []);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) startProcessing(f);
  };

  const reset = () => {
    setFile(null);
    setPhase("idle");
    setProgress(0);
    setResult(null);
    setErrorMessage(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="surface-card overflow-hidden">
      <div className="p-6">
        <label
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-16 text-center transition ${
            dragOver ? "border-primary bg-primary/[0.04]" : "border-border bg-surface/40 hover:border-white/15"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="video/*,image/*"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) startProcessing(f);
            }}
          />
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-primary/10 text-primary ring-1 ring-primary/20">
            <UploadCloud size={22} />
          </div>
          <h3 className="mt-5 text-lg font-semibold">Drag &amp; drop your media</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            MP4, MOV, WebM up to 500MB · JPG, PNG, WebP up to 50MB
          </p>
          <span className="mt-5 inline-flex items-center gap-2 rounded-md bg-card px-3 py-1.5 text-xs font-medium text-foreground ring-1 ring-border">
            or click to browse
          </span>
        </label>

        <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-2 rounded-lg border border-border bg-card/40 px-3 py-2">
            <FileVideo size={14} className="text-primary" /> Video — frame-by-frame analysis
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-border bg-card/40 px-3 py-2">
            <FileImage size={14} className="text-primary" /> Image — full pixel forensics
          </div>
        </div>

        <AnimatePresence>
          {file && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-6 space-y-4"
            >
              {/* File row */}
              <div className="rounded-xl border border-border bg-surface/60 p-4">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-card text-primary">
                    {file.type.startsWith("video") ? <FileVideo size={18} /> : <FileImage size={18} />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{file.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB ·{" "}
                      {phase === "uploading" && `Uploading ${Math.round(progress)}%`}
                      {phase === "analyzing" && "Running detection models…"}
                      {phase === "done" && "Analysis complete"}
                      {phase === "error" && "Analysis failed"}
                    </div>
                  </div>
                  <button
                    onClick={reset}
                    className="rounded-md p-1.5 text-muted-foreground hover:bg-card hover:text-foreground"
                  >
                    <X size={16} />
                  </button>
                </div>

                {phase !== "error" && (
                  <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-card">
                    <motion.div
                      className="h-full bg-gradient-to-r from-primary to-primary-soft"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.2 }}
                    />
                  </div>
                )}

                <div className="mt-4 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    {phase === "analyzing" && (
                      <><Loader2 size={14} className="animate-spin text-primary" /> Inference running across 4 models</>
                    )}
                    {phase === "uploading" && (
                      <><Loader2 size={14} className="animate-spin text-primary" /> Securely transferring</>
                    )}
                    {phase === "done" && (
                      <><CheckCircle2 size={14} className="text-success" /> Ready to view</>
                    )}
                    {phase === "error" && (
                      <><AlertTriangle size={14} className="text-danger" /> Failed</>
                    )}
                  </div>
                    {phase === "done" && (
                      <><CheckCircle2 size={14} className="text-success" /> Results ready below</>
                    )}
                </div>
              </div>

              {/* Error message */}
              {phase === "error" && errorMessage && (
                <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
                  <AlertTriangle size={15} className="mt-0.5 shrink-0 text-danger" />
                  <div>
                    <p className="text-sm font-semibold text-danger">Analysis Failed</p>
                    <p className="mt-1 text-xs text-red-700">{errorMessage}</p>
                  </div>
                </div>
              )}

              {/* Combined Analysis Results — all data from a single /analyze-video call */}
              {phase === "done" && result && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="rounded-xl border border-border bg-surface/60 p-5 space-y-4"
                >
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold">Analysis Results</h4>
                    <RiskBadge score={result.deepfake_probability ?? result.risk_score} />
                  </div>

                  {/* Quick stat tiles */}
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-center">
                    <div className="rounded-lg border border-border bg-card/60 p-3">
                      <div className="text-2xl font-semibold text-foreground">
                        {result.deepfake_probability != null
                          ? `${result.deepfake_probability}%`
                          : `${result.risk_score}%`}
                      </div>
                      <div className="mt-0.5 text-xs text-muted-foreground">AI Probability</div>
                    </div>
                    <div className="rounded-lg border border-border bg-card/60 p-3">
                      <div className="text-2xl font-semibold text-foreground">
                        {result.frames_analyzed}
                      </div>
                      <div className="mt-0.5 text-xs text-muted-foreground">Frames</div>
                    </div>
                    {result.fps != null && (
                      <div className="rounded-lg border border-border bg-card/60 p-3">
                        <div className="text-2xl font-semibold text-foreground">
                          {typeof result.fps === "number" ? result.fps.toFixed(1) : result.fps}
                        </div>
                        <div className="mt-0.5 text-xs text-muted-foreground">FPS</div>
                      </div>
                    )}
                    {result.duration_seconds != null && (
                      <div className="rounded-lg border border-border bg-card/60 p-3">
                        <div className="text-2xl font-semibold text-foreground">
                          {typeof result.duration_seconds === "number"
                            ? result.duration_seconds.toFixed(1)
                            : result.duration_seconds}s
                        </div>
                        <div className="mt-0.5 text-xs text-muted-foreground">Duration</div>
                      </div>
                    )}
                  </div>

                  {/* AI Probability bar */}
                  {(() => {
                    const pct = result.deepfake_probability ?? result.risk_score;
                    return (
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>AI Probability — <span className="font-medium text-foreground">
                            {pct >= 70 ? "High" : pct >= 40 ? "Medium" : "Low"}
                          </span></span>
                          <span>{pct}%</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted">
                          <motion.div
                            className="h-full rounded-full"
                            style={{
                              background:
                                pct >= 70
                                  ? "linear-gradient(90deg, #f87171, #dc2626)"
                                  : pct >= 40
                                  ? "linear-gradient(90deg, #fbbf24, #d97706)"
                                  : "linear-gradient(90deg, #4ade80, #16a34a)",
                            }}
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                          />
                        </div>
                      </div>
                    );
                  })()}

                  {/* Frame-level analysis details (embedded in same response) */}
                  {(result.faces_detected != null ||
                    result.deepfake_probability != null ||
                    result.blur_score != null ||
                    result.brightness != null) && (
                    <div className="border-t border-border pt-4 space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Frame Analysis
                      </p>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {result.faces_detected != null && (
                          <div className="flex justify-between rounded-md bg-card/40 px-3 py-2">
                            <span className="text-muted-foreground">Faces detected</span>
                            <span className="font-medium">{result.faces_detected}</span>
                          </div>
                        )}
                        {result.deepfake_probability != null && (
                          <div className="flex justify-between rounded-md bg-card/40 px-3 py-2">
                            <span className="text-muted-foreground">Deepfake prob.</span>
                            <span className="font-medium">{result.deepfake_probability}%</span>
                          </div>
                        )}
                        {result.blur_score != null && (
                          <div className="flex justify-between rounded-md bg-card/40 px-3 py-2">
                            <span className="text-muted-foreground">Blur score</span>
                            <span className="font-medium">{result.blur_score}</span>
                          </div>
                        )}
                        {result.brightness != null && (
                          <div className="flex justify-between rounded-md bg-card/40 px-3 py-2">
                            <span className="text-muted-foreground">Brightness</span>
                            <span className="font-medium">{result.brightness}</span>
                          </div>
                        )}
                      </div>

                      {result.explanation && (
                        <div className="flex items-start gap-2 rounded-md border border-border bg-card/40 p-3 text-xs text-muted-foreground">
                          <Info size={13} className="mt-0.5 shrink-0 text-primary" />
                          <p>{result.explanation}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* File metadata footer */}
                  {result.resolution && (
                    <p className="text-xs text-muted-foreground">
                      Resolution: {result.resolution} · {result.file_size_mb?.toFixed(2)} MB
                    </p>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
