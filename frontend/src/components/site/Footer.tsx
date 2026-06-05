import { Shield, Github } from "lucide-react";
import { Link } from "@tanstack/react-router";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="grid h-7 w-7 place-items-center rounded-md bg-primary text-primary-foreground">
                <Shield size={15} />
              </span>
              <span className="text-base font-semibold">Technoax</span>
            </div>
            <p className="mt-3 max-w-xs text-sm text-muted-foreground">
              Detect deepfakes and manipulated media with AI.
            </p>
          </div>

          <div>
            <h4 className="text-sm font-semibold">Product</h4>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li><Link to="/features" className="hover:text-foreground">Features</Link></li>
              <li><Link to="/dashboard" className="hover:text-foreground">Dashboard</Link></li>
              <li><a href="#" className="hover:text-foreground">Documentation</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold">Company</h4>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li><Link to="/about" className="hover:text-foreground">About</Link></li>
              <li><Link to="/about" className="hover:text-foreground">Team members</Link></li>
              <li><Link to="/contact" className="hover:text-foreground">Contact</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold">Resources</h4>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li><a href="https://github.com" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 hover:text-foreground"><Github size={14} /> GitHub</a></li>
              <li><a href="#" className="hover:text-foreground">Privacy</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-border pt-6 text-xs text-muted-foreground">
          © {new Date().getFullYear()} Technoax. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
