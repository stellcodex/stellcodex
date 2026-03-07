export const EVENT_NAMES = [
  "upload_received",
  "virus_scan_failed",
  "convert_job_queued",
  "convert_job_started",
  "convert_job_failed",
  "convert_job_succeeded",
  "viewer_opened",
  "share_created",
  "permission_denied",
  "rate_limited",
] as const;

export type EventName = typeof EVENT_NAMES[number];
