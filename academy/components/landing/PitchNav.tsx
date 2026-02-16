"use client";

import { useCallback, useEffect, useState } from "react";

const SECTION_IDS = [
  "pitch-hero",
  "pitch-problem",
  "pitch-report",
  "pitch-rubric",
  "pitch-pipeline",
  "pitch-moltbook",
  "pitch-alumni",
  "pitch-demo",
  "pitch-graph",
  "pitch-opus",
  "pitch-enroll",
];

export default function PitchNav() {
  const [current, setCurrent] = useState(0);
  const [visible, setVisible] = useState(true);

  // Track which section is in view
  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    SECTION_IDS.forEach((id, i) => {
      const el = document.getElementById(id);
      if (!el) return;
      const obs = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) setCurrent(i);
        },
        { threshold: 0.4 }
      );
      obs.observe(el);
      observers.push(obs);
    });
    return () => observers.forEach((o) => o.disconnect());
  }, []);

  // Hide during scroll, show after idle
  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    function onScroll() {
      setVisible(false);
      clearTimeout(timeout);
      timeout = setTimeout(() => setVisible(true), 800);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      clearTimeout(timeout);
    };
  }, []);

  const scrollTo = useCallback((index: number) => {
    const clamped = Math.max(0, Math.min(index, SECTION_IDS.length - 1));
    const el = document.getElementById(SECTION_IDS[clamped]);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
      setCurrent(clamped);
    }
  }, []);

  // Keyboard navigation
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowDown" || e.key === "PageDown") {
        e.preventDefault();
        scrollTo(current + 1);
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        scrollTo(current - 1);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [current, scrollTo]);

  const isFirst = current === 0;
  const isLast = current === SECTION_IDS.length - 1;

  return (
    <div
      className={`fixed right-6 bottom-8 z-50 flex flex-col items-center gap-2 transition-opacity duration-300 ${visible ? "opacity-100" : "opacity-0 pointer-events-none"}`}
    >
      <button
        onClick={() => scrollTo(current - 1)}
        disabled={isFirst}
        aria-label="Previous section"
        className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-md border border-white/20 transition-all hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 15l-6-6-6 6" />
        </svg>
      </button>

      <button
        onClick={() => scrollTo(current + 1)}
        disabled={isLast}
        aria-label="Next section"
        className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-md border border-white/20 transition-all hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
    </div>
  );
}
