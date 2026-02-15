"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useGlossary } from "../../lib/GlossaryContext";

const NAV_ITEMS = [
  { label: "Insights", href: "/insights" },
  { label: "How It Works", href: "/how-it-works" },
  { label: "Rubric", href: "/rubric" },
  { label: "Records", href: "/records" },
  { label: "Alumni", href: "/alumni" },
];

export default function Header() {
  const pathname = usePathname();
  const { openGlossary } = useGlossary();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="relative z-10 border-b border-white/20 bg-white/60 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-action text-white text-sm font-bold">
            E
          </div>
          <span className="text-lg font-semibold tracking-tight text-foreground">
            Ethos Academy
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  isActive
                    ? "text-foreground font-bold"
                    : "text-foreground font-semibold hover:text-foreground/80 transition-colors"
                }
              >
                {item.label}
              </Link>
            );
          })}
          <button
            onClick={() => openGlossary()}
            aria-label="Open glossary"
            className="flex h-8 w-8 items-center justify-center rounded-md text-foreground/80 hover:bg-black/5 hover:text-foreground transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 2h4.5c.8 0 1.5.7 1.5 1.5V14l-1-1H2V2z" />
              <path d="M14 2H9.5C8.7 2 8 2.7 8 3.5V14l1-1H14V2z" />
            </svg>
          </button>
        </nav>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          className="md:hidden flex h-8 w-8 items-center justify-center rounded-md text-foreground/80 hover:bg-black/5 hover:text-foreground transition-colors"
        >
          {mobileOpen ? (
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M4 4l10 10M14 4L4 14" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M3 5h12M3 9h12M3 13h12" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <nav className="md:hidden border-t border-white/20 bg-white/80 backdrop-blur-xl px-6 py-3 flex flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`py-2 px-3 rounded-md text-sm transition-colors ${
                  isActive
                    ? "text-foreground font-bold bg-black/5"
                    : "text-foreground font-semibold hover:bg-black/5"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
          <button
            onClick={() => {
              setMobileOpen(false);
              openGlossary();
            }}
            className="py-2 px-3 rounded-md text-sm text-foreground font-semibold hover:bg-black/5 transition-colors text-left flex items-center gap-2"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 2h4.5c.8 0 1.5.7 1.5 1.5V14l-1-1H2V2z" />
              <path d="M14 2H9.5C8.7 2 8 2.7 8 3.5V14l1-1H14V2z" />
            </svg>
            Glossary
          </button>
        </nav>
      )}
    </header>
  );
}
