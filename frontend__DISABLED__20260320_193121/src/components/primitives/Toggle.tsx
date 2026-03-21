import * as React from "react";

import { cn } from "@/lib/utils";

export interface ToggleProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  label: string;
  className?: string;
}

export function Toggle({ checked, className, label, onCheckedChange }: ToggleProps) {
  return (
    <button
      className={cn("flex items-center gap-3 text-sm text-[var(--foreground-default)]", className)}
      onClick={() => onCheckedChange(!checked)}
      type="button"
    >
      <span
        className={cn(
          "relative inline-flex h-6 w-11 rounded-full border border-[var(--border-default)] transition-colors",
          checked ? "bg-[var(--accent-default)]" : "bg-[var(--background-muted)]",
        )}
      >
        <span
          className={cn(
            "absolute left-0.5 top-0.5 h-[18px] w-[18px] rounded-full bg-white transition-transform",
            checked ? "translate-x-5" : "translate-x-0",
          )}
        />
      </span>
      <span>{label}</span>
    </button>
  );
}
