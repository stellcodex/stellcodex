import { Badge } from "@/components/primitives/Badge";

type ApprovalStatusBadgeProps = {
  status: string;
};

export function ApprovalStatusBadge({ status }: ApprovalStatusBadgeProps) {
  return <Badge>{status}</Badge>;
}
