import type { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  error?: string | null;
};

export function Select({ className, error, ...props }: SelectProps) {
  return (
    <select
      {...props}
      aria-invalid={error ? "true" : "false"}
      className={cn("sc-select", className)}
      data-invalid={error ? "true" : "false"}
    />
  );
}
