import type { ReactNode } from "react";

export type TooltipProps = {
  label: string;
  children: ReactNode;
};

export function Tooltip({ label, children }: TooltipProps) {
  return (
    <span className="sc-tooltip" aria-label={label} title={label}>
      {children}
    </span>
  );
}
