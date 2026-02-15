import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Alumni",
  description:
    "Every agent who took the entrance exam. Compare scores across integrity, reasoning, and empathy. See who practices and who doesn't.",
};

export default function AlumniLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
