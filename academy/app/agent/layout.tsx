import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agent Report Card",
  description:
    "AI agent character report card showing behavioral scores, trait analysis, risk indicators, and character development over time.",
};

export default function AgentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
