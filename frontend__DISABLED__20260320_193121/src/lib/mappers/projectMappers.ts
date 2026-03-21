import type { RawProject } from "@/lib/contracts/projects";
import type { ProjectRecord } from "@/lib/contracts/ui";

export function mapProjectRecord(project: RawProject): ProjectRecord {
  return {
    projectId: project.id,
    name: project.name,
    fileCount: project.file_count,
    updatedAt: project.updated_at ?? null,
    files: (project.files ?? []).map((file) => ({
      fileId: file.file_id,
      originalFilename: file.original_filename,
      status: file.status,
      kind: file.kind ?? null,
      mode: file.mode ?? null,
      createdAt: file.created_at ?? null,
    })),
  };
}
