"use client";

import { apiFetchJson } from "@/lib/apiClient";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("scx_token");
}

async function adminFetch<T = any>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  if (!token) throw new Error("An access token is required.");
  const headers = new Headers(init?.headers || {});
  headers.set("Authorization", `Bearer ${token}`);
  if (!headers.has("Content-Type") && init?.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  return apiFetchJson<T>(path, { ...init, headers }, { fallbackMessage: "The admin request failed." });
}

export function fetchAdminHealth(): Promise<any> {
  return adminFetch("/admin/health");
}

export function fetchAdminQueues(): Promise<any> {
  return adminFetch("/admin/queues");
}

export function fetchAdminFailed(limit = 50): Promise<any> {
  return adminFetch(`/admin/queues/failed?limit=${limit}`);
}

export function fetchAdminUsers(): Promise<any> {
  return adminFetch("/admin/users");
}

export function fetchAdminFiles(): Promise<any> {
  return adminFetch("/admin/files");
}

export function fetchAdminShares(): Promise<any> {
  return adminFetch("/admin/shares");
}

export function fetchAdminApprovals(): Promise<any> {
  return adminFetch("/admin/approvals");
}

export function approveAdminApproval(approvalId: string, reason?: string): Promise<any> {
  return adminFetch(`/admin/approvals/${encodeURIComponent(approvalId)}:approve`, {
    method: "POST",
    body: JSON.stringify({ reason: reason || null }),
  });
}

export function rejectAdminApproval(approvalId: string, reason?: string): Promise<any> {
  return adminFetch(`/admin/approvals/${encodeURIComponent(approvalId)}:reject`, {
    method: "POST",
    body: JSON.stringify({ reason: reason || null }),
  });
}

export function fetchAdminAudit(): Promise<any> {
  return adminFetch("/admin/audit");
}
