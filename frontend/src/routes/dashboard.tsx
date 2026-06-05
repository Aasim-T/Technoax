import { createFileRoute } from "@tanstack/react-router";
import { SiteLayout } from "@/components/site/SiteLayout";
import { motion } from "framer-motion";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from "recharts";
import {
  ShieldAlert, Activity, Gauge, Users, Sparkles, Film, Clock, Image as ImageIcon,
  AlertTriangle, ChevronRight,
} from "lucide-react";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Technoax" },
      { name: "description", content: "Realtime media intelligence dashboard with deepfake probability, risk scoring, and frame timeline." },
    ],
  }),
  component: Dashboard,
});

const riskDistribution = [
  { name: "Authentic", value: 38, color: "#16a34a" },
  { name: "Suspicious", value: 34, color: "#d97706" },
  { name: "Manipulated", value: 28, color: "#dc2626" },
];

const trendData = Array.from({ length: 24 }, (_, i) => ({
  t: `${i}`,
  risk: Math.round(40 + Math.sin(i / 2.5) * 18 + (i > 14 ? 18 : 0) + Math.random() * 5),
  conf: Math.round(70 + Math.cos(i / 3) * 10 + Math.random() * 4),
}));

const frames = Array.from({ length: 40 }, (_, i) => {
  const r = Math.sin(i / 3) * 0.5 + 0.5 + (i > 22 && i < 30 ? 0.4 : 0) + Math.random() * 0.1;
  const score = Math.min(1, r);
  return { i, score, suspicious: score > 0.7 };
});

