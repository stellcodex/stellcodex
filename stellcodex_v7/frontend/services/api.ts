import { apiFetch, getApiBase } from "@/lib/apiClient";

export type FileItem = {
  file_id: string;
  original_name: string;
  original_filename: string;
  kind: string;
  mode?: string | null;
  created_at: string;
  content_type: string;
  size_bytes: number;
  status: string;
  visibility: string;
  thumbnail_url?: string | null;
  preview_url?: string | null;
  preview_urls?: string[] | null;
  gltf_url?: string | null;
  original_url?: string | null;
  bbox_meta?: { x?: number; y?: number; z?: number; [key: string]: unknown } | null;
  part_count?: number | null;
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

export type ExplorerFolder = {
  folder_key: string;
  parent_key?: string | null;
  label: string;
  item_count: number;
};

export type ExplorerTreeResponse = {
  project_id: string;
  folders: ExplorerFolder[];
};

export type ExplorerItem = {
  file_id: string;
  name: string;
  ext: string;
  kind: string;
  mode: string;
  size: number;
  created_at: string;
  status: string;
  thumb_url?: string | null;
  preview_urls?: string[] | null;
  bbox_meta?: { x?: number; y?: number; z?: number; [key: string]: unknown } | null;
  part_count?: number | null;
  open_url: string;
};

export type ExplorerListResponse = {
  project_id: string;
  folder_key?: string | null;
  total: number;
  items: ExplorerItem[];
};

export type AssemblyTreeNode = {
  id?: string;
  name?: string;
  display_name?: string;
  label?: string;
  occurrence_id?: string;
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
  id?: string;
  token: string;
  expires_at: string;
  permission?: string;
};

export type ShareResolveResult = {
  file_id: string;
  status: string;
  permission: string;
  can_view: boolean;
  can_download: boolean;
  expires_at: string;
  content_type: string;
  original_filename: string;
  size_bytes: number;
  gltf_url?: string | null;
  original_url?: string | null;
  expires_in_seconds?: number;
};

export type LibraryItem = {
  id: string;
  file_id: string;
  visibility: "private" | "unlisted" | "public";
  slug: string;
  title: string;
  description?: string | null;
  tags: string[];
  cover_thumb?: string | null;
  share_url?: string | null;
  stats?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type LibraryFeedResponse = {
  items: LibraryItem[];
  total: number;
  page: number;
  page_size: number;
};

export type UploadDirectResult = {
  file_id: string;
};

export type ProjectSummary = {
  id: string;
  name: string;
  file_count: number;
  updated_at?: string | null;
  files?: Array<{
    file_id: string;
    original_filename: string;
    status: string;
    kind?: string | null;
    mode?: string | null;
    created_at?: string | null;
  }>;
};

export type JobStatus = {
  job_id: string;
  status: string;
  enqueued_at?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  origin?: string | null;
  timeout?: number | null;
  meta?: Record<string, unknown> | null;
  result?: string | null;
  error?: string | null;
};

export type AppsCatalogItem = {
  id: string;
  slug: string;
  name: string;
  category: string;
  tier: string;
  enabled_by_default: boolean;
  enabled: boolean;
  routes: string[];
  required_capabilities: string[];
  supported_formats: string[];
};

export type AppManifestResponse = {
  slug: string;
  manifest: Record<string, unknown>;
};

export type DecisionJsonResponse = {
  file_id: string;
  state_code: string;
  state_label: string;
  status_gate: string;
  approval_required: boolean;
  risk_flags: string[];
  decision_json: Record<string, unknown>;
};

export class ApiHttpError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiHttpError";
    this.status = status;
  }
}

const API_BASE = getApiBase();
const UPLOAD_TIMEOUT_MS = 300_000;

function inferKind(contentType: string, name: string): "2d" | "3d" {
  const lowerName = name.toLowerCase();
  const lowerType = contentType.toLowerCase();
  if (lowerName.endsWith(".dxf")) return "2d";
  if (lowerType === "application/pdf") return "2d";
  if (lowerType.startsWith("image/")) return "2d";
  return "3d";
}

