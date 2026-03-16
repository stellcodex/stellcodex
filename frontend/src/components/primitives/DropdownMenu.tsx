"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export interface DropdownMenuItem {
  id: string;
  label: string;
  onSelect: () => void;
}

export interface DropdownMenuProps {
  label: string;
  items: DropdownMenuItem[];
  className?: string;
}

export function DropdownMenu({ className, items, label }: DropdownMenuProps) {
  return (
    <details className={cn("relative", className)}>
      <summary className="list-none cursor-pointer rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--background-surface)] px-3 py-2 text-sm text-[var(--foreground-default)]">
        {label}
      </summary>
      <div className="absolute right-0 z-[var(--z-dropdown)] mt-2 min-w-40 rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--background-surface)] p-1 shadow-[var(--shadow-sm)]">
        {items.map((item) => (
          <button
            key={item.id}
            className="flex w-full rounded-[var(--radius-sm)] px-3 py-2 text-left text-sm text-[var(--foreground-default)] hover:bg-[var(--background-subtle)]"
            onClick={item.onSelect}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
    </details>
  );
}
