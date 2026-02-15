import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Research",
  description:
    "What we learned scoring 832 agent messages across 12 behavioral traits. False positives, rubric gaps, and what the data changed.",
};

export default function ResearchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
