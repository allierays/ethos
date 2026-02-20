import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Header from "../components/shared/Header";
import Footer from "../components/landing/Footer";

import ErrorBoundary from "../components/shared/ErrorBoundary";
import ScrollToTop from "../components/shared/ScrollToTop";
import { GlossaryProvider } from "../lib/GlossaryContext";
import GlossarySidebar from "../components/shared/GlossarySidebar";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Ethos Academy",
    template: "%s | Ethos Academy",
  },
  description:
    "Enroll your AI agents to learn integrity, logic, and empathy. Character takes practice.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://ethos-academy.com"
  ),
  openGraph: {
    title: "Ethos Academy",
    description:
      "Enroll your AI agents to learn integrity, logic, and empathy. Character takes practice.",
    type: "website",
    images: [
      {
        url: "/og-image-with-text.jpeg",
        width: 1200,
        height: 630,
        alt: "Ethos Academy - Character development for AI agents",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Ethos Academy",
    description:
      "Enroll your AI agents to learn integrity, logic, and empathy. Character takes practice.",
    images: ["/og-image-with-text.jpeg"],
  },
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              name: "Ethos Academy",
              url: process.env.NEXT_PUBLIC_SITE_URL || "https://ethos-academy.com",
              description:
                "Enroll your AI agents to learn integrity, logic, and empathy. Character takes practice.",
            }),
          }}
        />
        {/* Suppress Next.js dev-mode performance.measure('NotFound') bug */}
        {process.env.NODE_ENV === "development" && (
          <script
            dangerouslySetInnerHTML={{
              __html: `(function(){var m=performance.measure.bind(performance);performance.measure=function(n,s,e){try{return m(n,s,e)}catch(e){return null}}})()`,
            }}
          />
        )}
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <GlossaryProvider>
          <ScrollToTop />
          <Header />
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
          <Footer />
          <GlossarySidebar />
        </GlossaryProvider>
      </body>
    </html>
  );
}
