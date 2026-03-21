export type FileKind = "3d" | "2d" | "pdf" | "image" | "office" | "zip" | "unknown";

export type ViewerEngine =
  | "viewer3d"
  | "viewer2d"
  | "pdf"
  | "image"
  | "office"
  | "archive"
  | "unsupported";

export type JobStatus = "CREATED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "NEEDS_APPROVAL";
export type JobStage = "uploaded" | "security" | "preview" | "ready";

export type ProjectRecord = {
  id: string;
  name: string;
  ownerId?: string | null;
  createdAt: string;
};

export type FolderRecord = {
  id: string;
  projectId: string;
  name: string;
  parentId?: string | null;
  isSystem: boolean;
  systemKey?: string | null;
  createdAt: string;
};

export type FileRecord = {
  id: string;
  projectId: string;
  folderId: string;
  name: string;
  ext: string;
  mime: string;
  sizeBytes: number;
  kind: FileKind;
  engine: ViewerEngine;
  storageKey: string;
  createdAt: string;
  previewUrl?: string | null;
  downloadUrl?: string | null;
  archiveEntries?: ArchiveEntry[] | null;
  extractedFolderId?: string | null;
};

export type JobRecord = {
  id: string;
  fileId: string;
  status: JobStatus;
  stage: JobStage;
  progress: number;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
  startedAtMs?: number;
  riskFlags?: string[];
};

export type ShareLinkRecord = {
  id: string;
  fileId: string;
  token: string;
  canView: boolean;
  canDownload: boolean;
  passwordHash?: string | null;
  expiresAt?: string | null;
  createdAt: string;
};

export type ArchiveEntry = {
  path: string;
  sizeBytes: number;
  kind: FileKind;
};

export type ProjectTreeResponse = {
  projectId: string;
  projectName: string;
  folders: FolderRecord[];
  files: FileRecord[];
};

export type FileDetailResponse = {
  file: FileRecord;
  previewUrl: string | null;
  downloadUrl: string;
  inFolder: FolderRecord | null;
  job: JobRecord | null;
};

