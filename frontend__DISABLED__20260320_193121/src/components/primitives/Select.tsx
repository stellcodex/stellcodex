import * as React from "react";

import { cn } from "@/lib/utils";

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>;

export function Select({ className, children, ...props }: SelectProps) {
  return (
    <select
      className={cn(
        "h-10 w-full rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--background-surface)] px-3 text-sm text-[var(--foreground-default)] outline-none transition-colors focus:border-[var(--border-strong)]",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}
