"use client";

import QRCode from "react-qr-code";

const LINKS = [
  {
    label: "Connect on LinkedIn",
    url: "https://www.linkedin.com/in/allierays/",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
  },
  {
    label: "Book a Meeting",
    url: "https://calendly.com/allie-allthrive/30min",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    ),
  },
];

export default function ConnectPrint() {
  return (
    <div className="connect-print mx-auto max-w-[8in] bg-white px-8 py-6 text-[#1a2538]">
      <style>{`
        @media print {
          body { margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
          header, footer, section { display: none !important; }
          .connect-print { padding: 0 !important; }
          @page { margin: 0.6in 0.75in; size: letter; }
        }
      `}</style>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1a2538]">
            <span className="text-xs font-bold text-white tracking-tight">EA</span>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight leading-tight">Ethos Academy</h1>
            <p className="text-[10px] text-gray-400 leading-tight">Character development for AI agents</p>
          </div>
        </div>
      </div>

      {/* Profile section */}
      <div className="flex items-center gap-5 mb-10">
        <img
          src="/allie-headshot-2026.png"
          alt="Allie Rays"
          className="h-24 w-24 rounded-full object-cover border-2 border-gray-100"
        />
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Allie Rays</h2>
          <p className="text-sm font-bold text-[#1a2538] mt-1.5">Does your AI agent have wisdom?</p>
          <p className="text-xs text-gray-500 mt-0.5 leading-relaxed max-w-[20rem]">
            Enroll your agent in Ethos Academy to measure integrity, logic, and empathy growth over time.
          </p>
        </div>
      </div>

      {/* QR code cards */}
      <div className="grid grid-cols-2 gap-8">
        {LINKS.map((link) => (
          <div
            key={link.url}
            className="flex flex-col items-center rounded-2xl border border-gray-200 bg-gray-50 px-6 py-8"
          >
            <div className="mb-4 text-[#1a2538]">{link.icon}</div>
            <h3 className="text-sm font-bold mb-5">{link.label}</h3>
            <div className="rounded-xl bg-white p-4 shadow-sm">
              <QRCode value={link.url} size={160} level="M" />
            </div>
            <p className="mt-4 font-mono text-[10px] text-gray-400 text-center break-all">
              {link.url}
            </p>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-10 border-t border-gray-200 pt-3 flex items-center justify-between text-[9px] text-gray-400">
        <p>Does your AI agent have wisdom?</p>
        <p>ethos-academy.com</p>
      </div>

      {/* Print button */}
      <div className="no-print fixed bottom-6 right-6 z-50">
        <button
          type="button"
          onClick={() => window.print()}
          className="flex items-center gap-2 rounded-xl bg-[#1a2538] px-5 py-3 text-sm font-semibold text-white shadow-lg transition-all hover:bg-[#243347] active:scale-[0.98]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 6 2 18 2 18 9" />
            <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
            <rect x="6" y="14" width="12" height="8" />
          </svg>
          Print / Save PDF
        </button>
      </div>
    </div>
  );
}
