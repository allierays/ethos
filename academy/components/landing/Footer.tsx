import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background py-12">
      <div className="mx-auto max-w-5xl px-6 text-center">
        <p className="text-sm text-muted">
          Ethos — Better agents. Better data. Better alignment.
        </p>
        <p className="mt-2 text-xs text-muted/60">
          Built for the Claude Code Hackathon 2025
        </p>
        <Link
          href="/styleguide"
          className="mt-3 inline-block text-xs text-muted/40 transition-colors hover:text-muted"
        >
          Styleguide
        </Link>
      </div>
    </footer>
  );
}
