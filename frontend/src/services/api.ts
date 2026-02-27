import { apiFetch, getApiBase } from "@/lib/apiClient";

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
  lods?: Record<
    string,
    {
      key?: string;
      ready?: boolean;
      url?: string;
      triangle_count?: number | null;
    }
  > | null;
  quality_default?: string | null;
  view_mode_default?: string | null;
};

export type RecentFileItem = {
  file_id: string;
  original_name: string;
  kind: string;
  status: string;
  created_at: string;
  thumbnail_url?: string | null;
};

export type AssemblyTreeNode = {
  id?: string;
  name?: string;
  display_name?: string;
  label?: string;
  kind?: string;
  selectable?: boolean;
  children?: AssemblyTreeNode[];
  [key: string]: unknown;
};

export type FileManifest = {
  format_version?: string;
  app?: string;
  model_id?: string;
  assembly_tree?: AssemblyTreeNode[];
  part_count?: number | null;
  [key: string]: unknown;
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

export type UploadDirectResult = {
  file_id: string;
};

const API_BASE = getApiBase();
const UPLOAD_TIMEOUT_MS = 120_000;

function getGuestTokenKey() {
  return "stellcodex_access_token";
}

function getUserTokenKey() {
  return "scx_token";
}

function getUserToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(getUserTokenKey());
}

async function ensureGuestToken(): Promise<string> {
  const existing =
    typeof window !== "undefined" ? window.localStorage.getItem(getGuestTokenKey()) : null;
  if (existing) return existing;

  const res = await apiFetch("/auth/guest", { method: "POST" });
  if (!res.ok) {
    throw new Error("Misafir token alınamadı.");
  }
  const data = await res.json();
  const token = data?.access_token as string;
  if (!token || typeof token !== "string") {
    throw new Error("Misafir token yanıtı geçersiz.");
  }
  if (typeof window !== "undefined") {
    window.localStorage.setItem(getGuestTokenKey(), token);
  }
  return token;
}

