import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Header from "../components/shared/Header";
import ErrorBoundary from "../components/shared/ErrorBoundary";
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
  title: "Ethos Academy",
  description:
    "Trust visualization for AI agents — honesty, accuracy, and intent across 12 behavioral traits.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <GlossaryProvider>
          <Header />
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
          <GlossarySidebar />
        </GlossaryProvider>
      </body>
    </html>
  );
}
