import { Badge } from "@/components/primitives/Badge";

export interface ShareExpiryBadgeProps {
  expiresAt?: string | null;
}

export function ShareExpiryBadge({ expiresAt }: ShareExpiryBadgeProps) {
  return <Badge variant={expiresAt ? "warning" : "muted"}>{expiresAt || "No expiry"}</Badge>;
}
