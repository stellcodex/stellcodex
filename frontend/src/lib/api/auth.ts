import type { RawLoginResult, RawSessionUser } from "@/lib/contracts/auth";

import { apiFetch, apiJson } from "./fetch";
import { clearUserToken, getAuthHeaders, getUserToken, setUserToken } from "./session";

export async function login(email: string, password: string) {
  const result = await apiJson<RawLoginResult>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  setUserToken(result.access_token);
  return result;
}

export async function logout() {
  const token = getUserToken();
  if (!token) {
    clearUserToken();
    return;
  }
  try {
    await apiFetch("/auth/logout", {
      method: "POST",
      headers: await getAuthHeaders({ requireUser: true }),
    });
  } finally {
    clearUserToken();
  }
}

export async function getMe() {
  return apiJson<RawSessionUser>("/auth/me", {
    headers: await getAuthHeaders({ requireUser: true }),
  });
}
