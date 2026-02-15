import type { Metadata } from "next";
import Hero from "../components/landing/Hero";
import WhatIsEthos from "../components/landing/WhatIsEthos";
import WhatIsPhronesis from "../components/landing/WhatIsPhronesis";
import WhyNow from "../components/landing/WhyNow";
import TheLoop from "../components/landing/TheLoop";
import LiveGraph from "../components/landing/LiveGraph";
import MarketingCTA from "../components/landing/MarketingCTA";

export const metadata: Metadata = {
  title: "Ethos Academy — Character Takes Practice",
  description:
    "Your agents are what they repeatedly do. Benchmarks are snapshots. Character takes practice. Welcome to the Academy.",
};

export default function LandingPage() {
  return (
    <main>
      <Hero />
      <WhatIsEthos />
      <WhatIsPhronesis />
      <WhyNow />
      <TheLoop />
      <LiveGraph />
      <MarketingCTA />
    </main>
  );
}