function normalizeFileItem(input: unknown): FileItem {
  const data = (input && typeof input === "object" ? input : {}) as Record<string, unknown>;
  const originalName =
    (typeof data.original_name === "string" && data.original_name.trim()) ||
    (typeof data.original_filename === "string" && data.original_filename.trim()) ||
    "isimsiz";
  const contentType = typeof data.content_type === "string" ? data.content_type : "application/octet-stream";
  const sizeBytes = typeof data.size_bytes === "number" ? data.size_bytes : 0;
  const status = typeof data.status === "string" ? data.status : "queued";
  const visibility = typeof data.visibility === "string" ? data.visibility : "private";
  const kind = typeof data.kind === "string" && data.kind ? data.kind : inferKind(contentType, originalName);
  const createdAt = typeof data.created_at === "string" ? data.created_at : new Date().toISOString();

  return {
    file_id: typeof data.file_id === "string" ? data.file_id : "",
    original_name: originalName,
    original_filename: originalName,
    kind,
    mode: typeof data.mode === "string" ? data.mode : null,
    created_at: createdAt,
    content_type: contentType,
    size_bytes: sizeBytes,
    status,
    visibility,
    thumbnail_url: typeof data.thumbnail_url === "string" ? data.thumbnail_url : null,
    preview_url: typeof data.preview_url === "string" ? data.preview_url : null,
    preview_urls: Array.isArray(data.preview_urls)
      ? (data.preview_urls.filter((x): x is string => typeof x === "string") as string[])
      : null,
    gltf_url: typeof data.gltf_url === "string" ? data.gltf_url : null,
    original_url: typeof data.original_url === "string" ? data.original_url : null,
    bbox_meta: data.bbox_meta && typeof data.bbox_meta === "object" ? (data.bbox_meta as FileItem["bbox_meta"]) : null,
    part_count: typeof data.part_count === "number" ? data.part_count : null,
    error: typeof data.error === "string" ? data.error : null,
  };
}

function normalizeFileDetail(input: unknown): FileDetail {
  const item = normalizeFileItem(input);
  const data = (input && typeof input === "object" ? input : {}) as Record<string, unknown>;
  return {
    ...item,
    lods:
      data.lods && typeof data.lods === "object"
        ? (data.lods as FileDetail["lods"])
        : null,
    quality_default: typeof data.quality_default === "string" ? data.quality_default : null,
    view_mode_default: typeof data.view_mode_default === "string" ? data.view_mode_default : null,
  };
}

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
    throw new ApiHttpError(401, "Yetkisiz / token alınamadı.");
  }
  if (res.status === 403) {
    throw new ApiHttpError(403, "Erişim yok.");
  }
  if (res.status === 404) {
    throw new ApiHttpError(404, "Bulunamadı.");
  }
  if (res.status === 410) {
    throw new ApiHttpError(410, "Paylaşım süresi doldu.");
  }
  if (res.status === 429) {
    throw new ApiHttpError(429, "Çok fazla istek gönderildi.");
  }
  throw new ApiHttpError(res.status, readErrorDetail(err, `${fallback} (${res.status})`));
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
  const data = await res.json().catch(() => null);
  if (!data || typeof data !== "object") return [];
  const rawItems = (data as { items?: unknown }).items;
  if (!Array.isArray(rawItems)) return [];
  return rawItems.map((item) => normalizeFileItem(item));
}

export async function getExplorerTree(projectId = "default"): Promise<ExplorerTreeResponse> {
  const res = await authFetch(`${API_BASE}/explorer/tree?project_id=${encodeURIComponent(projectId)}`);
  if (!res.ok) await throwHttpError(res, "Explorer ağacı yüklenemedi.");
  const data = (await res.json().catch(() => null)) as ExplorerTreeResponse | null;
  return data || { project_id: projectId, folders: [] };
}

