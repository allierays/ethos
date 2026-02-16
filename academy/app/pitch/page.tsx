import PitchHero from "../../components/landing/PitchHero";
import WhatIsEthos from "../../components/landing/WhatIsEthos";
import SampleReportCard from "../../components/landing/SampleReportCard";
import RubricFoundations from "../../components/landing/RubricFoundations";
import EvaluationPipeline from "../../components/landing/EvaluationPipeline";
import Moltbook from "../../components/landing/Moltbook";
import LiveGraph from "../../components/landing/LiveGraph";
import PoweredByOpus from "../../components/landing/PoweredByOpus";
import Hero from "../../components/landing/Hero";
import PitchNav from "../../components/landing/PitchNav";
import AlumniShowcase from "../../components/landing/AlumniShowcase";
import { getAgents } from "../../lib/api";
import type { AgentSummary } from "../../lib/types";

const s = "min-h-screen flex flex-col justify-center";

export default async function PitchPage() {
  let agents: AgentSummary[] = [];
  try {
    agents = await getAgents();
  } catch {
    agents = [];
  }

  return (
    <main>
      <div id="pitch-hero" className={s}><PitchHero /></div>
      <div id="pitch-problem"><WhatIsEthos pitchMode pitchGroup="problem" /></div>
      <div id="pitch-report" className={s}><SampleReportCard /></div>
      <div id="pitch-rubric" className={s}><RubricFoundations /></div>
      <div id="pitch-pipeline" className={s}><EvaluationPipeline /></div>
      <div id="pitch-moltbook" className={s}><Moltbook /></div>
      <div id="pitch-alumni"><AlumniShowcase agents={agents} /></div>
      <div id="pitch-demo" className={s}><WhatIsEthos pitchMode pitchGroup="demo" /></div>
      <div id="pitch-graph" className={s}><LiveGraph /></div>
      <div id="pitch-opus" className={s}><PoweredByOpus /></div>
      <div id="pitch-enroll" className={s}><Hero /></div>
      <PitchNav />
    </main>
  );
}
