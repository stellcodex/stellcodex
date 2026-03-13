import { Badge } from "@/components/primitives/Badge";

type RiskSeverityBadgeProps = {
  severity: string;
};

export function RiskSeverityBadge({ severity }: RiskSeverityBadgeProps) {
  return <Badge>{severity}</Badge>;
}
