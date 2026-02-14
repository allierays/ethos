"use client";

import { useGlossary } from "../../lib/GlossaryContext";

export default function GraphHelpButton({ slug }: { slug: string }) {
  const { openGlossary } = useGlossary();

  return (
    <button
      onClick={() => openGlossary(slug)}
      aria-label="How to read this chart"
      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-border text-[11px] font-semibold text-muted hover:border-accent/40 hover:bg-accent-light hover:text-accent cursor-pointer transition-colors"
    >
      ?
    </button>
  );
}
