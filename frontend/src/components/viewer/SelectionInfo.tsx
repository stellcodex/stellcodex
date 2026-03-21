export interface SelectionInfoProps {
  selectedCount: number;
  hiddenCount: number;
  isolatedNodeId: string | null;
}

export function SelectionInfo({ hiddenCount, isolatedNodeId, selectedCount }: SelectionInfoProps) {
  return (
    <div className="rounded-[12px] border border-[#eeeeee] bg-white px-3 py-3 text-sm text-[var(--foreground-muted)]">
      <div>Selected: <span className="font-medium text-[var(--foreground-strong)]">{selectedCount}</span></div>
      <div className="mt-1">Hidden: <span className="font-medium text-[var(--foreground-strong)]">{hiddenCount}</span></div>
      <div className="mt-1">Isolation: <span className="font-medium text-[var(--foreground-strong)]">{isolatedNodeId || "Off"}</span></div>
    </div>
  );
}
