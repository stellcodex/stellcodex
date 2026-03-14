import { apiFetchJson } from "@/lib/api/client";

export async function getHealth() {
  return apiFetchJson("/admin/health", undefined, { requireUser: true });
}

export async function getQueues() {
  return apiFetchJson("/admin/queues", undefined, { requireUser: true });
}

export async function getFailedJobs() {
  return apiFetchJson("/admin/queues/failed", undefined, { requireUser: true });
}

export async function getAudit() {
  return apiFetchJson("/admin/audit", undefined, { requireUser: true });
}

export async function getUsers() {
  return apiFetchJson("/admin/users", undefined, { requireUser: true });
}

export async function getFiles() {
  return apiFetchJson("/admin/files", undefined, { requireUser: true });
}
