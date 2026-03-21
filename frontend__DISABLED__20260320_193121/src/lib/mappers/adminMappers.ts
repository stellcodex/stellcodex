import type {
  RawAdminAuditEntry,
  RawAdminFailedJob,
  RawAdminFilesEntry,
  RawAdminHealth,
  RawAdminQueueEntry,
  RawAdminUsersEntry,
} from "@/lib/contracts/admin";
import type {
  AdminAuditRecord,
  AdminFailedJobRecord,
  AdminFileRecord,
  AdminHealthRecord,
  AdminQueueRecord,
  AdminUserRecord,
} from "@/lib/contracts/ui";

const SENSITIVE_KEYS = new Set([
  "bucket",
  "object_key",
  "storage_key",
  "objectKey",
  "storageKey",
  "provider_url",
  "providerUrl",
  "filesystem_path",
  "filesystemPath",
  "local_path",
  "trace_path",
  "access_token",
  "upload_url",
]);

function sanitizeValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sanitizeValue);
  if (!value || typeof value !== "object") return value;
  const sanitized: Record<string, unknown> = {};
  for (const [key, entry] of Object.entries(value)) {
    if (SENSITIVE_KEYS.has(key)) continue;
    sanitized[key] = sanitizeValue(entry);
  }
  return sanitized;
}

export function mapAdminHealth(input: RawAdminHealth): AdminHealthRecord[] {
  return Object.entries(input).map(([component, status]) => ({
    component,
    status,
  }));
}

export function mapAdminQueue(input: RawAdminQueueEntry): AdminQueueRecord {
  return {
    name: input.name,
    queuedCount: input.queued_count,
    startedCount: input.started_count,
    failedCount: input.failed_count,
  };
}

export function mapAdminFailedJob(input: RawAdminFailedJob): AdminFailedJobRecord {
  return {
    id: input.id,
    jobId: input.job_id,
    fileId: input.file_id,
    stage: input.stage,
    errorClass: input.error_class,
    message: input.message,
    createdAt: input.created_at,
  };
}

export function mapAdminUser(input: RawAdminUsersEntry): AdminUserRecord {
  return {
    id: input.id,
    email: input.email,
    role: input.role,
    suspended: input.is_suspended,
    createdAt: input.created_at,
  };
}

export function mapAdminFile(input: RawAdminFilesEntry): AdminFileRecord {
  return {
    fileId: input.file_id,
    originalFilename: input.original_filename,
    status: input.status,
    visibility: input.visibility,
    privacy: input.privacy,
    ownerUserId: input.owner_user_id,
    ownerAnonSub: input.owner_anon_sub,
    createdAt: input.created_at,
  };
}

export function mapAdminAudit(input: RawAdminAuditEntry): AdminAuditRecord {
  return {
    id: input.id,
    eventType: input.event_type,
    actorUserId: input.actor_user_id,
    actorAnonSub: input.actor_anon_sub,
    fileId: input.file_id,
    data: (sanitizeValue(input.data) as Record<string, unknown> | null) ?? null,
    createdAt: input.created_at,
  };
}
