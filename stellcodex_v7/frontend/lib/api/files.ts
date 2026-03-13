import { apiFetchJson, ensureGuestToken } from "@/lib/api/client";

export async function listFiles(page = 1, pageSize = 50) {
  return apiFetchJson(`/files?page=${page}&page_size=${pageSize}`);
}

export async function listRecentFiles(limit = 8) {
  return apiFetchJson(`/files?recent=1&limit=${limit}`);
}

export async function getFile(fileId: string) {
  return apiFetchJson(`/files/${encodeURIComponent(fileId)}`);
}

export async function getFileVersions(fileId: string) {
  return apiFetchJson(`/files/${encodeURIComponent(fileId)}/versions`);
}

export async function getFileStatus(fileId: string) {
  return apiFetchJson(`/files/${encodeURIComponent(fileId)}/status`);
}

export async function getFileManifest(fileId: string) {
  return apiFetchJson(`/files/${encodeURIComponent(fileId)}/manifest`);
}

export async function listFileShares(fileId: string) {
  return apiFetchJson(`/files/${encodeURIComponent(fileId)}/shares`);
}

export async function uploadFile(
  file: File,
  options?: {
    onProgress?: (loaded: number, total: number) => void;
    signal?: AbortSignal;
  }
): Promise<{ file_id: string }> {
  const token = await ensureGuestToken();
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/v1/files/upload");
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.responseType = "json";
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        options?.onProgress?.(event.loaded, event.total);
      }
    };
    xhr.onerror = () => reject(new Error("The upload could not be completed."));
    xhr.onabort = () => reject(new Error("The upload was cancelled."));
    xhr.onload = () => {
      const payload = xhr.response;
      if (xhr.status < 200 || xhr.status >= 300 || !payload?.file_id) {
        reject(new Error(payload?.detail || "Upload failed."));
        return;
      }
      resolve({ file_id: payload.file_id as string });
    };
    if (options?.signal) {
      options.signal.addEventListener("abort", () => xhr.abort(), { once: true });
    }
    const formData = new FormData();
    formData.append("upload", file);
    xhr.send(formData);
  });
}
