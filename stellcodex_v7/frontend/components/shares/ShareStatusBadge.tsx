import { Badge } from "@/components/primitives/Badge";
import type { ShareSummary } from "@/lib/contracts/shares";

export interface ShareStatusBadgeProps {
  status: ShareSummary["status"];
}

export function ShareStatusBadge({ status }: ShareStatusBadgeProps) {
  const variant = status === "active" ? "success" : status === "expired" ? "warning" : status === "revoked" ? "danger" : "muted";
  return <Badge variant={variant}>{status}</Badge>;
}