export async function getExplorerList(params: {
  projectId?: string;
  folderKey?: string | null;
  q?: string;
  sort?: "newest" | "oldest";
  filter?: string | null;
}): Promise<ExplorerListResponse> {
  const query = new URLSearchParams();
  query.set("project_id", params.projectId || "default");
  if (params.folderKey) query.set("folder_key", params.folderKey);
  if (params.q) query.set("q", params.q);
  if (params.sort) query.set("sort", params.sort);
  if (params.filter) query.set("filter", params.filter);
  const res = await authFetch(`${API_BASE}/explorer/list?${query.toString()}`);
  if (!res.ok) await throwHttpError(res, "Explorer liste yüklenemedi.");
  const data = (await res.json().catch(() => null)) as ExplorerListResponse | null;
  return data || { project_id: params.projectId || "default", folder_key: params.folderKey || null, total: 0, items: [] };
}

export async function getFormatsRegistry() {
  const res = await apiFetch(`${API_BASE}/formats`);
  if (!res.ok) await throwHttpError(res, "Format listesi alınamadı.");
  return res.json();
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
  if (!res.ok) await throwHttpError(res, "Dosya yüklenemedi.");
  const data = await res.json().catch(() => null);
  return normalizeFileDetail(data);
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
    if (file.gltf_url) derivatives.push("gltf");
    if (file.thumbnail_url) derivatives.push("thumbnail");
    if (file.original_url) derivatives.push("original");
    return {
      state,
      derivatives_available: derivatives,
      progress_hint: file.status || null,
      progress_percent:
        state === "succeeded" ? 100 : state === "failed" ? 100 : state === "running" ? 55 : 5,
      stage: file.status || null,
    };
  }

  await throwHttpError(res, "Durum yüklenemedi.");
}

export async function getFileDecisionJson(fileId: string): Promise<DecisionJsonResponse> {
  const res = await authFetch(`${API_BASE}/files/${encodeURIComponent(fileId)}/decision_json`);
  if (!res.ok) await throwHttpError(res, "Decision JSON yüklenemedi.");
  return res.json();
}

export async function listAppsCatalog(includeDisabled = false): Promise<AppsCatalogItem[]> {
  const suffix = includeDisabled ? "?include_disabled=true" : "";
  const res = await authFetch(`${API_BASE}/apps/catalog${suffix}`);
  if (!res.ok) await throwHttpError(res, "Apps katalogu yüklenemedi.");
  const data = await res.json().catch(() => []);
  return Array.isArray(data) ? (data as AppsCatalogItem[]) : [];
}

export async function getAppManifest(slug: string): Promise<AppManifestResponse> {
  const res = await authFetch(`${API_BASE}/apps/${encodeURIComponent(slug)}/manifest`);
  if (!res.ok) await throwHttpError(res, "App manifesti yüklenemedi.");
  return res.json();
}

