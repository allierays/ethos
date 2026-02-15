import type { Metadata } from "next";
import Hero from "../components/landing/Hero";
import WhatIsPhronesis from "../components/landing/WhatIsPhronesis";
import WhyNow from "../components/landing/WhyNow";
import TheLoop from "../components/landing/TheLoop";
import LiveGraph from "../components/landing/LiveGraph";
import MarketingCTA from "../components/landing/MarketingCTA";

export const metadata: Metadata = {
  title: "Ethos Academy — Trust Visualization for AI Agents",
  description:
    "Score AI agent messages for honesty, accuracy, and intent across 12 behavioral traits. Build phronesis over time.",
};

export default function LandingPage() {
  return (
    <main>
      <Hero />
      <WhatIsPhronesis />
      <WhyNow />
      <TheLoop />
      <LiveGraph />
      <MarketingCTA />
    </main>
  );
}
