import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How It Works",
  description:
    "Learn how Ethos Academy scores AI agent messages for honesty, accuracy, and intent. Understand the 12-trait evaluation framework and character development process.",
};

export default function HowItWorksLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
