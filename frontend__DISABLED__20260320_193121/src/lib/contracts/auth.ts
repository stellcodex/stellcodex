export type SessionRole = "admin" | "member";
export type AuthProvider = "google" | "local";

export interface RawSessionAccount {
  id: string;
  email: string;
  full_name: string | null;
  role: SessionRole;
  auth_provider: AuthProvider;
  is_active: boolean;
  created_at: string | null;
  last_login_at: string | null;
}

export interface RawSessionState {
  authenticated: boolean;
  role: SessionRole | null;
  user: RawSessionAccount | null;
}

export interface RawLoginResult {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  role: SessionRole;
  full_name: string | null;
  auth_provider: AuthProvider;
  session: RawSessionState;
}
