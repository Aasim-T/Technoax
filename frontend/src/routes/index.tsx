import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  ShieldCheck, Scan, Activity, Eye, Brain, Radar,
  ArrowRight, CheckCircle2, AlertTriangle, Upload, Sparkles,
  FileSearch, Gauge,
} from "lucide-react";
import { SiteLayout } from "@/components/site/SiteLayout";
import { UploadCenter } from "@/components/site/UploadCenter";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Technoax — AI Media Intelligence & Deepfake Detection" },
      { name: "description", content: "Detect deepfakes, manipulated images, and misinformation in seconds with Technoax — an AI-powered media intelligence platform." },
    ],
  }),
  component: Home,
});

const features = [
  { icon: ShieldCheck, title: "Deepfake detection", desc: "Spot AI-generated faces and synthetic videos with high accuracy." },
  { icon: Scan, title: "Frame-by-frame analysis", desc: "Every frame is scanned for tampering, splicing, and edits." },
  { icon: Activity, title: "Risk score", desc: "A simple 0–100 score tells you how trustworthy the media is." },
  { icon: Eye, title: "Artifact detection", desc: "Find hidden traces left behind by editing and generation tools." },
  { icon: Brain, title: "Plain-English results", desc: "Understand exactly what was found and why it matters." },
  { icon: Radar, title: "Continuous monitoring", desc: "Watch live media streams in real time for suspicious patterns." },
];

const steps = [
  { icon: Upload, title: "1. Upload", desc: "Drop a video or image — MP4, MOV, JPG, PNG and more." },
  { icon: FileSearch, title: "2. Analyze", desc: "Our AI models run forensic checks across every frame." },
  { icon: Gauge, title: "3. Get results", desc: "See a clear risk score with a plain-English explanation." },
];

const stats = [
  { value: "98.4%", label: "Detection accuracy" },
  { value: "< 8s", label: "Avg analysis time" },
  { value: "4", label: "AI models combined" },
  { value: "50M+", label: "Frames analyzed" },
];

const techStack = ["React", "TanStack", "Tailwind CSS", "Framer Motion", "Recharts", "TypeScript", "Vite", "Lucide"];

