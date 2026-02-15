import Link from "next/link";
import ColumnIcon from "../shared/ColumnIcon";

export default function Footer() {
  return (
    <footer className="relative overflow-hidden">
      {/* Pantheon background — center on the columns */}
      <img
        src="/ethos-academy.jpeg"
        alt=""
        className="absolute inset-0 h-full w-full object-cover"
        style={{ objectPosition: "center 30%" }}
      />
      <div className="absolute inset-0 bg-[#0a1628]/80" />

      <div className="relative mx-auto max-w-5xl px-6 py-16">
        <div className="flex flex-col gap-10 sm:flex-row sm:justify-between">
          {/* Left: branding */}
          <div className="text-center sm:text-left">
            <div className="flex items-center gap-2">
              <ColumnIcon className="h-5 w-5 text-white/70" />
              <p className="text-lg font-semibold text-white">Ethos Academy</p>
            </div>
            <p className="mt-1 max-w-xs text-sm text-white/80">
              Better data. Better alignment. Better agents.
            </p>
            <div className="mt-4 flex items-center justify-center gap-4 sm:justify-start">
              <a
                href="https://github.com/allierays/ethos-academy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/70 transition-colors hover:text-white"
                aria-label="GitHub"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
                </svg>
              </a>
              <a
                href="https://www.linkedin.com/in/allierays/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/70 transition-colors hover:text-white"
                aria-label="LinkedIn"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </a>
              <a
                href="https://x.com/allierays"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/70 transition-colors hover:text-white"
                aria-label="X (Twitter)"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
            </div>
          </div>

          {/* Center: Academy links */}
          <div className="text-center sm:text-left">
            <p className="text-xs font-semibold uppercase tracking-wider text-white/90">
              Academy
            </p>
            <nav className="mt-3 flex flex-col gap-2">
              <Link href="/how-it-works" className="text-sm text-white/70 transition-colors hover:text-white">
                How It Works
              </Link>
              <Link href="/rubric" className="text-sm text-white/70 transition-colors hover:text-white">
                Rubric
              </Link>
              <Link href="/insights" className="text-sm text-white/70 transition-colors hover:text-white">
                Insights
              </Link>
              <Link href="/alumni" className="text-sm text-white/70 transition-colors hover:text-white">
                Alumni
              </Link>
              <Link href="/research" className="text-sm text-white/70 transition-colors hover:text-white">
                Research
              </Link>
              <Link href="/architecture" className="text-sm text-white/70 transition-colors hover:text-white">
                Architecture
              </Link>
            </nav>
          </div>

          {/* Right: Project links */}
          <div className="text-center sm:text-left">
            <p className="text-xs font-semibold uppercase tracking-wider text-white/90">
              Project
            </p>
            <nav className="mt-3 flex flex-col gap-2">
              <a
                href="https://github.com/allierays/ethos-academy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-white/70 transition-colors hover:text-white"
              >
                Source Code
              </a>
              <a
                href="https://github.com/allierays/ethos-academy#readme"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-white/70 transition-colors hover:text-white"
              >
                Documentation
              </a>
              <a
                href="https://github.com/allierays/ethos-academy/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-white/70 transition-colors hover:text-white"
              >
                Issues
              </a>
              <a
                href="https://github.com/allierays/ethos-academy/blob/main/CONTRIBUTING.md"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-white/70 transition-colors hover:text-white"
              >
                Contributing
              </a>
            </nav>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-10 flex flex-col items-center gap-2 border-t border-white/10 pt-6 sm:flex-row sm:justify-between">
          <p className="text-xs text-white/50">
            Built for the{" "}
            <a
              href="https://cerebralvalley.ai/e/claude-code-hackathon"
              target="_blank"
              rel="noopener noreferrer"
              className="underline transition-colors hover:text-white/80"
            >
              Claude Code Hackathon 2026
            </a>
          </p>
          <p className="text-xs text-white/50">
            <Link href="/privacy" className="underline transition-colors hover:text-white/80">
              Privacy
            </Link>
            {" "}&middot;{" "}
            <Link href="/terms" className="underline transition-colors hover:text-white/80">
              Terms
            </Link>
            {" "}&middot;{" "}
            <a
              href="https://github.com/allierays/ethos-academy/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="underline transition-colors hover:text-white/80"
            >
              MIT License
            </a>
            {" "}&middot;{" "}
            made with love by{" "}
            <a
              href="https://www.linkedin.com/in/allierays/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline transition-colors hover:text-white/80"
            >
              allierays
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
