import { Link } from "@tanstack/react-router";
import { Menu, X } from "lucide-react";
import { useState } from "react";

const links = [
  { to: "/", label: "Home" },
  { to: "/features", label: "Features" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/text-analysis", label: "Text Analysis" },
] as const;

export function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <ul className="hidden items-center gap-6 md:flex">
          {links.map((l) => (
            <li key={l.to}>
              <Link
                to={l.to}
                activeOptions={{ exact: l.to === "/" }}
                activeProps={{ className: "text-foreground" }}
                inactiveProps={{ className: "text-muted-foreground hover:text-foreground" }}
                className="text-sm transition"
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="hidden md:block">
          <Link
            to="/dashboard"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-soft"
          >
            Get started
          </Link>
        </div>

        <button
          className="rounded-md p-2 md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </nav>

      {open && (
        <div className="border-t border-border md:hidden">
          <ul className="mx-auto flex max-w-6xl flex-col px-6 py-2">
            {links.map((l) => (
              <li key={l.to}>
                <Link
                  to={l.to}
                  onClick={() => setOpen(false)}
                  className="block py-2 text-sm text-muted-foreground hover:text-foreground"
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </header>
  );
}
