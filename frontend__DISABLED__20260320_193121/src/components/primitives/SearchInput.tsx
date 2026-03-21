import * as React from "react";

import { cn } from "@/lib/utils";

import { Input, type InputProps, inputClassName } from "./Input";

export type SearchInputProps = InputProps;

export function SearchInput({ className, ...props }: SearchInputProps) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[var(--foreground-soft)]">
        Search
      </span>
      <Input className={cn(inputClassName, "pl-16", className)} type="search" {...props} />
    </div>
  );
}
