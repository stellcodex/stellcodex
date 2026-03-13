"use client";

import { Button } from "@/components/primitives/Button";

export interface FitControlsProps {
  onFit: () => void;
  onReset: () => void;
}

export function FitControls({ onFit, onReset }: FitControlsProps) {
  return (
    <div className="sc-inline">
      <Button variant="ghost" onClick={onFit}>Fit</Button>
      <Button variant="ghost" onClick={onReset}>Reset</Button>
    </div>
  );
}
