import { apiFetchJson, clearStoredTokens } from "@/lib/api/client";

export type AuthUser = {
  id: string;
  email: string;
  role: string;
};

export async function getMe() {
  return apiFetchJson<AuthUser>("/auth/me", undefined, { requireUser: true });
}

export async function logout() {
  try {
    await apiFetchJson("/auth/logout", { method: "POST" });
  } finally {
    clearStoredTokens();
  }
}
