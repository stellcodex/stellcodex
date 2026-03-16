export interface RawAdminHealth {
  api: string;
  db: string;
  redis: string;
  rq: string;
  storage?: string;
}

export interface RawAdminQueueEntry {
  name: string;
  queued_count: number;
  started_count: number;
  failed_count: number;
}

export interface RawAdminQueues {
  queues: RawAdminQueueEntry[];
}

export interface RawAdminFailedJob {
  id: string;
  job_id: string;
  file_id: string | null;
  stage: string;
  error_class: string;
  message: string;
  created_at: string;
}

export interface RawAdminUsersEntry {
  id: string;
  email: string;
  role: string;
  is_suspended: boolean;
  created_at: string;
}

export interface RawAdminFilesEntry {
  file_id: string;
  original_filename: string;
  status: string;
  visibility: string;
  privacy: string;
  owner_user_id: string | null;
  owner_anon_sub: string | null;
  created_at: string;
}

export interface RawAdminAuditEntry {
  id: string;
  event_type: string;
  actor_user_id: string | null;
  actor_anon_sub: string | null;
  file_id: string | null;
  data: Record<string, unknown> | null;
  created_at: string;
}
