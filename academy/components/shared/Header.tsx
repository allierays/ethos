"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { label: "Explore", href: "/explore" },
  { label: "Curriculum", href: "/curriculum" },
  { label: "Find Your Agent", href: "/find" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border bg-white">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal text-white text-sm font-bold">
            E
          </div>
          <span className="text-lg font-semibold tracking-tight">
            Ethos Academy
          </span>
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  isActive
                    ? "text-foreground font-medium"
                    : "text-muted hover:text-foreground transition-colors"
                }
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
