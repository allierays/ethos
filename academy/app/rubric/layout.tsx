import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Rubric",
  description:
    "3 dimensions, 12 traits, 214 indicators. The rubric the Academy uses to score every message for honesty, reasoning, and empathy.",
};

export default function RubricLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
