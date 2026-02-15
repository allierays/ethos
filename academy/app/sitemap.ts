import type { MetadataRoute } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://ethos.academy";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8917";

async function getAgentIds(): Promise<string[]> {
  try {
    const res = await fetch(`${API_URL}/alumni`, { next: { revalidate: 3600 } });
    if (!res.ok) return [];
    const data = await res.json();
    const agents = (data.agents ?? data ?? []) as Record<string, unknown>[];
    return agents
      .map((a) => String(a.agentId ?? a.agent_id ?? ""))
      .filter(Boolean);
  } catch (err) {
    console.error("sitemap: failed to fetch agent IDs", err);
    return [];
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const agentIds = await getAgentIds();

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: BASE_URL, changeFrequency: "daily", priority: 1.0 },
    { url: `${BASE_URL}/alumni`, changeFrequency: "daily", priority: 0.9 },
    { url: `${BASE_URL}/explore`, changeFrequency: "daily", priority: 0.8 },
    { url: `${BASE_URL}/records`, changeFrequency: "daily", priority: 0.7 },
    { url: `${BASE_URL}/how-it-works`, changeFrequency: "monthly", priority: 0.6 },
    { url: `${BASE_URL}/rubric`, changeFrequency: "monthly", priority: 0.5 },
    { url: `${BASE_URL}/research`, changeFrequency: "monthly", priority: 0.7 },
    { url: `${BASE_URL}/privacy`, changeFrequency: "yearly", priority: 0.3 },
    { url: `${BASE_URL}/terms`, changeFrequency: "yearly", priority: 0.3 },
  ];

  const agentRoutes: MetadataRoute.Sitemap = agentIds.map((id) => ({
    url: `${BASE_URL}/agent/${id}`,
    changeFrequency: "daily" as const,
    priority: 0.8,
  }));

  return [...staticRoutes, ...agentRoutes];
}
