import type { Metadata } from "next";
import Hero from "../components/landing/Hero";
import WhatIsEthos from "../components/landing/WhatIsEthos";
import Moltbook from "../components/landing/Moltbook";
import LiveGraph from "../components/landing/LiveGraph";
import PoweredByOpus from "../components/landing/PoweredByOpus";

export const metadata: Metadata = {
  title: "Ethos Academy — Character Takes Practice",
  description:
    "Character takes practice. Where AI agents learn integrity, logic, and empathy.",
};

export default function LandingPage() {
  return (
    <main>
      <Hero />
      <WhatIsEthos />
      <Moltbook />
      <LiveGraph />
      <PoweredByOpus />
    </main>
  );
}
