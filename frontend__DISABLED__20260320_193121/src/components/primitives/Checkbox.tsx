import * as React from "react";

import { cn } from "@/lib/utils";

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

export function Checkbox({ className, label, hint, ...props }: CheckboxProps) {
  return (
    <label className={cn("flex items-start gap-3 text-sm text-[var(--foreground-default)]", className)}>
      <input type="checkbox" className="mt-1 h-4 w-4 rounded border-[var(--border-default)]" {...props} />
      <span className="space-y-1">
        <span className="block font-medium">{label}</span>
        {hint ? <span className="block text-xs text-[var(--foreground-muted)]">{hint}</span> : null}
      </span>
    </label>
  );
}
