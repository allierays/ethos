"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

/**
 * Reset scroll to top on every client-side route change.
 *
 * Next.js App Router should do this by default, but dynamic pages
 * with Framer Motion animations can interfere with scroll restoration.
 */
export default function ScrollToTop() {
  const pathname = usePathname();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}
