import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Technical Architecture",
  description:
    "How the Academy scores character. Evaluation pipeline, model routing, graph schema, and the deterministic scoring behind every report card.",
};

export default function ArchitectureLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
