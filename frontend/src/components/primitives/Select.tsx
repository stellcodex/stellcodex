import * as React from "react";

import { cn } from "@/lib/utils";

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>;

export function Select({ className, children, ...props }: SelectProps) {
  return (
    <select
      className={cn(
        "h-10 w-full rounded-[12px] border border-[#eeeeee] bg-white px-3 text-sm text-[var(--foreground-default)] outline-none transition-colors focus:border-[#dddddd]",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}
