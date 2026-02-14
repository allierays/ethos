import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Explore",
  description:
    "Explore the Ethos knowledge graph. Visualize agent character, similarity networks, alumni benchmarks, and dimensional balance.",
};

export default function ExploreLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
