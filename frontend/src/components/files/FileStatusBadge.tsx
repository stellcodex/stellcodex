import { Badge } from "@/components/primitives/Badge";

export interface FileStatusBadgeProps {
  status: string;
}

export function FileStatusBadge({ status }: FileStatusBadgeProps) {
  const normalized = status.toLowerCase();
  const tone =
    normalized === "ready" || normalized === "approved" || normalized === "ok" || normalized === "pass"
      ? "success"
      : normalized === "failed" || normalized === "fail"
      ? "danger"
      : normalized === "queued" || normalized === "processing" || normalized === "running"
      ? "warning"
      : normalized.includes("share")
      ? "info"
      : "neutral";

  return <Badge tone={tone}>{status}</Badge>;
}
