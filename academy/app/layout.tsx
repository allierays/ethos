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
    "Your agents are what they repeatedly do. Benchmarks are snapshots. Character takes practice. Welcome to the Academy.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://ethos.academy"
  ),
  openGraph: {
    title: "Ethos Academy",
    description:
      "Your agents are what they repeatedly do. Benchmarks are snapshots. Character takes practice.",
    type: "website",
    images: ["/academy-people-banner.jpeg"],
  },
  twitter: {
    card: "summary_large_image",
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
              url: process.env.NEXT_PUBLIC_SITE_URL || "https://ethos.academy",
              description:
                "Your agents are what they repeatedly do. Benchmarks are snapshots. Character takes practice.",
            }),
          }}
        />
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
