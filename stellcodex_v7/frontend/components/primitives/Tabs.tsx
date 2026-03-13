"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

export type TabItem = {
  value: string;
  label: string;
  badge?: ReactNode;
};

export type TabsProps = {
  items: TabItem[];
  value: string;
  onChange: (value: string) => void;
};

export function Tabs({ items, value, onChange }: TabsProps) {
  return (
    <div className="sc-tabs" role="tablist" aria-label="Tabs">
      {items.map((item) => (
        <button
          key={item.value}
          className={cn("sc-tab")}
          data-active={item.value === value ? "true" : "false"}
          onClick={() => onChange(item.value)}
          role="tab"
          type="button"
        >
          <span>{item.label}</span>
          {item.badge}
        </button>
      ))}
    </div>
  );
}
