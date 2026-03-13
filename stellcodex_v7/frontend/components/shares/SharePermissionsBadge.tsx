import { Badge } from "@/components/primitives/Badge";

export interface SharePermissionsBadgeProps {
  permission: string;
}

export function SharePermissionsBadge({ permission }: SharePermissionsBadgeProps) {
  return <Badge variant="info">{permission}</Badge>;
}
