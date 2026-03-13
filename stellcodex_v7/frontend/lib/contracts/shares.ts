export type ShareSummary = {
  shareId: string;
  targetType: "file" | "project";
  targetName: string;
  permission: string;
  watermark?: boolean;
  createdAt?: string | null;
  expiresAt?: string | null;
  status: "active" | "expired" | "revoked" | "unknown";
  publicUrl?: string | null;
  token?: string | null;
};

export type PublicShareSummary = {
  token: string;
  fileId?: string | null;
  fileName: string;
  status: "valid" | "expired" | "revoked" | "forbidden" | "invalid";
  permission?: string | null;
  canDownload?: boolean;
  expiresAt?: string | null;
  contentType?: string | null;
  viewerUrl?: string | null;
  downloadUrl?: string | null;
};