function Dashboard() {
  return (
    <SiteLayout>
      <div className="mx-auto max-w-7xl px-6 pb-24">
        {/* Header */}
        <div className="flex flex-wrap items-end justify-between gap-4 pb-8">
          <div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>Analyses</span>
              <ChevronRight size={12} />
              <span className="text-foreground">clip-0421.mp4</span>
            </div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">Analysis Report</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Processed 2 minutes ago · Models: Forensic-v4, FaceGuard, ArtifactNet
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-warning/30 bg-warning/10 px-3 py-1 text-xs font-medium text-warning">
              <AlertTriangle size={12} /> Elevated risk
            </span>
            <button className="rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted">
              Export PDF
            </button>
            <button className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary-soft">
              Re-run
            </button>
          </div>
        </div>

        {/* KPI row */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Kpi icon={Gauge} label="Risk Score" value="72" tone="warning" sub="+12 vs prior" />
          <Kpi icon={ShieldAlert} label="Threat Level" value="High" tone="danger" sub="2 critical regions" />
          <Kpi icon={Activity} label="Confidence" value="94%" tone="success" sub="Ensemble agreement" />
          <Kpi icon={Sparkles} label="Deepfake Prob." value="89%" tone="danger" sub="Face-swap detected" />
        </div>

        {/* Main grid */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          {/* Risk distribution — simplified */}
          <Card title="Risk Distribution" subtitle="Across all analyzed frames">
            <ul className="space-y-3 text-sm">
              {riskDistribution.map((d) => (
                <li key={d.name}>
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-2 text-muted-foreground">
                      <span className="h-2 w-2 rounded-full" style={{ background: d.color }} />
                      {d.name}
                    </span>
                    <span className="font-medium text-foreground">{d.value}%</span>
                  </div>
                  <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${d.value}%`, background: d.color }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </Card>

          {/* Analysis summary */}
          <Card title="Analysis Summary" subtitle="Composite signals">
            <ul className="space-y-3 text-sm">
              <Row label="Deepfake Probability" value="89%" tone="danger" />
              <Row label="Faces Detected" value="3 unique" />
              <Row label="Blur Score" value="0.18" />
              <Row label="Brightness Score" value="0.62" />
              <Row label="Audio-Visual Sync" value="0.41" tone="warning" />
              <Row label="Compression Anomalies" value="7 zones" tone="warning" />
            </ul>
          </Card>

          {/* Metadata */}
          <Card title="Video Metadata" subtitle="Source file properties">
            <ul className="grid grid-cols-2 gap-3 text-sm">
              <Meta icon={Clock} label="Duration" value="2m 41s" />
              <Meta icon={Film} label="FPS" value="29.97" />
              <Meta icon={ImageIcon} label="Resolution" value="1920×1080" />
              <Meta icon={Users} label="File Size" value="84.2 MB" />
              <Meta icon={Sparkles} label="Codec" value="H.264" />
              <Meta icon={Activity} label="Bitrate" value="4.1 Mbps" />
            </ul>
          </Card>
        </div>

        {/* Frame timeline + Trend */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2" title="Frame Timeline" subtitle="Suspicious frame markers across the clip">
            <div className="space-y-3">
              <div className="flex h-16 items-end gap-[3px] rounded-lg border border-border bg-surface/60 p-2">
                {frames.map((f) => (
                  <div
                    key={f.i}
                    className="w-full rounded-sm transition-all hover:opacity-100"
                    style={{
                      height: `${Math.max(8, f.score * 100)}%`,
                      background: f.suspicious ? "#dc2626" : f.score > 0.45 ? "#d97706" : "#d1d5db",
                      opacity: f.suspicious ? 1 : 0.85,
                    }}
                    title={`Frame ${f.i} · ${(f.score * 100).toFixed(0)}%`}
                  />
                ))}
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>00:00</span>
                <div className="flex items-center gap-4">
                  <Legend color="#d1d5db" label="Clean" />
                  <Legend color="#d97706" label="Suspicious" />
                  <Legend color="#dc2626" label="Manipulated" />
                </div>
                <span>02:41</span>
              </div>
            </div>
          </Card>

          {/* Threat Category Breakdown removed */}
        </div>

        {/* Trend + AI Explain */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2" title="Frame Analysis Trend" subtitle="Risk and confidence over time">
            <div className="h-64">
              <ResponsiveContainer>
                <AreaChart data={trendData} margin={{ left: -10, right: 8, top: 8 }}>
                  <defs>
                    <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ea580c" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#ea580c" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#16a34a" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="#16a34a" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#f3f4f6" />
                  <XAxis dataKey="t" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle} />
                  <Area type="monotone" dataKey="risk" stroke="#ea580c" strokeWidth={2} fill="url(#g1)" />
                  <Area type="monotone" dataKey="conf" stroke="#16a34a" strokeWidth={2} fill="url(#g2)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* AI Explanation — simplified */}
          <Card title="AI Explanation" subtitle="Why this clip was flagged">
            <ul className="space-y-3 text-sm">
              <li className="flex gap-2">
                <span className="text-danger font-medium">Face-swap detected:</span>
                <span className="text-muted-foreground">Inconsistent specular highlights around the left eye in frames 412–786.</span>
              </li>
              <li className="flex gap-2">
                <span className="text-warning font-medium">Lip-sync drift:</span>
                <span className="text-muted-foreground">Audio leads video by ~120ms in 14% of segments.</span>
              </li>
              <li className="flex gap-2">
                <span className="text-success font-medium">Recommendation:</span>
                <span className="text-muted-foreground">Flag for human review and request original camera metadata.</span>
              </li>
            </ul>
          </Card>
        </div>
      </div>
    </SiteLayout>
  );
}

const tooltipStyle = {
  contentStyle: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    fontSize: 12,
    color: "#111111",
  },
  cursor: { fill: "rgba(0,0,0,0.04)" },
};

function Kpi({
  icon: Icon, label, value, sub, tone,
}: { icon: any; label: string; value: string; sub: string; tone: "warning" | "danger" | "success" | "muted" }) {
  const t =
    tone === "danger" ? "text-danger" :
    tone === "warning" ? "text-warning" :
    tone === "success" ? "text-success" : "text-foreground";
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="surface-card flex items-start justify-between p-5"
    >
      <div>
        <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
        <div className={`mt-2 font-display text-3xl font-light ${t}`}>{value}</div>
        <div className="mt-1 text-xs text-muted-foreground">{sub}</div>
      </div>
      <div className={`grid h-9 w-9 place-items-center rounded-md bg-card ${t}`}>
        <Icon size={16} />
      </div>
    </motion.div>
  );
}

function Card({
  title, subtitle, children, className = "",
}: { title: string; subtitle?: string; children: React.ReactNode; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4 }}
      className={`surface-card p-6 ${className}`}
    >
      <div className="mb-5">
        <h3 className="text-sm font-semibold">{title}</h3>
        {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
      </div>
      {children}
    </motion.div>
  );
}

function Row({ label, value, tone }: { label: string; value: string; tone?: "danger" | "warning" }) {
  const t = tone === "danger" ? "text-danger" : tone === "warning" ? "text-warning" : "text-foreground";
  return (
    <li className="flex items-center justify-between border-b border-border pb-2 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className={`font-medium ${t}`}>{value}</span>
    </li>
  );
}

function Meta({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <li className="rounded-lg border border-border bg-surface/40 p-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon size={12} className="text-primary" /> {label}
      </div>
      <div className="mt-1 text-sm font-medium">{value}</div>
    </li>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-sm" style={{ background: color }} />
      {label}
    </span>
  );
}
