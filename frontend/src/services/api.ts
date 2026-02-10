export type FileItem = {
  file_id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  status: string;
  visibility: string;
  gltf_key?: string | null;
  thumbnail_key?: string | null;
  preview_url?: string | null;
  error?: string | null;
};

export type FileDetail = FileItem & {
  gltf_url?: string | null;
  original_url?: string | null;
};

export type DxfLayer = {
  name: string;
  color: string;
  linetype: string;
  is_visible: boolean;
};

export type DxfManifest = {
  layers: DxfLayer[];
  bbox: { min_x: number; min_y: number; max_x: number; max_y: number };
  units: { code: number; name: string };
  entity_counts: Record<string, number>;
};

export type ShareResult = {
  token: string;
  expires_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

function getTokenKey() {
  return "stellcodex_access_token";
}

async function ensureGuestToken(): Promise<string> {
  const existing =
    typeof window !== "undefined" ? window.localStorage.getItem(getTokenKey()) : null;
  if (existing) return existing;

  const res = await fetch(`${API_BASE}/v1/auth/guest`, { method: "POST" });
  if (!res.ok) {
    throw new Error("Guest token unavailable");
  }
  const data = await res.json();
  const token = data?.access_token as string;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(getTokenKey(), token);
  }
  return token;
}

async function authFetch(input: RequestInfo, init?: RequestInit) {
  const doFetch = async (token: string) => {
    const headers = new Headers(init?.headers || {});
    headers.set("Authorization", `Bearer ${token}`);
    if (!headers.has("Content-Type") && init?.body && !(init.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    return fetch(input, { ...init, headers });
  };

  let token = await ensureGuestToken();
  let res = await doFetch(token);
  if (res.status === 401) {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(getTokenKey());
    }
    token = await ensureGuestToken();
    res = await doFetch(token);
  }
  return res;
}

export async function fetchAuthedBlobUrl(url: string): Promise<string> {
  const res = await authFetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Failed to load content");
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function getDxfManifest(fileId: string): Promise<DxfManifest> {
  const res = await authFetch(`${API_BASE}/v1/files/${fileId}/dxf/manifest`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Failed to load DXF manifest");
  }
  return res.json();
}

export async function getDxfRender(fileId: string, layers: string[]): Promise<string> {
  const params = layers.length ? `?layers=${encodeURIComponent(layers.join(","))}` : "?layers=";
  const res = await authFetch(`${API_BASE}/v1/files/${fileId}/dxf/render${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Failed to render DXF");
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function listFiles(): Promise<FileItem[]> {
  const res = await authFetch(`${API_BASE}/v1/files`);
  if (!res.ok) throw new Error("Failed to load files");
  const data = await res.json();
  return data.items || [];
}

export async function getFile(fileId: string): Promise<FileDetail> {
  const res = await authFetch(`${API_BASE}/v1/files/${fileId}`);
  if (!res.ok) throw new Error("Failed to load file");
  return res.json();
}

export async function uploadDirect(file: File) {
  const form = new FormData();
  form.append("upload", file);
  const res = await authFetch(`${API_BASE}/v1/files/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Upload failed");
  }
  return res.json();
}

export async function createShare(fileId: string, expiresInSeconds?: number): Promise<ShareResult> {
  const body = JSON.stringify({
    file_id: fileId,
    expires_in_seconds: expiresInSeconds,
  });
  const res = await authFetch(`${API_BASE}/v1/share`, { method: "POST", body });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Share failed");
  }
  return res.json();
}

export async function resolveShare(token: string) {
  const res = await fetch(`${API_BASE}/v1/share/${token}`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Share invalid");
  }
  return res.json();
}

export async function setVisibility(fileId: string, visibility: "private" | "public" | "hidden") {
  const body = JSON.stringify({ visibility });
  const res = await authFetch(`${API_BASE}/v1/files/${fileId}/visibility`, { method: "PATCH", body });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Visibility update failed");
  }
  return res.json();
}
