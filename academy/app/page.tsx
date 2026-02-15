import type { Metadata } from "next";
import Hero from "../components/landing/Hero";
import WhatIsEthos from "../components/landing/WhatIsEthos";
import WhatIsPhronesis from "../components/landing/WhatIsPhronesis";
import WhyNow from "../components/landing/WhyNow";
import TheLoop from "../components/landing/TheLoop";
import LiveGraph from "../components/landing/LiveGraph";


export const metadata: Metadata = {
  title: "Ethos Academy — Character Takes Practice",
  description:
    "Character takes practice. Teach your AI agents integrity, logic, and empathy.",
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
    </main>
  );
}
