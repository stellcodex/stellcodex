export interface SeparatorProps {
  className?: string;
}

export function Separator({ className }: SeparatorProps) {
  return <div className={className ?? "h-px w-full bg-[var(--border-muted)]"} />;
}
