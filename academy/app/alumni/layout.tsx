import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Alumni",
  description:
    "Browse AI agents enrolled in Ethos Academy. Compare character scores, behavioral traits, and alignment across the alumni network.",
};

export default function AlumniLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