function Home() {
  return (
    <SiteLayout>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border">
        {/* Soft gradient backdrop */}
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -top-32 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-gradient-to-br from-orange-100 via-amber-50 to-transparent blur-3xl" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(0,0,0,0.06)_1px,transparent_0)] [background-size:24px_24px] opacity-50" />
        </div>

        <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 md:grid-cols-2 md:py-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight md:text-5xl lg:text-6xl">
              Tech<span className="text-primary">noax</span>
            </h1>
            <p className="mt-5 max-w-lg text-base text-muted-foreground md:text-lg">
              This uses AI to detect deepfakes, manipulated images, and fake media.
              Upload a file and get a clear answer.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a href="#upload" className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground transition hover:bg-primary-soft">
                Analyze a file <ArrowRight size={16} />
              </a>
              <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-5 py-2.5 text-sm font-medium text-foreground hover:bg-muted">
                See sample report
              </Link>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
              {["Free to try", "No sign-up needed", "Your files stay private"].map((b) => (
                <span key={b} className="inline-flex items-center gap-1.5">
                  <CheckCircle2 size={12} className="text-success" /> {b}
                </span>
              ))}
            </div>
          </motion.div>

          {/* Visual demo: Real vs Fake comparison */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="relative"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <motion.div
                whileHover={{ y: -4 }}
                className="surface-card overflow-hidden"
              >
                <div className="relative aspect-[4/5] bg-gradient-to-br from-emerald-50 to-emerald-100">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="h-20 w-20 rounded-full bg-emerald-200/70 ring-8 ring-emerald-100/60" />
                  </div>
                  <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/90 px-2 py-1 text-[10px] font-semibold text-success ring-1 ring-emerald-200">
                    <CheckCircle2 size={10} /> AUTHENTIC
                  </span>
                </div>
                <div className="p-4">
                  <div className="text-xs text-muted-foreground">Risk score</div>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-2xl font-semibold text-success">4</span>
                    <span className="text-xs text-muted-foreground">/ 100</span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                    <motion.div
                      className="h-full bg-success"
                      initial={{ width: 0 }}
                      animate={{ width: "4%" }}
                      transition={{ duration: 1.2, delay: 0.6 }}
                    />
                  </div>
                </div>
              </motion.div>

              <motion.div
                whileHover={{ y: -4 }}
                className="surface-card relative overflow-hidden sm:mt-8"
              >
                <div className="relative aspect-[4/5] bg-gradient-to-br from-rose-50 to-orange-100">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="h-20 w-20 rounded-full bg-rose-200/70 ring-8 ring-rose-100/60" />
                  </div>
                  {/* Scan line */}
                  <motion.div
                    className="absolute inset-x-0 h-px bg-primary/60 shadow-[0_0_8px_rgba(234,88,12,0.6)]"
                    initial={{ top: "0%" }}
                    animate={{ top: ["0%", "100%", "0%"] }}
                    transition={{ duration: 2.4, repeat: Infinity, ease: "linear" }}
                  />
                  <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/90 px-2 py-1 text-[10px] font-semibold text-danger ring-1 ring-rose-200">
                    <AlertTriangle size={10} /> DEEPFAKE
                  </span>
                </div>
                <div className="p-4">
                  <div className="text-xs text-muted-foreground">Risk score</div>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-2xl font-semibold text-danger">92</span>
                    <span className="text-xs text-muted-foreground">/ 100</span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                    <motion.div
                      className="h-full bg-danger"
                      initial={{ width: 0 }}
                      animate={{ width: "92%" }}
                      transition={{ duration: 1.2, delay: 0.8 }}
                    />
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Floating badge */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 }}
              className="absolute -bottom-4 left-1/2 -translate-x-1/2 rounded-full border border-border bg-background px-4 py-2 text-xs font-medium shadow-sm"
            >
              <span className="inline-flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
                </span>
                Live analysis · 4 AI models running
              </span>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Stats strip */}
      <section className="border-b border-border bg-surface">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-6 py-10 md:grid-cols-4">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="text-center"
            >
              <div className="text-2xl font-semibold text-foreground md:text-3xl">{s.value}</div>
              <div className="mt-1 text-xs text-muted-foreground md:text-sm">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-xl text-center">
            <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">How it works</h2>
            <p className="mt-3 text-muted-foreground"></p>
          </div>
          <div className="relative mt-12 grid gap-6 md:grid-cols-3">
            {steps.map((s, i) => (
              <motion.div
                key={s.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="surface-card p-6"
              >
                <div className="grid h-10 w-10 place-items-center rounded-md bg-primary/10 text-primary">
                  <s.icon size={18} />
                </div>
                <h3 className="mt-4 text-base font-semibold">{s.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-border bg-surface py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-xl text-center">
            <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">What Technoax can do</h2>
            <p className="mt-3 text-muted-foreground">Simple tools that help you tell real media from fake.</p>
          </div>
          <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                whileHover={{ y: -3 }}
                className="surface-card p-6"
              >
                <div className="grid h-10 w-10 place-items-center rounded-md bg-primary/10 text-primary">
                  <f.icon size={18} />
                </div>
                <h3 className="mt-4 text-base font-semibold">{f.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>


      {/* Upload Section */}
      <section id="upload" className="border-t border-border py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-xl text-center mb-10">
            <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">Try it now</h2>
            <p className="mt-3 text-muted-foreground">
              Drop a video or image below and we'll analyze it for you.
            </p>
          </div>
          <div className="mx-auto max-w-2xl">
            <UploadCenter />
          </div>
        </div>
      </section>


      <section className="border-t border-border py-14">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Built with</p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
            {techStack.map((t) => (
              <span key={t} className="rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground">
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border bg-gradient-to-br from-orange-50 to-amber-50 py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">Ready to see how it works?</h2>
          <p className="mt-3 text-muted-foreground">Open the dashboard for a full sample analysis report.</p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary-soft">
              Open dashboard <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
