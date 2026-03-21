import type { RawSessionState } from "@/lib/contracts/auth";
import type { SessionUser } from "@/lib/contracts/ui";

export function mapSessionUser(session: RawSessionState): SessionUser | null {
  if (!session.authenticated || !session.user) return null;
  return {
    label: session.user.full_name || session.user.email,
    role: session.user.role,
    email: session.user.email,
    fullName: session.user.full_name,
    authProvider: session.user.auth_provider,
  };
}
