"use client";

import { createContext, useContext, useState, useCallback } from "react";
import type { ReactNode } from "react";
import { getGlossaryEntry, type GlossaryEntry } from "./glossary";

interface GlossaryState {
  isOpen: boolean;
  selectedTerm: GlossaryEntry | null;
  openGlossary: (slug?: string) => void;
  closeGlossary: () => void;
  selectTerm: (slug: string) => void;
}

const GlossaryContext = createContext<GlossaryState | null>(null);

export function GlossaryProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedTerm, setSelectedTerm] = useState<GlossaryEntry | null>(null);

  const openGlossary = useCallback((slug?: string) => {
    if (slug) {
      const entry = getGlossaryEntry(slug);
      if (entry) setSelectedTerm(entry);
    }
    setIsOpen(true);
  }, []);

  const closeGlossary = useCallback(() => {
    setIsOpen(false);
    setSelectedTerm(null);
  }, []);

  const selectTerm = useCallback((slug: string) => {
    const entry = getGlossaryEntry(slug);
    if (entry) {
      setSelectedTerm(entry);
      setIsOpen(true);
    }
  }, []);

  return (
    <GlossaryContext.Provider
      value={{ isOpen, selectedTerm, openGlossary, closeGlossary, selectTerm }}
    >
      {children}
    </GlossaryContext.Provider>
  );
}

export function useGlossary(): GlossaryState {
  const ctx = useContext(GlossaryContext);
  if (!ctx) throw new Error("useGlossary must be used within GlossaryProvider");
  return ctx;
}
