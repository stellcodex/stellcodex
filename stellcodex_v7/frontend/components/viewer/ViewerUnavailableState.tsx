import { EmptyState } from "@/components/primitives/EmptyState";

export interface ViewerUnavailableStateProps {
  description: string;
}

export function ViewerUnavailableState({ description }: ViewerUnavailableStateProps) {
  return <EmptyState title="Viewer unavailable" description={description} />;
}
