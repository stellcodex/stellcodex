export type WorkspaceMode = "2d" | "3d";

export type WorkspaceFileRecord = {
  fileId: string;
  originalFilename: string;
  sizeBytes: number;
  mode: WorkspaceMode;
  uploadedAt: string;
  projectId: string;
  projectName: string;
};

export type WorkspaceProjectSummary = {
  projectId: string;
  projectName: string;
  updatedAt: string;
  fileCount: number;
};

const WORKSPACE_CACHE_SLOT = "scx_workspace_files_v1";
export const DEFAULT_PROJECT_ID = "default-project";
export const DEFAULT_PROJECT_NAME = "Default Project";
const WORKSPACE_UPDATED_EVENT = "scx-workspace-updated";

const MODE_2D_EXTENSIONS = new Set([
  "dxf",
  "pdf",
  "png",
  "jpg",
  "jpeg",
  "webp",
  "gif",
  "bmp",
  "svg",
  "tif",
  "tiff",
]);

function canUseStorage() {
  return typeof window !== "undefined" && !!window.localStorage;
}

function safeJsonParse(input: string | null): WorkspaceFileRecord[] {
  if (!input) return [];
  try {
    const parsed = JSON.parse(input) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => typeof item === "object" && item !== null) as WorkspaceFileRecord[];
  } catch {
    return [];
  }
}

function persist(records: WorkspaceFileRecord[]) {
  if (!canUseStorage()) return;
  window.localStorage.setItem(WORKSPACE_CACHE_SLOT, JSON.stringify(records));
  window.dispatchEvent(new CustomEvent(WORKSPACE_UPDATED_EVENT));
}

function normalized(records: WorkspaceFileRecord[]) {
  return records
    .filter((item) => typeof item.fileId === "string" && item.fileId.length > 0)
    .sort((a, b) => (a.uploadedAt < b.uploadedAt ? 1 : -1));
}

export function detectWorkspaceMode(fileName: string, contentType?: string | null): WorkspaceMode {
  const lower = fileName.toLowerCase();
  const ext = lower.includes(".") ? lower.slice(lower.lastIndexOf(".") + 1) : "";

  if (contentType === "application/pdf") return "2d";
  if ((contentType || "").startsWith("image/")) return "2d";
  if (MODE_2D_EXTENSIONS.has(ext)) return "2d";
  return "3d";
}

export function listWorkspaceFiles(): WorkspaceFileRecord[] {
  if (!canUseStorage()) return [];
  const records = safeJsonParse(window.localStorage.getItem(WORKSPACE_CACHE_SLOT));
  return normalized(records);
}

export function getWorkspaceFileById(fileId: string): WorkspaceFileRecord | null {
  return listWorkspaceFiles().find((item) => item.fileId === fileId) || null;
}

export function getLatestWorkspaceFile(mode?: WorkspaceMode): WorkspaceFileRecord | null {
  const records = listWorkspaceFiles();
  if (!mode) return records[0] || null;
  return records.find((item) => item.mode === mode) || null;
}

export function listWorkspaceFilesByProject(projectId: string): WorkspaceFileRecord[] {
  return listWorkspaceFiles().filter((item) => item.projectId === projectId);
}

export function listWorkspaceProjects(): WorkspaceProjectSummary[] {
  const groups = new Map<string, WorkspaceProjectSummary>();

  for (const item of listWorkspaceFiles()) {
    const existing = groups.get(item.projectId);
    if (!existing) {
      groups.set(item.projectId, {
        projectId: item.projectId,
        projectName: item.projectName || DEFAULT_PROJECT_NAME,
        updatedAt: item.uploadedAt,
        fileCount: 1,
      });
      continue;
    }
    existing.fileCount += 1;
    if (existing.updatedAt < item.uploadedAt) {
      existing.updatedAt = item.uploadedAt;
    }
  }

  return Array.from(groups.values()).sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1));
}

export function registerUploadedFile(input: {
  fileId: string;
  originalFilename: string;
  sizeBytes: number;
  contentType?: string | null;
  mode?: WorkspaceMode;
  projectId?: string;
  projectName?: string;
}): WorkspaceFileRecord {
  const projectId = input.projectId || DEFAULT_PROJECT_ID;
  const projectName = input.projectName || DEFAULT_PROJECT_NAME;
  const mode = input.mode || detectWorkspaceMode(input.originalFilename, input.contentType || null);

  const next: WorkspaceFileRecord = {
    fileId: input.fileId,
    originalFilename: input.originalFilename,
    sizeBytes: input.sizeBytes,
    mode,
    uploadedAt: new Date().toISOString(),
    projectId,
    projectName,
  };

  const current = listWorkspaceFiles().filter((item) => item.fileId !== input.fileId);
  persist(normalized([next, ...current]));
  return next;
}

export function formatWorkspaceDate(iso: string): string {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function subscribeWorkspaceUpdates(listener: () => void) {
  if (typeof window === "undefined") return () => undefined;
  const onStorage = (event: StorageEvent) => {
    if (event.key === WORKSPACE_CACHE_SLOT) listener();
  };
  const onCustom = () => listener();

  window.addEventListener("storage", onStorage);
  window.addEventListener(WORKSPACE_UPDATED_EVENT, onCustom);

  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(WORKSPACE_UPDATED_EVENT, onCustom);
  };
}
