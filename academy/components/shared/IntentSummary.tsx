"use client";

import type { IntentClassification } from "../../lib/types";
import { INTENT_COLORS, COST_COLORS } from "../../lib/colors";

interface IntentSummaryProps {
  intent: IntentClassification;
}

const INTENT_TOOLTIPS: Record<string, string> = {
  narrative: "Tells a story or shares an experience",
  persuasive: "Argues for a position or action",
  informational: "Shares facts or knowledge",
  technical: "Explains a technical concept",
  conversational: "Casual, social exchange",
  satirical: "Uses irony or humor to make a point",
  humorous: "Aims to entertain or amuse",
  exploratory: "Asks questions, speculates, wonders",
  creative: "Poetry, metaphor, imaginative expression",
  instructional: "Teaches or guides the reader",
  emotional_appeal: "Appeals to feelings and emotions",
};

const COST_TOOLTIPS: Record<string, string> = {
  none: "No cost to comply",
  financial: "Asks for money or financial commitment",
  time: "Requires significant time investment",
  trust: "Asks reader to extend trust",
  autonomy: "Limits reader's choices or freedom",
  privacy: "Requests personal information",
  emotional: "Emotional labor or vulnerability required",
  multiple: "Multiple costs combined",
};

function Pill({
  label,
  colorClass,
  tooltip,
}: {
  label: string;
  colorClass: string;
  tooltip?: string;
}) {
  const display = label.replace(/_/g, " ");
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${colorClass}`}
      title={tooltip}
    >
      {display}
    </span>
  );
}

export default function IntentSummary({ intent }: IntentSummaryProps) {
  const modeColor = INTENT_COLORS[intent.rhetoricalMode] ?? "bg-border/10 text-muted";
  const costColor = COST_COLORS[intent.costToReader] ?? "bg-border/10 text-muted";

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Pill
        label={intent.rhetoricalMode}
        colorClass={modeColor}
        tooltip={INTENT_TOOLTIPS[intent.rhetoricalMode]}
      />
      <Pill
        label={intent.primaryIntent}
        colorClass="bg-border/20 text-foreground/70"
        tooltip={`Primary goal: ${intent.primaryIntent}`}
      />
      {intent.costToReader !== "none" && (
        <Pill
          label={`cost: ${intent.costToReader}`}
          colorClass={costColor}
          tooltip={COST_TOOLTIPS[intent.costToReader]}
        />
      )}
      {intent.proportionality !== "proportional" && (
        <Pill
          label={intent.proportionality}
          colorClass="bg-drifting/10 text-drifting"
          tooltip={
            intent.proportionality === "disproportionate"
              ? "Rhetoric intensity exceeds actual stakes"
              : "Understated relative to actual stakes"
          }
        />
      )}
    </div>
  );
}
