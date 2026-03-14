import { RecentFileItem, listRecentFiles } from "@/services/api";

const DASHBOARD_STUBS_ENABLED = true;

export async function fetchRecentFiles(limit = 5): Promise<RecentFileItem[]> {
  return listRecentFiles(limit);
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
  throw new Error("The backend endpoint is not configured.");
}
