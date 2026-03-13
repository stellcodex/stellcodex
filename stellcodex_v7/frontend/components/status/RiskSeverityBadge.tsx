import { Badge } from "@/components/primitives/Badge";
import type { RiskSummary } from "@/lib/contracts/dfm";

type RiskSeverityBadgeProps = {
  severity: RiskSummary["severity"];
};

export function RiskSeverityBadge({ severity }: RiskSeverityBadgeProps) {
  const variant =
    severity === "critical" || severity === "high"
      ? "danger"
      : severity === "medium"
      ? "warning"
      : severity === "low"
      ? "info"
      : "muted";
  return <Badge variant={variant}>{severity}</Badge>;
}
