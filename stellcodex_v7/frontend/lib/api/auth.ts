import { apiFetchJson, clearStoredTokens, storeUserToken } from "@/lib/api/client";

export type AuthUser = {
  id: string;
  email: string;
  role: string;
};

export type PasswordResetRequestResult = {
  ok: boolean;
  deliveryEnabled: boolean;
};

type AuthResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  role: string;
};

type PasswordResetRequestResponse = {
  ok: boolean;
  delivery_enabled: boolean;
};

type PasswordResetResponse = {
  ok: boolean;
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

export async function requestPasswordReset(email: string): Promise<PasswordResetRequestResult> {
  const response = await apiFetchJson<PasswordResetRequestResponse>(
    "/auth/request-password-reset",
    {
      method: "POST",
      body: JSON.stringify({ email }),
    },
    { public: true },
  );
  return {
    ok: response.ok,
    deliveryEnabled: response.delivery_enabled,
  };
}

export async function resetPasswordWithToken(token: string, password: string): Promise<boolean> {
  const response = await apiFetchJson<PasswordResetResponse>(
    "/auth/reset-password",
    {
      method: "POST",
      body: JSON.stringify({ token, password }),
    },
    { public: true },
  );
  return response.ok;
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
