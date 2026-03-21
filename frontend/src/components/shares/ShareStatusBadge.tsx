import { Badge } from "@/components/primitives/Badge";

export interface ShareStatusBadgeProps {
  status: "active" | "expired" | "revoked";
}

export function ShareStatusBadge({ status }: ShareStatusBadgeProps) {
  const tone = status === "active" ? "success" : status === "expired" ? "warning" : "danger";
  return <Badge tone={tone}>{status}</Badge>;
}
