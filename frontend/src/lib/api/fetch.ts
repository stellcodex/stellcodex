export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const API_BASE = resolveApiBase(
  process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE || process.env.NEXT_PUBLIC_API_BASE_URL,
);

function resolveApiBase(rawValue: string | undefined) {
  const value = String(rawValue || "").trim().replace(/\/+$/, "");
  if (!value) return "/api/v1";
  if (value.startsWith("http://") || value.startsWith("https://")) {
    try {
      const parsed = new URL(value);
      return parsed.pathname.endsWith("/api/v1") ? value : `${value}/api/v1`;
    } catch {
      return "/api/v1";
    }
  }
  if (value === "/api") return "/api/v1";
  if (value.endsWith("/api/v1")) return value;
  if (value.endsWith("/api")) return `${value}/v1`;
  return `${value}/api/v1`;
}

export function getApiBase() {
  return API_BASE;
}

function resolveApiUrl(path: string) {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  if (path.startsWith("/api/v1")) return path;
  if (path.startsWith("/")) return `${API_BASE}${path}`;
  return `${API_BASE}/${path}`;
}

export async function apiFetch(path: string, init?: RequestInit) {
  const response = await fetch(resolveApiUrl(path), {
    ...init,
    headers: init?.headers,
    cache: "no-store",
  });
  return response;
}

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, init);
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body && typeof body === "object" && "detail" in body ? body.detail : body;
    const message =
      typeof detail === "string" && detail.trim().length > 0
        ? detail
        : `API request failed (${response.status})`;
    throw new ApiError(response.status, message, detail);
  }
  return body as T;
}
