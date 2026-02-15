import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Technical Architecture",
  description:
    "Evaluation pipeline, model routing, graph schema, security architecture, and Opus 4.6 integration behind Ethos Academy.",
};

export default function ArchitectureLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
