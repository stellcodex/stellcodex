import { ApiError } from "@/lib/api/errors";

const API_VERSION_PATH = "/api/v1";
const GUEST_TOKEN_KEY = "stellcodex_access_token";
const USER_TOKEN_KEY = "scx_token";

function resolveApiBase(raw?: string) {
  const value = (raw || "").trim().replace(/\/+$/, "");
  if (!value) return API_VERSION_PATH;
  if (value.startsWith("/")) return value === "/api" ? API_VERSION_PATH : value;
  if (/^https?:\/\//i.test(value)) return value;
  return `/${value}`;
}

const API_BASE = resolveApiBase(process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE);

function buildUrl(path: string) {
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith("/")) {
    if (path.startsWith(API_VERSION_PATH)) {
      if (API_BASE === API_VERSION_PATH) return path;
      return `${API_BASE}${path.slice(API_VERSION_PATH.length)}`;
    }
    return `${API_BASE}${path}`;
  }
  return `${API_BASE}/${path}`;
}

function getStoredToken(requireUser = false) {
  if (typeof window === "undefined") return null;
  const userToken = window.localStorage.getItem(USER_TOKEN_KEY);
  if (requireUser) return userToken;
  return userToken || window.localStorage.getItem(GUEST_TOKEN_KEY);
}

function safeMessageFromStatus(status: number) {
  if (status === 401) return ["unauthorized", "Authentication is required."] as const;
  if (status === 403) return ["forbidden", "Access denied."] as const;
  if (status === 404) return ["not_found", "The requested resource was not found."] as const;
  if (status === 410) return ["expired", "Share expired."] as const;
  if (status === 429) return ["rate_limited", "Too many requests. Try again later."] as const;
  if (status >= 500) return ["server_error", "The server could not complete the request."] as const;
  return ["request_failed", "The request could not be completed."] as const;
}

async function parseFailure(res: Response) {
  const payload = await res.json().catch(() => null);
  const [code, defaultMessage] = safeMessageFromStatus(res.status);
  const detail =
    typeof payload?.detail === "string" && payload.detail.trim().length > 0
      ? payload.detail.trim()
      : defaultMessage;
  return new ApiError(res.status, code, detail);
}

export async function ensureGuestToken() {
  if (typeof window === "undefined") return null;
  const existing = window.localStorage.getItem(GUEST_TOKEN_KEY);
  if (existing) return existing;
  const res = await fetch(buildUrl("/auth/guest"), { method: "POST" });
  const payload = await res.json().catch(() => null);
  if (!res.ok || !payload?.access_token) {
    throw new ApiError(res.status || 500, "guest_token_failed", "Guest access could not be initialized.");
  }
  window.localStorage.setItem(GUEST_TOKEN_KEY, payload.access_token);
  return payload.access_token as string;
}

export async function apiFetch(path: string, init?: RequestInit, options?: { requireUser?: boolean; public?: boolean }) {
  const headers = new Headers(init?.headers || {});
  if (!options?.public) {
    let token = getStoredToken(Boolean(options?.requireUser));
    if (!token && !options?.requireUser) {
      token = await ensureGuestToken();
    }
    if (!token && options?.requireUser) {
      throw new ApiError(401, "unauthorized", "Authentication is required.");
    }
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  if (init?.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path), {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(503, "network_error", "The server could not be reached.");
  }

  if (!res.ok) {
    throw await parseFailure(res);
  }
  return res;
}

export async function apiFetchJson<T>(path: string, init?: RequestInit, options?: { requireUser?: boolean; public?: boolean }) {
  const res = await apiFetch(path, init, options);
  return (await res.json().catch(() => null)) as T;
}

export function storeUserToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(USER_TOKEN_KEY, token);
  window.localStorage.removeItem(GUEST_TOKEN_KEY);
}

export function clearStoredTokens() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(USER_TOKEN_KEY);
  window.localStorage.removeItem(GUEST_TOKEN_KEY);
}
