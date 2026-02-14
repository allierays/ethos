import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Framework",
  description:
    "The Ethos behavioral framework: 3 dimensions, 12 traits, and 153 indicators for measuring AI agent honesty, reasoning, and emotional intelligence.",
};

export default function FrameworkLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
