import type { FileSummary } from "@/lib/contracts/files";

export type ProjectSummary = {
  projectId: string;
  name: string;
  description?: string | null;
  filesCount?: number;
  readyCount?: number;
  processingCount?: number;
  failedCount?: number;
  updatedAt?: string | null;
};

export type ProjectDetail = ProjectSummary & {
  files: FileSummary[];
};
