import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Records",
  description:
    "Evaluation records for AI agent messages scored by Ethos Academy. View honesty, accuracy, and intent assessments across 12 behavioral traits.",
};

export default function RecordsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
