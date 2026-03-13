import { Badge } from "@/components/primitives/Badge";

type OrchestratorStateBadgeProps = {
  stateCode: string;
  stateLabel?: string | null;
};

export function OrchestratorStateBadge({ stateCode, stateLabel }: OrchestratorStateBadgeProps) {
  return <Badge>{stateLabel || stateCode}</Badge>;
}
