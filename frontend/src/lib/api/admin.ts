import type {
  RawAdminAuditEntry,
  RawAdminFailedJob,
  RawAdminFilesEntry,
  RawAdminHealth,
  RawAdminQueueEntry,
  RawAdminUsersEntry,
} from "@/lib/contracts/admin";

import { apiJson } from "./fetch";
import { getAuthHeaders } from "./session";

export async function getAdminHealth() {
  return apiJson<RawAdminHealth>("/admin/health", {
    headers: await getAuthHeaders({ requireUser: true }),
  });
}

export async function getAdminQueues() {
  const payload = await apiJson<{ queues: RawAdminQueueEntry[] }>("/admin/queues", {
    headers: await getAuthHeaders({ requireUser: true }),
  });
  return payload.queues;
}

export async function getAdminFailedJobs() {
  const payload = await apiJson<{ items: RawAdminFailedJob[] }>("/admin/queues/failed", {
    headers: await getAuthHeaders({ requireUser: true }),
  });
  return payload.items;
}

export async function getAdminAudit() {
  const payload = await apiJson<{ items: RawAdminAuditEntry[] }>("/admin/audit", {
    headers: await getAuthHeaders({ requireUser: true }),
  });
  return payload.items;
}

export async function getAdminUsers() {
  const payload = await apiJson<{ items: RawAdminUsersEntry[] }>("/admin/users", {
    headers: await getAuthHeaders({ requireUser: true }),
  });
  return payload.items;
}

export async function getAdminFiles() {
  const payload = await apiJson<{ items: RawAdminFilesEntry[] }>("/admin/files", {
    headers: await getAuthHeaders({ requireUser: true }),
  });
  return payload.items;
}