export async function uploadDirect(file: File, projectId?: string): Promise<UploadDirectResult> {
  const form = new FormData();
  form.append("upload", file);
  if (projectId) {
    form.append("projectId", projectId);
  }
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

export async function resolveShare(token: string): Promise<ShareResolveResult> {
  const res = await apiFetch(`${API_BASE}/shares/${encodeURIComponent(token)}`);
  if (!res.ok) await throwHttpError(res, "Paylaşım geçersiz.");
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

export async function publishLibraryItem(input: {
  file_id: string;
  visibility: "private" | "unlisted" | "public";
  title?: string;
  description?: string;
  tags?: string[];
}): Promise<LibraryItem> {
  const res = await authFetch(`${API_BASE}/library/publish`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  if (!res.ok) await throwHttpError(res, "Publish başarısız.");
  return res.json();
}

export async function updateLibraryItem(
  itemId: string,
  input: { title?: string; description?: string; tags?: string[]; visibility?: "private" | "unlisted" | "public" }
): Promise<LibraryItem> {
  const res = await authFetch(`${API_BASE}/library/item/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
  if (!res.ok) await throwHttpError(res, "Library item güncellenemedi.");
  return res.json();
}

export async function unpublishLibraryItem(itemId: string): Promise<void> {
  const res = await authFetch(`${API_BASE}/library/unpublish`, {
    method: "POST",
    body: JSON.stringify({ item_id: itemId }),
  });
  if (!res.ok) await throwHttpError(res, "Unpublish başarısız.");
}

export async function getLibraryFeed(params?: { q?: string; sort?: "new" | "old"; page?: number; page_size?: number }): Promise<LibraryFeedResponse> {
  const query = new URLSearchParams();
  if (params?.q) query.set("q", params.q);
  if (params?.sort) query.set("sort", params.sort);
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));
  const suffix = query.toString();
  const path = `${API_BASE}/library/feed${suffix ? `?${suffix}` : ""}`;
  const res = await apiFetch(path);
  if (!res.ok) await throwHttpError(res, "Library feed alınamadı.");
  return res.json();
}

export async function getLibraryItem(slug: string): Promise<LibraryItem> {
  const res = await apiFetch(`${API_BASE}/library/item/${encodeURIComponent(slug)}`);
  if (!res.ok) await throwHttpError(res, "Library item alınamadı.");
  return res.json();
}

export async function logoutMe() {
  const res = await authFetch(`${API_BASE}/auth/logout`, { method: "POST" });
  if (!res.ok) await throwHttpError(res, "Oturum kapatilamadi.");
  return res.json();
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const res = await authFetch(`${API_BASE}/projects`);
  if (!res.ok) await throwHttpError(res, "Projeler yuklenemedi.");
  const data = await res.json().catch(() => []);
  return Array.isArray(data) ? (data as ProjectSummary[]) : [];
}

export async function createProject(name: string): Promise<ProjectSummary> {
  const res = await authFetch(`${API_BASE}/projects`, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  if (!res.ok) await throwHttpError(res, "Proje olusturulamadi.");
  return res.json();
}

export async function getProject(projectId: string): Promise<ProjectSummary> {
  const res = await authFetch(`${API_BASE}/projects/${encodeURIComponent(projectId)}`);
  if (!res.ok) await throwHttpError(res, "Proje yuklenemedi.");
  return res.json();
}

export async function downloadFileText(fileId: string): Promise<string> {
  const res = await authFetch(`${API_BASE}/files/${encodeURIComponent(fileId)}/download`);
  if (!res.ok) await throwHttpError(res, "Dosya indirilemedi.");
  return res.text();
}

export async function enqueueConvert(fileId: string): Promise<JobStatus> {
  const res = await authFetch(`${API_BASE}/jobs/convert`, {
    method: "POST",
    body: JSON.stringify({ file_id: fileId }),
  });
  if (!res.ok) await throwHttpError(res, "Convert isi baslatilamadi.");
  const data = await res.json();
  return { job_id: data.job_id, status: "queued" };
}

export async function enqueueMesh2d3d(fileId: string): Promise<JobStatus> {
  const res = await authFetch(`${API_BASE}/jobs/mesh2d3d`, {
    method: "POST",
    body: JSON.stringify({ file_id: fileId }),
  });
  if (!res.ok) await throwHttpError(res, "Mesh2D3D isi baslatilamadi.");
  const data = await res.json();
  return { job_id: data.job_id, status: "queued" };
}

export async function enqueueMoldcodesExport(input: {
  project_id: string;
  category: string;
  family: string;
  params: Record<string, unknown>;
}): Promise<JobStatus> {
  const res = await authFetch(`${API_BASE}/jobs/moldcodes_export`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  if (!res.ok) await throwHttpError(res, "MoldCodes export isi baslatilamadi.");
  const data = await res.json();
  return { job_id: data.job_id, status: "queued" };
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const res = await authFetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`);
  if (!res.ok) await throwHttpError(res, "Job durumu yuklenemedi.");
  return res.json();
}
