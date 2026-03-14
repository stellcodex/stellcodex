export type AuditEventSummary = {
  id: string;
  timestamp: string;
  actor?: string | null;
  action: string;
  targetType?: string | null;
  targetId?: string | null;
  safeMetaPreview?: string | null;
};

export type QueueSummary = {
  name: string;
  queuedCount: number;
  startedCount: number;
  failedCount: number;
};

export type FailedJobSummary = {
  id: string;
  jobId?: string | null;
  fileId?: string | null;
  stage?: string | null;
  errorClass?: string | null;
  message?: string | null;
  createdAt?: string | null;
};

export type UserSummary = {
  id: string;
  email: string;
  role: string;
  suspended: boolean;
  createdAt?: string | null;
};

export type AdminFileSummary = {
  fileId: string;
  fileName: string;
  status: string;
  visibility?: string | null;
  createdAt?: string | null;
  ownerLabel?: string | null;
};
