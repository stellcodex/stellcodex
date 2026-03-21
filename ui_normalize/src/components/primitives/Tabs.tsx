"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export interface TabsItem {
  id: string;
  label: string;
  content: React.ReactNode;
}

export interface TabsProps {
  items: TabsItem[];
  defaultValue?: string;
  className?: string;
}

export function Tabs({ className, defaultValue, items }: TabsProps) {
  const [activeTab, setActiveTab] = React.useState(defaultValue ?? items[0]?.id ?? "");
  const activeItem = items.find((item) => item.id === activeTab) ?? items[0];

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <button
            key={item.id}
            className={cn(
              "rounded-[12px] border px-3 py-2 text-sm transition-colors",
              item.id === activeItem?.id
                ? "border-[#dddddd] bg-[var(--background-subtle)] font-semibold text-[var(--foreground-strong)]"
                : "border-[#eeeeee] bg-white text-[var(--foreground-muted)] hover:text-[var(--foreground-default)]",
            )}
            onClick={() => setActiveTab(item.id)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
      <div>{activeItem?.content}</div>
    </div>
  );
}
