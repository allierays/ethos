import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getAgent, getHistory, getCharacterReport, getDrift } from "../../../lib/api";
import AgentReportClient from "./AgentReportClient";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  try {
    const profile = await getAgent(id);
    const name = profile.agentName || profile.agentId;
    return {
      title: `${name} Report Card`,
      description: `Behavioral evaluation for ${name} across 12 traits in honesty, accuracy, and intent.`,
      openGraph: {
        title: `${name} Report Card | Ethos Academy`,
        description: `Behavioral evaluation for ${name} across 12 traits in honesty, accuracy, and intent.`,
      },
    };
  } catch {
    return { title: "Agent Report Card" };
  }
}

export default async function AgentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: agentId } = await params;

  const [profileResult, historyResult, reportResult, driftResult] =
    await Promise.allSettled([
      getAgent(agentId),
      getHistory(agentId),
      getCharacterReport(agentId),
      getDrift(agentId),
    ]);

  if (profileResult.status === "rejected") {
    notFound();
  }

  const profile = profileResult.value;
  const history =
    historyResult.status === "fulfilled" ? historyResult.value : [];
  const rawReport =
    reportResult.status === "fulfilled" ? reportResult.value : null;
  const report =
    rawReport && rawReport.grade && rawReport.totalEvaluationCount > 0
      ? rawReport
      : null;
  const breakpoints =
    driftResult.status === "fulfilled" && driftResult.value.breakpoints.length > 0
      ? driftResult.value.breakpoints
      : [];

  return (
    <AgentReportClient
      agentId={agentId}
      profile={profile}
      history={history}
      report={report}
      breakpoints={breakpoints}
    />
  );
}
