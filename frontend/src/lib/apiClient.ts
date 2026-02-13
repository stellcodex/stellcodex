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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/v1";
const DEFAULT_TIMEOUT_MS = 15_000;

export function getApiBase() {
  return API_BASE;
}

function resolveApiUrl(path: string) {
  if (/^https?:\/\//i.test(path)) return path;
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
    const fallback = options?.fallbackMessage || "API isteği başarısız.";
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
