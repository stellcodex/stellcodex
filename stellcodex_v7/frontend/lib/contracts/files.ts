export type FileSummary = {
  fileId: string;
  fileName: string;
  mimeType?: string | null;
  sizeBytes?: number | null;
  status: string;
  kind?: string | null;
  mode?: string | null;
  viewerReady?: boolean;
  gltfUrl?: string | null;
  originalUrl?: string | null;
  thumbnailUrl?: string | null;
  previewUrls?: string[];
  projectId?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  partCount?: number | null;
  extractionStatus?: string | null;
  error?: string | null;
};

export type FileVersionSummary = {
  versionId: string;
  label: string;
  createdAt?: string | null;
  status?: string | null;
  isCurrent?: boolean;
};

export type FileTimelineEvent = {
  id: string;
  label: string;
  timestamp?: string | null;
  status: string;
};
