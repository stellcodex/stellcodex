import type { ProjectDetail, ProjectSummary } from "@/lib/contracts/projects";
import { mapFileSummary } from "@/lib/mappers/fileMappers";

type RawRecord = Record<string, unknown>;

export function mapProjectSummary(input: unknown): ProjectSummary {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  const files = Array.isArray(row.files) ? row.files : [];
  const mappedFiles = files.map((item) => mapFileSummary(item));
  return {
    projectId: typeof row.id === "string" ? row.id : "default",
    name: typeof row.name === "string" ? row.name : "Untitled project",
    filesCount: typeof row.file_count === "number" ? row.file_count : mappedFiles.length,
    readyCount: mappedFiles.filter((file) => file.status === "ready" || file.status === "succeeded").length,
    processingCount: mappedFiles.filter((file) => !["ready", "succeeded", "failed"].includes(file.status)).length,
    failedCount: mappedFiles.filter((file) => file.status === "failed").length,
    updatedAt: typeof row.updated_at === "string" ? row.updated_at : null,
  };
}

export function mapProjectDetail(input: unknown): ProjectDetail {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  const summary = mapProjectSummary(row);
  return {
    ...summary,
    files: Array.isArray(row.files) ? row.files.map((item) => mapFileSummary(item)) : [],
  };
}
