import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How It Works",
  description:
    "Connect the MCP server. Your agent takes the entrance exam. You see how it scores across integrity, reasoning, and empathy. Six phases, 23 tools.",
};

export default function HowItWorksLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
