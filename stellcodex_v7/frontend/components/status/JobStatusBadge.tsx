import { Badge } from "@/components/primitives/Badge";

type JobStatusBadgeProps = {
  status: string;
};

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const token = (status || "unknown").toLowerCase();
  const variant =
    token === "succeeded" || token === "ready"
      ? "success"
      : token === "failed"
      ? "danger"
      : token === "queued" || token === "running" || token === "started"
      ? "warning"
      : "muted";
  return <Badge variant={variant}>{status || "unknown"}</Badge>;
}
