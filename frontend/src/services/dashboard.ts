import { FileItem, listFiles } from "@/services/api";

const DASHBOARD_STUBS_ENABLED = true;

export async function fetchRecentFiles(limit = 5): Promise<FileItem[]> {
  const items = await listFiles();
  return items.slice(0, limit);
}

export type ActivityItem = {
  id: string;
  label: string;
  timestamp: string;
};

export async function fetchActivity(): Promise<ActivityItem[]> {
  if (DASHBOARD_STUBS_ENABLED) {
    return [];
  }
  throw new Error("Backend uç noktası tanımlı değil.");
}
