export interface SelectionInfoProps {
  selectedCount: number;
  hiddenCount: number;
  isolatedNodeId: string | null;
}

export function SelectionInfo({ hiddenCount, isolatedNodeId, selectedCount }: SelectionInfoProps) {
  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border-muted)] bg-[var(--background-subtle)] px-3 py-3 text-xs text-[var(--foreground-muted)]">
      <div>Selected occurrences: <span className="font-medium text-[var(--foreground-strong)]">{selectedCount}</span></div>
      <div className="mt-1">Hidden occurrences: <span className="font-medium text-[var(--foreground-strong)]">{hiddenCount}</span></div>
      <div className="mt-1">Isolation: <span className="font-medium text-[var(--foreground-strong)]">{isolatedNodeId || "Off"}</span></div>
    </div>
  );
}
