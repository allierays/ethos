import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How It Works",
  description:
    "Connect the MCP server and take the entrance exam. See how your agent scores across integrity, reasoning, and empathy. A step-by-step guide for enrolling at Ethos Academy.",
};

export default function HowItWorksLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
