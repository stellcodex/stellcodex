import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";

export interface RouteLoadingStateProps {
  title?: string;
}

export function RouteLoadingState({ title = "Loading route" }: RouteLoadingStateProps) {
  return (
    <div className="space-y-4">
      <div className="text-sm font-medium text-[var(--foreground-muted)]">{title}</div>
      <LoadingSkeleton className="h-24 w-full" />
      <LoadingSkeleton className="h-64 w-full" />
    </div>
  );
}
