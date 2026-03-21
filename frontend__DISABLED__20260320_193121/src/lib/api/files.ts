import type { RawFileDetail, RawFileManifest, RawFileStatus, RawFileSummary } from "@/lib/contracts/files";

import { apiFetch, apiJson } from "./fetch";
import { getAuthHeaders } from "./session";

export interface UploadProgressEvent {
  progress: number;
  fileId?: string;
}

export async function listFiles() {
  const payload = await apiJson<{ items: RawFileSummary[] }>("/files", {
    headers: await getAuthHeaders(),
  });
  return payload.items ?? [];
}

export async function listRecentFiles(limit = 8) {
  const payload = await apiJson<{ items: RawFileSummary[] }>(`/files?recent=1&limit=${limit}`, {
    headers: await getAuthHeaders(),
  });
  return payload.items ?? [];
}

export async function getFile(fileId: string) {
  return apiJson<RawFileDetail>(`/files/${encodeURIComponent(fileId)}`, {
    headers: await getAuthHeaders(),
  });
}

export async function getFileStatus(fileId: string) {
  return apiJson<RawFileStatus>(`/files/${encodeURIComponent(fileId)}/status`, {
    headers: await getAuthHeaders(),
  });
}

export async function getFileManifest(fileId: string) {
  return apiJson<RawFileManifest>(`/files/${encodeURIComponent(fileId)}/manifest`, {
    headers: await getAuthHeaders(),
  });
}

export async function uploadFile(
  file: File,
  options?: {
    projectId?: string;
    onProgress?: (event: UploadProgressEvent) => void;
  },
) {
  const formData = new FormData();
  formData.append("upload", file);
  if (options?.projectId) formData.append("projectId", options.projectId);

  return new Promise<{ file_id: string }>((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", "/api/v1/files/upload");
    request.withCredentials = true;
    request.responseType = "json";
    request.upload.addEventListener("progress", (event) => {
      if (!event.lengthComputable) return;
      options?.onProgress?.({
        progress: Math.round((event.loaded / event.total) * 100),
      });
    });
    request.onerror = () => reject(new Error("The upload request failed."));
    request.onload = () => {
      const payload = (request.response || {}) as { file_id?: unknown; detail?: unknown };
      if (request.status < 200 || request.status >= 300) {
        reject(new Error(typeof payload.detail === "string" ? payload.detail : "The upload failed."));
        return;
      }
      const fileId = typeof payload.file_id === "string" ? payload.file_id : null;
      if (!fileId) {
        reject(new Error("The upload response did not include a file_id."));
        return;
      }
      options?.onProgress?.({ progress: 100, fileId });
      resolve({ file_id: fileId });
    };
    request.send(formData);
  });
}

export async function fetchBlobUrl(path: string) {
  const response = await apiFetch(path, {
    headers: await getAuthHeaders(),
  });
  if (!response.ok) throw new Error(`Blob request failed (${response.status})`);
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
