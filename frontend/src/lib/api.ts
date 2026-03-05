"use client";

import type {
  FileDetailResponse,
  JobRecord,
  ProjectTreeResponse,
  ViewerEngine,
  FileKind,
} from "@/lib/stellcodex/types";

const USER_TOKEN_KEY = "scx_token";
const GUEST_TOKEN_KEY = "stellcodex_access_token";

function getStoredToken(key: string): string | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(key);
  return value && value.trim() ? value.trim() : null;
}

function writeTokenCookie(key: string, token: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${key}=${encodeURIComponent(token)}; path=/; max-age=86400; SameSite=Lax`;
}

async function ensureGuestToken(): Promise<string | null> {
  const existing = getStoredToken(GUEST_TOKEN_KEY);
  if (existing) {
    writeTokenCookie(GUEST_TOKEN_KEY, existing);
    return existing;
  }
  const res = await fetch("/api/v1/auth/guest", { method: "POST", cache: "no-store" }).catch(() => null);
  if (!res || !res.ok) return null;
  const payload = await res.json().catch(() => null);
  const token =
    payload && typeof payload === "object" && typeof (payload as { access_token?: unknown }).access_token === "string"
      ? String((payload as { access_token: string }).access_token).trim()
      : "";
  if (!token) return null;
  if (typeof window !== "undefined") window.localStorage.setItem(GUEST_TOKEN_KEY, token);
  writeTokenCookie(GUEST_TOKEN_KEY, token);
  return token;
}

async function getAccessToken(): Promise<string | null> {
  const userToken = getStoredToken(USER_TOKEN_KEY);
  if (userToken) {
    writeTokenCookie(USER_TOKEN_KEY, userToken);
    return userToken;
  }
  return ensureGuestToken();
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAccessToken();
  const headers = new Headers(init?.headers || {});
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(path, {
    ...init,
    headers,
    cache: "no-store",
  });
  const payload = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(
      (payload && typeof payload === "object" && "error" in payload && typeof payload.error === "string"
        ? payload.error
        : payload && typeof payload === "object" && "detail" in payload && typeof payload.detail === "string"
        ? payload.detail
        : null) || `Request failed (${res.status})`
    );
  }
  return payload as T;
}

export async function uploadFile(file: File, projectId?: string) {
  const form = new FormData();
  form.set("file", file);
  if (projectId) form.set("projectId", projectId);
  return api<{ fileId: string; jobId: string }>("/api/upload", { method: "POST", body: form });
}

export async function getJob(jobId: string) {
  return api<JobRecord>(`/api/job/${jobId}`);
}

export async function getDefaultProject() {
  return api<{ projectId: string; name: string }>("/api/projects/default");
}

export async function getProjectTree(projectId: string) {
  return api<ProjectTreeResponse>(`/api/project/${projectId}/tree`);
}

export async function getFile(fileId: string) {
  return api<FileDetailResponse>(`/api/file/${fileId}`);
}

export async function createShare(fileId: string, options: { canView: boolean; canDownload: boolean; password?: string; expiresAt?: string }) {
  return api<{ shareUrl: string; token: string }>(`/api/share`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fileId, ...options }),
  });
}

export async function getPublicShare(token: string) {
  return api<{
    file: FileDetailResponse["file"];
    previewUrl: string | null;
    downloadUrl: string;
    canView: boolean;
    canDownload: boolean;
    expiresAt?: string | null;
  }>(`/api/share/${token}`);
}

export async function resolveViewer(fileId: string) {
  return api<{ engine: ViewerEngine; kind: FileKind }>(`/api/view/resolve?fileId=${encodeURIComponent(fileId)}`);
}

export async function listArchive(fileId: string) {
  return api<{ entries: Array<{ path: string; sizeBytes: number; kind: FileKind }> }>(`/api/archive/${fileId}/list`);
}

export async function extractArchive(fileId: string) {
  return api<{ newFolderId: string }>(`/api/archive/${fileId}/extract`, { method: "POST" });
}

export async function deleteFiles(input: { projectId: string; fileIds: string[] }) {
  return api<{ deleted: number }>(`/api/project/${input.projectId}/tree`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "deleteFiles", ...input }),
  });
}

export async function getAdminSnapshot() {
  function getToken() {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem("scx_token");
  }
  const token = getToken();
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  const [healthRes, queuesRes] = await Promise.all([
    fetch("/api/v1/admin/health", { headers, cache: "no-store" }),
    fetch("/api/v1/admin/queues", { headers, cache: "no-store" }),
  ]);

  const systemInfo = healthRes.ok ? await healthRes.json() : {};
  const queues = queuesRes.ok ? await queuesRes.json() : {};

  return {
    jobs: [] as JobRecord[],
    pendingApprovals: [] as JobRecord[],
    systemInfo: { ...systemInfo, queues },
  };
}
