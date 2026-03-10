export class ApiClientError extends Error {
  status: number;
  detail: unknown;
  endpoint: string;

  constructor(params: { message: string; status: number; detail: unknown; endpoint: string }) {
    super(params.message);
    this.name = "ApiClientError";
    this.status = params.status;
    this.detail = params.detail;
    this.endpoint = params.endpoint;
  }
}

export class ApiTimeoutError extends Error {
  timeoutMs: number;
  endpoint: string;

  constructor(params: { timeoutMs: number; endpoint: string }) {
    super(`API timeout (${params.timeoutMs}ms): ${params.endpoint}`);
    this.name = "ApiTimeoutError";
    this.timeoutMs = params.timeoutMs;
    this.endpoint = params.endpoint;
  }
}

const API_VERSION_PATH = "/api/v1";
const API_BASE = resolveApiBase(process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE);
const DEFAULT_TIMEOUT_MS = 15_000;

export function getApiBase() {
  return API_BASE;
}

function resolveApiBase(raw: string | undefined) {
  const value = (raw || "").trim().replace(/\/+$/, "");
  if (!value) return API_VERSION_PATH;

  if (value.startsWith("/")) {
    return normalizeApiPath(value);
  }

  if (/^https?:\/\//i.test(value)) {
    try {
      const parsed = new URL(value);
      // Browser requests should stay same-origin to avoid CORS/preflight failures.
      if (typeof window !== "undefined" && parsed.origin !== window.location.origin) {
        return API_VERSION_PATH;
      }
      return `${parsed.origin}${normalizeApiPath(parsed.pathname)}`;
    } catch {
      return API_VERSION_PATH;
    }
  }

  return normalizeApiPath(`/${value.replace(/^\/+/, "")}`);
}

function normalizeApiPath(pathname: string) {
  const basePath = pathname.replace(/\/+$/, "");
  if (!basePath || basePath === "/") return API_VERSION_PATH;
  if (basePath === "/api") return API_VERSION_PATH;
  if (basePath === API_VERSION_PATH || basePath.endsWith(API_VERSION_PATH)) return basePath;
  if (basePath.endsWith("/api")) return `${basePath}/v1`;
  return `${basePath}${API_VERSION_PATH}`;
}

function resolveApiUrl(path: string) {
  if (/^https?:\/\//i.test(path)) return path;
  if (path === API_VERSION_PATH || path.startsWith(`${API_VERSION_PATH}/`)) {
    if (API_BASE === API_VERSION_PATH) return path;
    return `${API_BASE}${path.slice(API_VERSION_PATH.length)}`;
  }
  if (path === API_BASE || path.startsWith(`${API_BASE}/`)) return path;
  if (path.startsWith("/")) return `${API_BASE}${path}`;
  return `${API_BASE}/${path}`;
}

export async function apiFetch(
  path: string,
  init?: RequestInit,
  options?: { timeoutMs?: number }
): Promise<Response> {
  const endpoint = resolveApiUrl(path);
  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(endpoint, {
      ...init,
      signal: init?.signal ?? controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiTimeoutError({ timeoutMs, endpoint });
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export async function apiFetchJson<T = unknown>(
  path: string,
  init?: RequestInit,
  options?: {
    timeoutMs?: number;
    fallbackMessage?: string;
  }
): Promise<T> {
  const endpoint = resolveApiUrl(path);
  const res = await apiFetch(path, init, options);
  const payload = await res.json().catch(() => null);
  if (!res.ok) {
    const fallback = options?.fallbackMessage || "The API request failed.";
    const detail =
      (payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail?: unknown }).detail
        : null) ?? null;
    const message =
      typeof detail === "string" && detail.trim().length > 0 ? detail : `${fallback} (${res.status})`;
    throw new ApiClientError({
      message,
      status: res.status,
      detail,
      endpoint,
    });
  }
  return payload as T;
}
