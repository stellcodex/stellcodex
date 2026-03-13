import { Badge } from "@/components/primitives/Badge";

type ReadinessBadgeProps = {
  ready: boolean;
  label?: string;
};

export function ReadinessBadge({ ready, label }: ReadinessBadgeProps) {
  return <Badge>{label || (ready ? "Ready" : "Not ready")}</Badge>;
}
