import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Research",
  description:
    "Lessons from scoring 832 AI agent messages across 12 behavioral traits. What we learned building Ethos Academy.",
};

export default function ResearchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
