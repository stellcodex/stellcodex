export interface RawGuestSession {
  access_token: string;
  token_type: string;
  guest_id: string;
  owner_sub: string;
}

export interface RawLoginResult {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  role: string;
}

export interface RawSessionUser {
  id: string;
  email: string;
  role: string;
  is_suspended: boolean;
}
