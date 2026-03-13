"use client";

import { Button } from "@/components/primitives/Button";

export interface VisibilityControlsProps {
  onShowAll: () => void;
  onHideSelected: () => void;
  disableShowAll?: boolean;
  disableHide?: boolean;
  hint?: string;
}

export function VisibilityControls({
  onShowAll,
  onHideSelected,
  disableShowAll = false,
  disableHide = false,
  hint,
}: VisibilityControlsProps) {
  return (
    <div className="sc-stack">
      <div className="sc-inline">
      <Button variant="ghost" disabled={disableShowAll} onClick={onShowAll}>
        Show all
      </Button>
      <Button variant="ghost" disabled={disableHide} onClick={onHideSelected}>
        Hide selected
      </Button>
      </div>
      {hint ? <span className="sc-muted">{hint}</span> : null}
    </div>
  );
}
