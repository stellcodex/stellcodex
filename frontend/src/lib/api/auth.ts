import type { RawLoginResult, RawSessionState } from "@/lib/contracts/auth";

import { apiFetch, apiJson } from "./fetch";

export async function login(email: string, password: string) {
  return apiJson<RawLoginResult>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function logout() {
  await apiFetch("/auth/logout", {
    method: "POST",
  });
}

export async function getMe() {
  return apiJson<RawSessionState>("/auth/me");
}
