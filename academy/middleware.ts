import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(_request: NextRequest) {
  const response = NextResponse.next();
  const isDev = process.env.NODE_ENV === "development";

  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=()"
  );

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8917";
  const connectSrc = isDev
    ? "connect-src *"
    : `connect-src 'self' ${apiUrl}`;

  response.headers.set(
    "Content-Security-Policy",
    [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      connectSrc,
      "frame-ancestors 'none'",
    ].join("; ")
  );

  return response;
}

export const config = {
  matcher: [
    // Match all paths except Next.js internals and static files
    "/((?!_next|favicon.ico|.*\\..*).*)",
  ],
};
