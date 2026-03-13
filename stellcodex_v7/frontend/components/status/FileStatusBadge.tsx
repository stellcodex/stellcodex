import { Badge } from "@/components/primitives/Badge";

type FileStatusBadgeProps = {
  status: string;
};

export function FileStatusBadge({ status }: FileStatusBadgeProps) {
  return <Badge>{status || "unknown"}</Badge>;
}
