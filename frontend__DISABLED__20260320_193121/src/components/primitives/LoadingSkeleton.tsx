import { cn } from "@/lib/utils";

export interface LoadingSkeletonProps {
  className?: string;
}

export function LoadingSkeleton({ className }: LoadingSkeletonProps) {
  return <div className={cn("animate-pulse rounded-[var(--radius-md)] bg-[var(--background-muted)]", className)} />;
}
