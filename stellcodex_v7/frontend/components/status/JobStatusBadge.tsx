import { Badge } from "@/components/primitives/Badge";

type JobStatusBadgeProps = {
  status: string;
};

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  return <Badge>{status || "unknown"}</Badge>;
}
