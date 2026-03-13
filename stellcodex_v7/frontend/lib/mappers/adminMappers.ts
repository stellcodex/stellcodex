import type {
  AdminFileSummary,
  AuditEventSummary,
  FailedJobSummary,
  QueueSummary,
  UserSummary,
} from "@/lib/contracts/admin";
import { safePreview } from "@/lib/utils/noLeak";

type RawRecord = Record<string, unknown>;

export function mapQueues(input: unknown): QueueSummary[] {
  const items = Array.isArray((input as RawRecord | undefined)?.queues)
    ? ((input as RawRecord).queues as unknown[])
    : [];
  return items.map((item) => {
    const row = (item && typeof item === "object" ? item : {}) as RawRecord;
    return {
      name: typeof row.name === "string" ? row.name : "queue",
      queuedCount: typeof row.queued_count === "number" ? row.queued_count : 0,
      startedCount: typeof row.started_count === "number" ? row.started_count : 0,
      failedCount: typeof row.failed_count === "number" ? row.failed_count : 0,
    };
  });
}

export function mapFailedJobs(input: unknown): FailedJobSummary[] {
  const items = Array.isArray((input as RawRecord | undefined)?.items)
    ? ((input as RawRecord).items as unknown[])
    : [];
  return items.map((item) => {
    const row = (item && typeof item === "object" ? item : {}) as RawRecord;
    return {
      id: typeof row.id === "string" ? row.id : "job",
      jobId: typeof row.job_id === "string" ? row.job_id : null,
      fileId: typeof row.file_id === "string" ? row.file_id : null,
      stage: typeof row.stage === "string" ? row.stage : null,
      errorClass: typeof row.error_class === "string" ? row.error_class : null,
      message: typeof row.message === "string" ? row.message : null,
      createdAt: typeof row.created_at === "string" ? row.created_at : null,
    };
  });
}

export function mapAudit(input: unknown): AuditEventSummary[] {
  const items = Array.isArray((input as RawRecord | undefined)?.items)
    ? ((input as RawRecord).items as unknown[])
    : [];
  return items.map((item) => {
    const row = (item && typeof item === "object" ? item : {}) as RawRecord;
    return {
      id: typeof row.id === "string" ? row.id : "audit",
      timestamp: typeof row.created_at === "string" ? row.created_at : new Date().toISOString(),
      actor:
        (typeof row.actor_user_id === "string" && row.actor_user_id) ||
        (typeof row.actor_anon_sub === "string" && row.actor_anon_sub) ||
        null,
      action: typeof row.event_type === "string" ? row.event_type : "event",
      targetType: typeof row.file_id === "string" && row.file_id ? "file" : null,
      targetId: typeof row.file_id === "string" ? row.file_id : null,
      safeMetaPreview: safePreview(row.data),
    };
  });
}

export function mapUsers(input: unknown): UserSummary[] {
  const items = Array.isArray((input as RawRecord | undefined)?.items)
    ? ((input as RawRecord).items as unknown[])
    : [];
  return items.map((item) => {
    const row = (item && typeof item === "object" ? item : {}) as RawRecord;
    return {
      id: typeof row.id === "string" ? row.id : "user",
      email: typeof row.email === "string" ? row.email : "Unknown user",
      role: typeof row.role === "string" ? row.role : "user",
      suspended: Boolean(row.is_suspended),
      createdAt: typeof row.created_at === "string" ? row.created_at : null,
    };
  });
}

export function mapAdminFiles(input: unknown): AdminFileSummary[] {
  const items = Array.isArray((input as RawRecord | undefined)?.items)
    ? ((input as RawRecord).items as unknown[])
    : [];
  return items.map((item) => {
    const row = (item && typeof item === "object" ? item : {}) as RawRecord;
    return {
      fileId: typeof row.file_id === "string" ? row.file_id : "unknown",
      fileName: typeof row.original_filename === "string" ? row.original_filename : "Untitled file",
      status: typeof row.status === "string" ? row.status : "unknown",
      visibility: typeof row.visibility === "string" ? row.visibility : null,
      createdAt: typeof row.created_at === "string" ? row.created_at : null,
      ownerLabel:
        (typeof row.owner_user_id === "string" && row.owner_user_id) ||
        (typeof row.owner_anon_sub === "string" && row.owner_anon_sub) ||
        null,
    };
  });
}
