export type StatusTone = "neutral" | "success" | "warning" | "danger" | "info";

export interface SessionUser {
  label: string;
  role: "guest" | "user" | "admin";
  email?: string;
}

export interface FileRecord {
  fileId: string;
  originalName: string;
  kind: string;
  mode: string | null;
  createdAt: string;
  contentType: string;
  sizeBytes: number;
  status: string;
  statusTone: StatusTone;
  visibility: string;
  thumbnailUrl: string | null;
  previewUrl: string | null;
  previewUrls: string[];
  gltfUrl: string | null;
  originalUrl: string | null;
  partCount: number | null;
  error: string | null;
}

export interface ProjectFileRecord {
  fileId: string;
  originalFilename: string;
  status: string;
  kind: string | null;
  mode: string | null;
  createdAt: string | null;
}

export interface ProjectRecord {
  projectId: string;
  name: string;
  fileCount: number;
  updatedAt: string | null;
  files: ProjectFileRecord[];
}

export interface ViewerNodeRecord {
  id: string;
  occurrenceId: string;
  partId: string;
  label: string;
  kind: string;
  partCount: number;
  gltfNodes: string[];
  children: ViewerNodeRecord[];
}

export interface ViewerModel {
  file: FileRecord;
  state: "loading" | "processing" | "failed" | "metadata_missing" | "ready";
  stateMessage: string;
  modelId: string | null;
  modelUrl: string | null;
  contentUrl: string | null;
  previewUrls: string[];
  nodes: ViewerNodeRecord[];
  occurrenceCount: number;
}

export interface DecisionRecord {
  sessionId: string;
  fileId: string;
  stateCode: string;
  stateLabel: string;
  approvalRequired: boolean;
  riskFlags: string[];
  manufacturingMethod: string;
  mode: string;
  confidence: number;
  ruleVersion: string;
  explanations: Array<{
    ruleId: string;
    triggered: boolean;
    severity: string;
    reference: string;
    reasoning: string;
  }>;
}

export interface RequiredInputRecord {
  key: string;
  label: string;
  inputType: string;
  required: boolean;
}

export interface DfmFindingRecord {
  code: string;
  severity: string;
  message: string;
  recommendation: string | null;
  fields: string[];
}

export interface DfmRecord {
  fileId: string;
  statusGate: string;
  riskFlags: string[];
  findings: DfmFindingRecord[];
  geometryReport: Record<string, unknown>;
}

export interface ShareRecord {
  shareId: string;
  token: string;
  permission: string;
  expiresAt: string;
  publicUrl: string;
  status: "active" | "expired" | "revoked";
  fileId?: string;
}

export interface PublicShareRecord {
  permission: string;
  canView: boolean;
  canDownload: boolean;
  expiresAt: string;
  contentType: string;
  originalFilename: string;
  sizeBytes: number;
  gltfUrl: string | null;
  originalUrl: string | null;
}

export interface AdminHealthRecord {
  component: string;
  status: string;
}

export interface AdminQueueRecord {
  name: string;
  queuedCount: number;
  startedCount: number;
  failedCount: number;
}

export interface AdminFailedJobRecord {
  id: string;
  jobId: string;
  fileId: string | null;
  stage: string;
  errorClass: string;
  message: string;
  createdAt: string;
}

export interface AdminUserRecord {
  id: string;
  email: string;
  role: string;
  suspended: boolean;
  createdAt: string;
}

export interface AdminFileRecord {
  fileId: string;
  originalFilename: string;
  status: string;
  visibility: string;
  privacy: string;
  ownerUserId: string | null;
  ownerAnonSub: string | null;
  createdAt: string;
}

export interface AdminAuditRecord {
  id: string;
  eventType: string;
  actorUserId: string | null;
  actorAnonSub: string | null;
  fileId: string | null;
  data: Record<string, unknown> | null;
  createdAt: string;
}
