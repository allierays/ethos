import { getRecords } from "../../lib/api";
import RecordsClient from "./RecordsClient";

export default async function RecordsPage() {
  let initialData;
  try {
    initialData = await getRecords({ page: 0, size: 20, sort: "date", order: "desc" });
  } catch {
    initialData = null;
  }

  return <RecordsClient initialData={initialData} />;
}
