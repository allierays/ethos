import { getRecords } from "../../lib/api";
import RecordsClient from "./RecordsClient";

interface RecordsPageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function RecordsPage({ searchParams }: RecordsPageProps) {
  const params = await searchParams;
  const agent = typeof params.agent === "string" ? params.agent : undefined;

  let initialData;
  try {
    initialData = await getRecords({
      agent,
      page: 0,
      size: 20,
      sort: "date",
      order: "desc",
    });
  } catch {
    initialData = null;
  }

  return <RecordsClient initialData={initialData} initialAgent={agent} />;
}
