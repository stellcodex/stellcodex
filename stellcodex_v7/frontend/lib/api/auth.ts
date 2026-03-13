import { apiFetchJson, clearStoredTokens, storeUserToken } from "@/lib/api/client";

export type AuthUser = {
  id: string;
  email: string;
  role: string;
};

type AuthResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  role: string;
};

async function authenticate(path: string, payload: { email: string; password: string }) {
  const response = await apiFetchJson<AuthResponse>(
    path,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    { public: true },
  );
  storeUserToken(response.access_token);
  return {
    id: response.user_id,
    email: response.email,
    role: response.role,
  } satisfies AuthUser;
}

export function loginWithPassword(email: string, password: string) {
  return authenticate("/auth/login", { email, password });
}

export function registerWithPassword(email: string, password: string) {
  return authenticate("/auth/register", { email, password });
}

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
