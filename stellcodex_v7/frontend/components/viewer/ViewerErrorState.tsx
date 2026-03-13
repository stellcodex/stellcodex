import { ErrorState } from "@/components/primitives/ErrorState";

export interface ViewerErrorStateProps {
  description?: string;
  onRetry?: () => void;
}

export function ViewerErrorState({ description, onRetry }: ViewerErrorStateProps) {
  return <ErrorState title="Viewer error" description={description || "Viewer could not be opened"} retryLabel="Retry" onRetry={onRetry} />;
}
