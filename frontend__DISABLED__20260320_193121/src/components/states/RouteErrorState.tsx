import { ErrorState } from "@/components/primitives/ErrorState";

export interface RouteErrorStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function RouteErrorState({ actionLabel, description, onAction, title }: RouteErrorStateProps) {
  return <ErrorState actionLabel={actionLabel} description={description} onAction={onAction} title={title} />;
}
