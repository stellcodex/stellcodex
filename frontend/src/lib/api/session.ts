import type { RawGuestSession } from "@/lib/contracts/auth";

import { apiJson } from "./fetch";

const USER_TOKEN_KEY = "scx_token";
const GUEST_TOKEN_KEY = "stellcodex_access_token";

function readStorage(key: string) {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

function writeStorage(key: string, value: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, value);
}

export function getUserToken() {
  return readStorage(USER_TOKEN_KEY);
}

export function setUserToken(token: string) {
  writeStorage(USER_TOKEN_KEY, token);
}

export function clearUserToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(USER_TOKEN_KEY);
}

export function getGuestToken() {
  return readStorage(GUEST_TOKEN_KEY);
}

export async function ensureGuestToken() {
  const existing = getGuestToken();
  if (existing) return existing;
  const created = await apiJson<RawGuestSession>("/auth/guest", { method: "POST" });
  writeStorage(GUEST_TOKEN_KEY, created.access_token);
  return created.access_token;
}

export async function getAccessToken(options?: { requireUser?: boolean }) {
  const userToken = getUserToken();
  if (options?.requireUser) {
    if (!userToken) throw new Error("A signed-in session is required.");
    return userToken;
  }
  return userToken ?? ensureGuestToken();
}

export async function getAuthHeaders(options?: { requireUser?: boolean; headers?: HeadersInit }) {
  const token = await getAccessToken(options);
  const headers = new Headers(options?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return headers;
}
