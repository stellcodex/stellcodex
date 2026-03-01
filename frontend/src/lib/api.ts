"use client";

import type {
  FileDetailResponse,
  JobRecord,
  ProjectTreeResponse,
  ViewerEngine,
  FileKind,
} from "@/lib/stellcodex/types";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  const payload = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(
      (payload && typeof payload === "object" && "error" in payload && typeof payload.error === "string"
        ? payload.error
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

export async function createFolder(input: { projectId: string; parentId?: string | null; name: string }) {
  return api<{ folder: { id: string; name: string } }>(`/api/project/${input.projectId}/tree`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "createFolder", ...input }),
  });
}

export async function moveFiles(input: { projectId: string; fileIds: string[]; folderId: string }) {
  return api<{ moved: number }>(`/api/project/${input.projectId}/tree`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "moveFiles", ...input }),
  });
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

