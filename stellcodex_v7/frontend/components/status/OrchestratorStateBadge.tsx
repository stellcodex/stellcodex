import { Badge } from "@/components/primitives/Badge";

type OrchestratorStateBadgeProps = {
  stateCode: string;
  stateLabel?: string | null;
};

export function OrchestratorStateBadge({ stateCode, stateLabel }: OrchestratorStateBadgeProps) {
  const token = (stateCode || "").toUpperCase();
  const variant = token === "S7" || token === "S6" ? "success" : token === "S5" ? "warning" : "info";
  return <Badge variant={variant}>{stateLabel || stateCode}</Badge>;
}
