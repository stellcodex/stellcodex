import { EmptyState } from "@/components/primitives/EmptyState";

export interface RouteEmptyStateProps {
  title: string;
  description: string;
}

export function RouteEmptyState({ description, title }: RouteEmptyStateProps) {
  return <EmptyState description={description} title={title} />;
}
