import { getAlumni } from "../../lib/api";
import ExploreClient from "./ExploreClient";

export const dynamic = "force-dynamic";

function avg(values: (number | undefined)[]): number {
  const defined = values.filter((v): v is number => v !== undefined);
  if (defined.length === 0) return 0;
  return defined.reduce((a, b) => a + b, 0) / defined.length;
}

export default async function ExplorePage() {
  let alumniDimensions: Record<string, number> = {};

  try {
    const data = await getAlumni();
    const traits = data.traitAverages;
    const ethos = avg([traits.virtue, traits.goodwill, traits.manipulation, traits.deception]);
    const logos = avg([traits.accuracy, traits.reasoning, traits.fabrication, traits.brokenLogic]);
    const pathos = avg([traits.recognition, traits.compassion, traits.dismissal, traits.exploitation]);
    alumniDimensions = { ethos, logos, pathos };
  } catch {
    // Silently fail — balance will show zeros
  }

  return <ExploreClient initialAlumniDimensions={alumniDimensions} />;
}