async function authFetch(
  input: RequestInfo,
  init?: RequestInit,
  options?: { requireUser?: boolean }
) {
  const doFetch = async (token: string) => {
    const headers = new Headers(init?.headers || {});
    headers.set("Authorization", `Bearer ${token}`);
    if (!headers.has("Content-Type") && init?.body && !(init.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    if (typeof input === "string") {
      return apiFetch(input, { ...init, headers });
    }
    return fetch(input, { ...init, headers });
  };

  try {
    const userToken = getUserToken();
    if (options?.requireUser && !userToken) {
      throw new Error("Kullanıcı tokenı gerekli.");
    }

    let token = userToken || (await ensureGuestToken());
    let res = await doFetch(token);
    if (res.status === 401) {
      if (typeof window !== "undefined") {
        if (userToken) {
          window.localStorage.removeItem(getUserTokenKey());
        } else {
          window.localStorage.removeItem(getGuestTokenKey());
        }
      }
      if (userToken && !options?.requireUser) {
        token = await ensureGuestToken();
        res = await doFetch(token);
      } else if (!userToken) {
        token = await ensureGuestToken();
        res = await doFetch(token);
      }
    }
    return res;
  } catch (error) {
    throw normalizeTransportError(error, "API isteği başarısız.");
  }
}

async function userFetch(input: RequestInfo, init?: RequestInit) {
  return authFetch(input, init, { requireUser: true });
}

function readErrorDetail(err: unknown, fallback: string): string {
  if (!err) return fallback;
  if (typeof err === "string") return err;
  if (typeof err === "object" && err !== null) {
    const detail = (err as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (typeof first === "string") return first;
      if (typeof first === "object" && first !== null) {
        const msg = (first as { msg?: unknown }).msg;
        if (typeof msg === "string") return msg;
      }
    }
  }
  return fallback;
}

function normalizeTransportError(error: unknown, fallback: string): Error {
  if (error instanceof Error) {
    const message = (error.message || "").toLowerCase();
    if (message.includes("failed to fetch") || message.includes("networkerror") || message.includes("load failed")) {
      return new Error("Sunucuya erişilemedi. API yönlendirmesi veya ağ bağlantısını kontrol edin.");
    }
    return error;
  }
  return new Error(fallback);
}

async function throwHttpError(res: Response, fallback: string): Promise<never> {
  const err = await res.json().catch(() => null);
  if (res.status === 401) {
    throw new Error("Kimlik doğrulama başarısız (401). Misafir token yenilenemedi.");
  }
  if (res.status === 403) {
    throw new Error("Erişim reddedildi (403). Bu dosyaları görüntüleme izni yok.");
  }
  throw new Error(readErrorDetail(err, `${fallback} (${res.status})`));
}

export async function fetchAuthedBlobUrl(url: string): Promise<string> {
  const res = await authFetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "İçerik yüklenemedi.");
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function getDxfManifest(fileId: string): Promise<DxfManifest> {
  const res = await authFetch(`${API_BASE}/files/${fileId}/dxf/manifest`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "DXF manifesti yüklenemedi.");
  }
  return res.json();
}

export async function getDxfRender(fileId: string, layers: string[]): Promise<string> {
  const params = layers.length ? `?layers=${encodeURIComponent(layers.join(","))}` : "?layers=";
  const res = await authFetch(`${API_BASE}/files/${fileId}/dxf/render${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "DXF çizimi üretilemedi.");
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function listFiles(): Promise<FileItem[]> {
  const res = await authFetch(`${API_BASE}/files`);
  if (!res.ok) await throwHttpError(res, "Dosyalar yüklenemedi.");
  const data = await res.json();
  return data.items || [];
}

export async function listRecentFiles(limit = 8): Promise<RecentFileItem[]> {
  const safeLimit = Number.isFinite(limit) ? Math.max(1, Math.min(20, Math.floor(limit))) : 8;
  const res = await authFetch(`${API_BASE}/files?recent=1&limit=${safeLimit}`);
  if (!res.ok) await throwHttpError(res, "Son yüklenen dosyalar alınamadı.");
  const data = await res.json().catch(() => null);
  if (data && typeof data === "object" && Array.isArray((data as { items?: unknown }).items)) {
    return (data as { items: RecentFileItem[] }).items;
  }
  return [];
}

export async function getFile(fileId: string): Promise<FileDetail> {
  const res = await authFetch(`${API_BASE}/files/${fileId}`);
  if (!res.ok) throw new Error("Dosya yüklenemedi.");
  return res.json();
}

export async function getFileStatus(fileId: string) {
  const res = await authFetch(`${API_BASE}/files/${fileId}/status`);
  if (res.ok) return res.json();

  if (res.status === 404) {
    const file = await getFile(fileId);
    const raw = (file.status || "").toLowerCase();
    const state =
      raw === "ready" || raw === "succeeded"
        ? "succeeded"
        : raw === "failed"
        ? "failed"
        : raw === "running" || raw === "processing"
        ? "running"
        : "queued";
    const derivatives: string[] = [];
    if (file.gltf_key) derivatives.push("gltf");
    if (file.thumbnail_key) derivatives.push("thumbnail");
    return {
      state,
      derivatives_available: derivatives,
      progress_hint: file.status || null,
    };
  }

  throw new Error("Durum yüklenemedi.");
}

export async function uploadDirect(file: File): Promise<UploadDirectResult> {
  const form = new FormData();
  form.append("upload", file);
  const abortController = new AbortController();
  const timeoutId = setTimeout(() => abortController.abort(), UPLOAD_TIMEOUT_MS);
  let res: Response;
  let data: unknown = null;
  try {
    res = await authFetch(`${API_BASE}/files/upload`, {
      method: "POST",
      body: form,
      signal: abortController.signal,
    });
    data = await res.json().catch(() => null);
  } catch (error: unknown) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Yükleme zaman aşımına uğradı. Lütfen tekrar deneyin.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    throw new Error(readErrorDetail(data, "Yükleme başarısız."));
  }
  const parsedFileId = (() => {
    if (typeof data !== "object" || data === null) return null;
    const candidate =
      (data as { file_id?: unknown; id?: unknown; scx_id?: unknown }).file_id ??
      (data as { id?: unknown }).id ??
      (data as { scx_id?: unknown }).scx_id;
    return typeof candidate === "string" && candidate.trim().length > 0 ? candidate : null;
  })();
  if (!parsedFileId) {
    throw new Error("Yükleme yanıtı geçersiz: file_id bulunamadı.");
  }
  return { file_id: parsedFileId };
}

export async function createShare(fileId: string, expiresInSeconds?: number): Promise<ShareResult> {
  const body = JSON.stringify({
    expires_in_seconds: expiresInSeconds,
  });
  const res = await authFetch(`${API_BASE}/files/${fileId}/share`, { method: "POST", body });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Paylaşım oluşturulamadı.");
  }
  return res.json();
}

export async function resolveShare(token: string) {
  const res = await apiFetch(`/share/${token}`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Paylaşım geçersiz.");
  }
  return res.json();
}

export async function setVisibility(fileId: string, visibility: "private" | "public" | "hidden") {
  const body = JSON.stringify({ visibility });
  const res = await authFetch(`${API_BASE}/files/${fileId}/visibility`, { method: "PATCH", body });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Görünürlük güncellenemedi.");
  }
  return res.json();
}

export async function getFileManifest(fileId: string): Promise<FileManifest> {
  const res = await authFetch(`${API_BASE}/files/${fileId}/manifest`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Manifest yüklenemedi.");
  }
  return res.json();
}

export async function downloadScx(fileId: string): Promise<Blob> {
  const res = await authFetch(`${API_BASE}/files/${fileId}/scx`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "SCX indirilemedi.");
  }
  return res.blob();
}

export async function getMe() {
  const res = await userFetch(`${API_BASE}/me`);
  if (!res.ok) throw new Error("Yetkisiz.");
  return res.json();
}

export async function requestRenderPreset(fileId: string, preset: string) {
  const body = JSON.stringify({ preset });
  const res = await authFetch(`${API_BASE}/files/${fileId}/render`, { method: "POST", body });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "Render isteği başarısız.");
  }
  return res.json();
}
