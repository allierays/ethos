import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Insights",
  description:
    "Alumni insights from the Ethos knowledge graph. Agent alignment, honesty scoring, behavioral similarity, and dimensional balance.",
};

export default function ExploreLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
