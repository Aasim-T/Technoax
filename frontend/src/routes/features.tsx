import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteLayout } from "@/components/site/SiteLayout";
import {
  ShieldCheck, Scan, Activity, Eye, Brain, Radar, Lock, Network, Workflow, Zap, Database, Globe, ArrowRight,
} from "lucide-react";

export const Route = createFileRoute("/features")({
  head: () => ({
    meta: [
      { title: "Features — Technoax" },
      { name: "description", content: "Detection capabilities across deepfakes, artifacts, risk scoring and explainable AI reasoning." },
    ],
  }),
  component: FeaturesPage,
});

const main = [
  { icon: ShieldCheck, title: "Deepfake Detection", desc: "Ensemble of CNN, transformer, and frequency-domain models surface synthetic faces and voices with calibrated confidence." },
  { icon: Scan, title: "Frame Analysis", desc: "Every frame is broken down into facial regions, motion vectors, and lighting maps to find inconsistencies." },
  { icon: Activity, title: "Risk Assessment", desc: "Quantified threat scoring combines signals into a single risk number with explainable contributors." },
  { icon: Eye, title: "Artifact Detection", desc: "Surface compression seams, warping, GAN fingerprints, and re-encoding evidence invisible to the human eye." },
  { icon: Brain, title: "Media Intelligence", desc: "Reasoning layer that summarizes findings in plain language analysts can act on." },
  { icon: Radar, title: "Threat Monitoring", desc: "Continuous ingestion from streams and APIs with policy-aware alerting and routing." },
];

const platform = [
  { icon: Network, title: "Integrations", desc: "Webhook, REST, S3, and SIEM exports out of the box." },
  { icon: Workflow, title: "Workflows", desc: "Compose detection pipelines and approval queues per use case." },
  { icon: Zap, title: "Low latency", desc: "Sub-second image scoring, real-time video frame streaming." },
  { icon: Database, title: "Audit trail", desc: "Every decision is logged with model versions and inputs." },
  { icon: Globe, title: "Multilingual", desc: "Reasoning available in 14 languages for global teams." },
];

function FeaturesPage() {
  return (
    <SiteLayout>
      <section className="mx-auto max-w-5xl px-6 pb-16 pt-8 text-center">
        <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-6xl">
          The complete <span className="text-gradient-orange">media verification</span> stack
        </h1>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {main.map((f) => (
            <div key={f.title} className="surface-card p-6">
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/20">
                <f.icon size={18} />
              </div>
              <h3 className="mt-5 text-base font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-border bg-surface/40 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">Enterprise-grade by default</h2>
          </div>
          <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {platform.map((f) => (
              <div key={f.title} className="rounded-xl border border-border bg-card/60 p-5">
                <div className="flex items-center gap-3">
                  <div className="grid h-8 w-8 place-items-center rounded-md bg-primary/10 text-primary"><f.icon size={16} /></div>
                  <h4 className="text-sm font-semibold">{f.title}</h4>
                </div>
                <p className="mt-3 text-sm text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-14 flex justify-center">
            <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-medium text-primary-foreground hover:bg-primary-soft">
              Explore the dashboard <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
