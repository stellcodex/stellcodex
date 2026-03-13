import { Badge } from "@/components/primitives/Badge";

type ApprovalStatusBadgeProps = {
  status: string;
};

export function ApprovalStatusBadge({ status }: ApprovalStatusBadgeProps) {
  const token = (status || "").toLowerCase();
  const variant = token === "approved" ? "success" : token === "required" || token === "pending" ? "warning" : token === "rejected" ? "danger" : "muted";
  return <Badge variant={variant}>{status}</Badge>;
}
