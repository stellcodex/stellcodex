import { Badge } from "@/components/primitives/Badge";

type FileStatusBadgeProps = {
  status: string;
};

export function FileStatusBadge({ status }: FileStatusBadgeProps) {
  const token = (status || "unknown").toLowerCase();
  const variant =
    token === "ready" || token === "succeeded" || token === "approved"
      ? "success"
      : token === "failed"
      ? "danger"
      : token === "queued" || token === "pending" || token === "processing"
      ? "warning"
      : "muted";
  return <Badge variant={variant}>{status || "unknown"}</Badge>;
}
